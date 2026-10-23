"""Record Wallex public trade WebSocket messages as local OHLCV candles.

Protocol selection
------------------
Wallex documents two WebSocket generations:

* version 1, ``wss://api.wallex.ir/ws``, is explicitly described as deprecated
  but still working, and its pages describe the *logical* subscription frame
  ``["subscribe", {"channel": "MARKET@trade"}]``;
* version 2 (Centrifugo), ``wss://api.wallex.ir/connection/websocket``, is what
  the official documentation recommends for new implementations.

Version 2 is plain JSON over one WebSocket, so this recorder implements it with
the already-required ``websockets`` package and needs no extra SDK dependency.
The documented frames are (https://developers.wallex.ir/docs/socket-raw-protocol):

    client -> {"id": 1, "connect": {}}
    server -> {"id": 1, "connect": {"client": ..., "ping": 25, "pong": true}}
    client -> {"id": 2, "subscribe": {"channel": "public:<SYMBOL>@trade"}}
    server -> {"id": 2, "subscribe": {}}                 (empty ack)
    server -> {"push": {"channel": ..., "pub": {"data": {...}}}}
    server -> {}                                         (heartbeat, echo {} back)

A single transport frame may carry several newline-separated JSON messages, so
every frame is split before classification. Nothing here is verified against a
live Wallex session from this environment; see ``docs/agent/CANDLE-RECORDER.md``
for the current runtime verification status.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from collections.abc import Mapping
from pathlib import Path
from typing import Any, Callable, Sequence

WALLEX_WS_URL = "wss://api.wallex.ir/connection/websocket"
TRADE_DOC_URL = "https://developers.wallex.ir/docs/socket-trade"
SOCKET_DOC_URL = "https://developers.wallex.ir/docs/socket-intro"
RAW_PROTOCOL_DOC_URL = "https://developers.wallex.ir/docs/socket-raw-protocol"
PROTOCOL_ID = "wallex-centrifugo-v2-raw"
MANIFEST_SCHEMA_VERSION = 2
CONNECT_REQUEST_ID = 1
SUBSCRIBE_REQUEST_ID = 2
DEFAULT_ACK_TIMEOUT_SECONDS = 15.0
DEFAULT_HEARTBEAT_TIMEOUT_SECONDS = 60.0
MANIFEST_UPDATE_INTERVAL_SECONDS = 2.0
_MAX_ERROR_MESSAGE_CHARS = 200

# Documented server close codes (https://developers.wallex.ir/docs/socket-raw-protocol).
# 3000-3499: reconnecting may help. 3500+: the client is at fault, retrying is futile.
FATAL_CLOSE_CODE_MIN = 3500

FRAME_HANDSHAKE = "handshake"
FRAME_LEGACY_V1 = "legacy_v1_frame"
FRAME_SERVER_PING = "server_ping"
FRAME_SUBSCRIPTION_ACK = "subscription_ack"
FRAME_SERVER_ERROR = "server_error"
FRAME_PUBLICATION = "publication"
FRAME_UNKNOWN = "unknown_event"
FRAME_MALFORMED = "malformed"


class RecorderProtocolError(RuntimeError):
    """A documented server rejection or fatal close code that retrying cannot fix."""


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite decimal")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a finite decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be a finite decimal")
    return result


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _short(value: Any, limit: int = _MAX_ERROR_MESSAGE_CHARS) -> str | None:
    """Render untrusted server text safely: single line, bounded length, no secrets."""
    if not isinstance(value, str):
        return None
    cleaned = " ".join(value.split())
    return cleaned[:limit] if cleaned else None


def _int_or_none(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, Decimal):
        if value.is_finite() and value == value.to_integral_value():
            return int(value)
        return None
    if isinstance(value, str) and value.strip().lstrip("-").isdigit():
        try:
            return int(value)
        except ValueError:
            return None
    return None


def _close_code(exc: BaseException) -> int | None:
    """Return the close code the server sent, if this exception carries one.

    ``websockets`` exposes it on ``ConnectionClosed.rcvd.code``; the flat
    ``.code`` attribute is deprecated and raises when no close frame arrived.
    Test doubles expose ``.code`` directly, so it is kept as a fallback.
    """
    received = getattr(getattr(exc, "rcvd", None), "code", None)
    if received is not None:
        return _int_or_none(received)
    return _int_or_none(getattr(exc, "code", None))


def trade_channel(symbol: str) -> str:
    """Documented v2 public trade channel name for one market symbol."""
    return f"public:{symbol}@trade"


def validate_symbol(symbol: str) -> str:
    """Validate a market symbol against the documented channel-name alphabet.

    The socket overview states a market name may contain only ASCII letters,
    digits, ``_`` and ``-``; official examples are uppercase (``BTCTMN``).
    Rejecting ``:``, ``@`` and ``#`` also prevents channel-name injection.
    """
    if not isinstance(symbol, str) or not symbol:
        raise ValueError("symbol must be an uppercase alphanumeric Wallex market symbol")
    allowed = set("ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-")
    if len(symbol) > 32 or symbol[0] in "_-" or any(ch not in allowed for ch in symbol):
        raise ValueError(
            "symbol must be an uppercase Wallex market symbol using only A-Z, 0-9, '_' and '-'"
        )
    return symbol


def split_messages(raw: str | bytes) -> list[str]:
    """Split one transport frame into the newline-separated JSON messages it carries.

    The official raw-protocol example splits every received frame on ``\\n``
    because one frame may contain several messages.
    """
    if isinstance(raw, (bytes, bytearray)):
        text = bytes(raw).decode("utf-8")
    elif isinstance(raw, str):
        text = raw
    else:
        raise TypeError("websocket frame must be text")
    # Exactly the documented split: on "\n" only. ``str.splitlines`` would also split
    # on U+2028, U+0085 and friends, which are legal inside a JSON string, and would
    # cut one message into two unparseable halves.
    return [line.strip() for line in text.split("\n") if line.strip()]


@dataclass(slots=True)
class ServerFrame:
    """Classified Wallex v2 server frame (one JSON message, not a transport frame)."""

    kind: str
    request_id: int | None = None
    error_code: int | None = None
    error_message: str | None = None
    channel: str | None = None
    data: Mapping[str, Any] | None = None
    server_ping_seconds: int | None = None


def _looks_like_legacy_handshake(payload: Mapping[str, Any]) -> bool:
    """Detect the Engine.IO/Socket.IO opening packet served by the deprecated ``/ws``."""
    return "sid" in payload and ("pingInterval" in payload or "upgrades" in payload)


def _legacy_publication(payload: Any) -> bool:
    """Detect the deprecated v1 ``[channel, body]`` envelope (never a v2 message)."""
    return (
        isinstance(payload, list)
        and len(payload) == 2
        and isinstance(payload[0], str)
        and isinstance(payload[1], dict)
    )


def classify_server_message(message: str | bytes) -> ServerFrame:
    """Classify one server message without guessing that unknown frames are trades."""
    try:
        text = message.decode("utf-8") if isinstance(message, (bytes, bytearray)) else message
    except UnicodeDecodeError:
        return ServerFrame(FRAME_MALFORMED)
    if not isinstance(text, str):
        return ServerFrame(FRAME_MALFORMED)
    try:
        # parse_float=Decimal keeps a numeric (non-string) payload exactly as sent;
        # the documented wire format uses decimal strings, but a JSON number must
        # not lose precision before OHLCV accumulation.
        payload = json.loads(text, parse_float=Decimal)
    except (json.JSONDecodeError, TypeError, ValueError):
        return ServerFrame(FRAME_MALFORMED)

    if isinstance(payload, dict):
        if not payload:
            # Documented heartbeat: the server sends an empty object every 25s.
            return ServerFrame(FRAME_SERVER_PING)
        if "error" in payload:
            error = payload["error"]
            if isinstance(error, dict):
                return ServerFrame(
                    FRAME_SERVER_ERROR,
                    request_id=_int_or_none(payload.get("id")),
                    error_code=_int_or_none(error.get("code")),
                    error_message=_short(error.get("message")),
                )
            return ServerFrame(
                FRAME_SERVER_ERROR,
                request_id=_int_or_none(payload.get("id")),
                error_message=_short(error),
            )
        if "push" in payload:
            push = payload["push"]
            if not isinstance(push, dict):
                return ServerFrame(FRAME_MALFORMED)
            channel = push.get("channel")
            pub = push.get("pub")
            if not isinstance(channel, str) or not isinstance(pub, dict):
                return ServerFrame(FRAME_MALFORMED)
            data = pub.get("data")
            if not isinstance(data, dict):
                return ServerFrame(FRAME_MALFORMED)
            return ServerFrame(FRAME_PUBLICATION, channel=channel, data=data)
        if "connect" in payload:
            reply = payload["connect"]
            if not isinstance(reply, dict):
                return ServerFrame(FRAME_MALFORMED)
            return ServerFrame(
                FRAME_HANDSHAKE,
                request_id=_int_or_none(payload.get("id")),
                server_ping_seconds=_int_or_none(reply.get("ping")),
            )
        if "subscribe" in payload:
            if not isinstance(payload["subscribe"], dict):
                return ServerFrame(FRAME_MALFORMED)
            return ServerFrame(FRAME_SUBSCRIPTION_ACK, request_id=_int_or_none(payload.get("id")))
        if _looks_like_legacy_handshake(payload):
            return ServerFrame(FRAME_LEGACY_V1)
        return ServerFrame(FRAME_UNKNOWN)

    if _legacy_publication(payload):
        # Valid JSON, but the deprecated v1 envelope: never treated as a trade here.
        return ServerFrame(FRAME_LEGACY_V1, channel=payload[0], data=payload[1])
    return ServerFrame(FRAME_UNKNOWN)


def parse_trade_payload(data: Mapping[str, Any] | None) -> tuple[datetime, Decimal, Decimal] | None:
    """Parse ``push.pub.data`` into (UTC timestamp, price, quantity).

    The documented trade body carries ``quantity`` and ``price`` decimal strings
    and an ISO-8601 ``timestamp``. ``isBuyOrder`` describes the maker side and is
    not needed for OHLCV construction.
    """
    if not isinstance(data, Mapping):
        return None
    try:
        price = _decimal(data.get("price"), "price")
        quantity = _decimal(data.get("quantity"), "quantity")
    except ValueError:
        return None
    stamp = data.get("timestamp")
    if not isinstance(stamp, str):
        return None
    try:
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        return None
    try:
        parsed = parsed.astimezone(timezone.utc)
    except (OverflowError, OSError, ValueError):
        return None
    if price <= 0 or quantity <= 0:
        return None
    return parsed, price, quantity


@dataclass(slots=True)
class CandleAccumulator:
    start: datetime
    interval_seconds: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trade_count: int = 1

    @classmethod
    def from_trade(cls, timestamp: datetime, price: Decimal, quantity: Decimal, interval_seconds: int) -> "CandleAccumulator":
        epoch = int(timestamp.timestamp())
        bucket = datetime.fromtimestamp(epoch - epoch % interval_seconds, timezone.utc)
        return cls(bucket, interval_seconds, price, price, price, price, quantity, 1)

    def add(self, price: Decimal, quantity: Decimal) -> None:
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.volume += quantity
        self.trade_count += 1

    def as_dict(self, symbol: str) -> dict[str, Any]:
        return {"timestamp": self.start.isoformat().replace("+00:00", "Z"),
                "open": str(self.open), "high": str(self.high), "low": str(self.low),
                "close": str(self.close), "volume": str(self.volume), "symbol": symbol,
                "interval_seconds": self.interval_seconds, "trade_count": self.trade_count,
                "source": "wallex_public_trade_websocket", "source_url": TRADE_DOC_URL}


class CandleWriter:
    """Append closed candles and maintain a source, freshness, and connection manifest.

    Manifest schema 2 separates transport from application state: ``connection_count``
    counts opened sockets, ``subscription_status`` reports whether the documented
    ``subscribe`` acknowledgement actually arrived, and frames are counted per
    documented class instead of being lumped into "malformed".
    """

    def __init__(self, output: str | Path, symbol: str, interval_seconds: int) -> None:
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.symbol = symbol
        self.interval_seconds = interval_seconds
        self.channel = trade_channel(symbol)
        self.manifest_path = self.output.with_suffix(self.output.suffix + ".manifest.json")
        self.started_at = _utc_now()
        self.updated_at = self.started_at
        self.status = "starting"
        self.stop_reason: str | None = None
        self.closed_candles = 0
        self.transport_frames = 0
        self.messages = 0
        self.trade_events = 0
        self.malformed = 0
        self.late_trades_ignored = 0
        self.other_channel_publications_ignored = 0
        self.last_candle: str | None = None
        self.last_trade_at: str | None = None
        self.last_message_at: str | None = None
        self.connection_count = 0
        self.reconnect_count = 0
        self.connection_errors = 0
        self.handshake_frames = 0
        self.subscription_ack_frames = 0
        self.server_ping_frames = 0
        self.server_pongs_sent = 0
        self.server_error_frames = 0
        self.unknown_frames = 0
        self.legacy_frames = 0
        self.subscription_status = "not_attempted"
        self.last_subscription_error_code: int | None = None
        self.last_subscription_error_message: str | None = None
        self.last_server_error: dict[str, Any] | None = None
        self.last_connection_error_type: str | None = None
        self.last_connection_error_message: str | None = None
        self.server_ping_interval_seconds: int | None = None
        self.fatal_close_code: int | None = None
        self.discarded_partial_candles = 0
        # Appending to an existing recording: the last finalized bucket is a hard
        # floor. Without it a restart would re-finalize an already-written bucket
        # and produce a duplicate timestamp that downstream gates reject.
        self.resumed_from_existing_output = False
        self.previous_last_closed_candle_utc: str | None = None
        self.last_written_start: datetime | None = None
        self._needs_leading_newline = False
        if self.output.exists():
            existing = self._read_last_written_bucket()
            if existing is not None:
                self.last_written_start = existing
                self.resumed_from_existing_output = True
                self.previous_last_closed_candle_utc = existing.isoformat().replace("+00:00", "Z")
        self._last_write = 0.0
        self.write_manifest(force=True)

    def _read_last_written_bucket(self) -> datetime | None:
        """Return the bucket start of the last finalized candle already on disk.

        Only the file tail is read, so a large recording is not loaded into memory.
        A tail that cannot be parsed means the dataset is already damaged; appending
        to it would make things worse, so this fails closed instead of guessing.
        """
        tail_bytes = 65536
        with self.output.open("rb") as handle:
            handle.seek(0, 2)
            size = handle.tell()
            handle.seek(max(0, size - tail_bytes))
            chunk = handle.read().decode("utf-8", errors="replace")
            # A file that does not end with a newline would otherwise have the next
            # record glued onto its final line, producing an unparseable JSONL line.
            handle.seek(max(0, size - 1))
            self._needs_leading_newline = size > 0 and handle.read(1) != b"\n"
        for line in reversed(chunk.splitlines()):
            if not line.strip():
                continue
            try:
                stamp = json.loads(line)["timestamp"]
                parsed = datetime.fromisoformat(str(stamp).replace("Z", "+00:00"))
            except (json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
                raise ValueError(
                    f"existing recording {self.output} ends with a line whose timestamp "
                    "cannot be read; move or repair that file before appending to it"
                ) from exc
            if parsed.tzinfo is None or parsed.utcoffset() is None:
                raise ValueError(
                    f"existing recording {self.output} ends with a timestamp without a timezone")
            return parsed.astimezone(timezone.utc)
        return None  # empty file: nothing was finalized yet

    # -- manifest -------------------------------------------------------
    def _manifest(self) -> dict[str, Any]:
        return {
            "schema_version": MANIFEST_SCHEMA_VERSION,
            "protocol": PROTOCOL_ID,
            "symbol": self.symbol,
            "interval_seconds": self.interval_seconds,
            "channel": self.channel,
            "websocket_url": WALLEX_WS_URL,
            "documentation_url": TRADE_DOC_URL,
            "socket_documentation_url": SOCKET_DOC_URL,
            "raw_protocol_documentation_url": RAW_PROTOCOL_DOC_URL,
            "started_at_utc": self.started_at,
            "updated_at_utc": self.updated_at,
            "status": self.status,
            "stop_reason": self.stop_reason,
            "subscription_status": self.subscription_status,
            "resumed_from_existing_output": self.resumed_from_existing_output,
            "previous_last_closed_candle_utc": self.previous_last_closed_candle_utc,
            "closed_candles_written_this_run": self.closed_candles,
            "last_closed_candle_utc": self.last_candle,
            "transport_frames_received": self.transport_frames,
            "messages_received": self.messages,
            "trade_events_received": self.trade_events,
            "last_trade_at_utc": self.last_trade_at,
            "last_message_at_utc": self.last_message_at,
            "malformed_or_unmatched_messages": self.malformed,
            "late_or_out_of_order_trades_ignored": self.late_trades_ignored,
            "other_channel_publications_ignored": self.other_channel_publications_ignored,
            "handshake_frames_received": self.handshake_frames,
            "subscription_ack_frames_received": self.subscription_ack_frames,
            "server_ping_frames_received": self.server_ping_frames,
            "server_pongs_sent": self.server_pongs_sent,
            "server_error_frames_received": self.server_error_frames,
            "unknown_frames_ignored": self.unknown_frames,
            "legacy_v1_frames_ignored": self.legacy_frames,
            "last_subscription_error_code": self.last_subscription_error_code,
            "last_subscription_error_message": self.last_subscription_error_message,
            "last_server_error": self.last_server_error,
            "server_ping_interval_seconds": self.server_ping_interval_seconds,
            "connection_count": self.connection_count,
            "reconnect_count": self.reconnect_count,
            "connection_errors": self.connection_errors,
            "last_connection_error_type": self.last_connection_error_type,
            "last_connection_error_message": self.last_connection_error_message,
            "fatal_close_code": self.fatal_close_code,
            "discarded_partial_candles": self.discarded_partial_candles,
            "gaps_possible_on_disconnect": (self.connection_errors > 0 or self.reconnect_count > 0
                                            or self.fatal_close_code is not None),
            # At least one documented acknowledgement was validated for our own
            # subscribe command during this run. `subscription_status` describes
            # the current connection; this boolean survives a later reconnect.
            "subscription_acknowledged": self.subscription_ack_frames > 0,
            "live_trade_received": self.trade_events > 0,
        }

    def write_manifest(self, *, force: bool = False) -> None:
        now = time.monotonic()
        if not force and now - self._last_write < MANIFEST_UPDATE_INTERVAL_SECONDS:
            return
        self._last_write = now
        self.updated_at = _utc_now()
        # Replace atomically: an operator or CI job may read the manifest while the
        # recorder is running and must never see a half-written status.
        temporary = self.manifest_path.with_name(self.manifest_path.name + ".tmp")
        temporary.write_text(json.dumps(self._manifest(), indent=2) + "\n", encoding="utf-8")
        os.replace(temporary, self.manifest_path)

    def set_status(self, status: str, *, force: bool = True) -> None:
        self.status = status
        self.write_manifest(force=force)

    # -- recording ------------------------------------------------------
    def note_message(self) -> None:
        self.last_message_at = _utc_now()

    def write_candle(self, candle: CandleAccumulator) -> None:
        record = candle.as_dict(self.symbol)
        prefix = ""
        if self._needs_leading_newline:
            prefix = "\n"
            self._needs_leading_newline = False
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(prefix + json.dumps(record, separators=(",", ":")) + "\n")
        self.closed_candles += 1
        self.last_candle = record["timestamp"]
        self.last_written_start = candle.start
        self.write_manifest(force=True)

    def finish(self, status: str, stop_reason: str) -> None:
        self.status = status
        self.stop_reason = stop_reason
        self.write_manifest(force=True)


async def record_trades(symbol: str, interval_seconds: int, output: str | Path, *,
                        max_runtime_seconds: float = 0,
                        connector: Callable[..., Any] | None = None,
                        clock: Callable[[], float] | None = None,
                        reconnect_backoff_seconds: float = 1.0,
                        max_reconnect_attempts: int = 10,
                        ack_timeout_seconds: float = DEFAULT_ACK_TIMEOUT_SECONDS,
                        heartbeat_timeout_seconds: float = DEFAULT_HEARTBEAT_TIMEOUT_SECONDS) -> int:
    """Record one public trade channel with bounded reconnects and no data fabrication.

    Candles are written only when a trade from a later interval arrives, so the
    most recent (unfinished) candle is always discarded: at shutdown, at a
    disconnect, or when a gap is detected. Outages are reported in the manifest
    instead of being backfilled or smoothed over.
    """
    validate_symbol(symbol)
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, int):
        raise ValueError("interval-seconds must be an integer")
    if not 1 <= interval_seconds <= 86400:
        raise ValueError("interval-seconds must be between 1 and 86400")
    if max_runtime_seconds < 0:
        raise ValueError("max-runtime-seconds cannot be negative")
    if reconnect_backoff_seconds < 0:
        raise ValueError("reconnect-backoff-seconds cannot be negative")
    if isinstance(max_reconnect_attempts, bool) or not isinstance(max_reconnect_attempts, int) or max_reconnect_attempts < 0:
        raise ValueError("max-reconnect-attempts must be a non-negative integer")
    if ack_timeout_seconds <= 0:
        raise ValueError("ack-timeout-seconds must be positive")
    if heartbeat_timeout_seconds <= 0:
        raise ValueError("heartbeat-timeout-seconds must be positive")
    if connector is None:
        try:
            from websockets.asyncio.client import connect
        except ImportError as exc:
            raise RuntimeError("install project dependencies including websockets") from exc
        connector = connect

    now = clock or time.monotonic
    channel = trade_channel(symbol)
    writer = CandleWriter(output, symbol, interval_seconds)
    active: CandleAccumulator | None = None
    deadline = now() + max_runtime_seconds if max_runtime_seconds else None
    consecutive_failures = 0
    failure_reason: str | None = None
    cancelled = False

    try:
        while deadline is None or now() < deadline:
            try:
                writer.set_status("connecting")
                async with connector(WALLEX_WS_URL, open_timeout=15, close_timeout=5,
                                     ping_interval=None, ping_timeout=None,
                                     max_size=1_000_000) as websocket:
                    writer.connection_count += 1
                    if writer.connection_count > 1:
                        writer.reconnect_count += 1
                    writer.subscription_status = "pending"
                    writer.set_status("handshaking", force=True)

                    # Documented order: the first command after the socket opens is
                    # `connect`, and `subscribe` is step 2. The official samples send
                    # both back-to-back, so waiting for the connect reply is a stricter
                    # choice, not a documented requirement: it guarantees that a
                    # connection the server never accepted can never reach a
                    # "subscribed" state, and that every error is attributed to the
                    # command that caused it.
                    await websocket.send(json.dumps({"id": CONNECT_REQUEST_ID, "connect": {}}))
                    connect_deadline = now() + ack_timeout_seconds
                    subscribe_deadline: float | None = None
                    connect_acked = False
                    subscribe_requested = False
                    subscribe_acked = False
                    last_rx = now()

                    while True:
                        waits = [last_rx + heartbeat_timeout_seconds]
                        if not connect_acked:
                            waits.append(connect_deadline)
                        elif not subscribe_acked and subscribe_deadline is not None:
                            waits.append(subscribe_deadline)
                        if deadline is not None:
                            waits.append(deadline)
                        timeout = min(waits) - now()
                        if timeout <= 0:
                            if deadline is not None and now() >= deadline:
                                break
                            if not connect_acked and now() >= connect_deadline:
                                raise TimeoutError(
                                    "no documented connect acknowledgement within "
                                    f"{ack_timeout_seconds:g}s")
                            if (not subscribe_acked and subscribe_deadline is not None
                                    and now() >= subscribe_deadline):
                                raise TimeoutError(
                                    "the server acknowledged connect but not the subscription "
                                    f"within {ack_timeout_seconds:g}s")
                            raise TimeoutError(
                                f"no frames received for {heartbeat_timeout_seconds:g}s; the "
                                "documented heartbeat is an empty object every 25s")
                        try:
                            message = await asyncio.wait_for(websocket.recv(), timeout=timeout)
                        except asyncio.TimeoutError:
                            continue
                        last_rx = now()
                        writer.transport_frames += 1
                        writer.note_message()
                        try:
                            messages = split_messages(message)
                        except (UnicodeDecodeError, TypeError):
                            # A non-UTF-8 or non-text frame cannot be a documented message.
                            writer.malformed += 1
                            writer.write_manifest()
                            continue
                        for text in messages:
                            writer.messages += 1
                            frame = classify_server_message(text)
                            if frame.kind == FRAME_SERVER_PING:
                                writer.server_ping_frames += 1
                                await websocket.send("{}")
                                writer.server_pongs_sent += 1
                                writer.write_manifest()
                                continue
                            if frame.kind == FRAME_HANDSHAKE:
                                if frame.request_id != CONNECT_REQUEST_ID or connect_acked:
                                    # An ack that does not answer our connect command
                                    # (or repeats it) proves nothing about this session.
                                    writer.unknown_frames += 1
                                    continue
                                writer.handshake_frames += 1
                                connect_acked = True
                                writer.server_ping_interval_seconds = frame.server_ping_seconds
                                writer.write_manifest()
                                # Step 2 only after the connect reply is validated.
                                await websocket.send(json.dumps({
                                    "id": SUBSCRIBE_REQUEST_ID,
                                    "subscribe": {"channel": channel}}))
                                subscribe_requested = True
                                subscribe_deadline = now() + ack_timeout_seconds
                                continue
                            if frame.kind == FRAME_SUBSCRIPTION_ACK:
                                if (not subscribe_requested
                                        or frame.request_id != SUBSCRIBE_REQUEST_ID
                                        or subscribe_acked):
                                    # An ack we never asked for, or for another id, is
                                    # not evidence that our channel is subscribed.
                                    writer.unknown_frames += 1
                                    continue
                                writer.subscription_ack_frames += 1
                                subscribe_acked = True
                                consecutive_failures = 0
                                writer.subscription_status = "acknowledged"
                                writer.set_status("subscribed", force=True)
                                continue
                            if frame.kind == FRAME_SERVER_ERROR:
                                writer.server_error_frames += 1
                                writer.last_server_error = {
                                    "code": frame.error_code,
                                    "message": frame.error_message,
                                    "request_id": frame.request_id,
                                }
                                if frame.request_id == CONNECT_REQUEST_ID:
                                    # A rejected connect means this socket is unusable;
                                    # no subscribe was sent, so nothing is subscribed.
                                    writer.write_manifest(force=True)
                                    raise ConnectionError(
                                        "server rejected the connect command: "
                                        f"code={frame.error_code} message={frame.error_message}")
                                if (frame.request_id == SUBSCRIBE_REQUEST_ID
                                        and subscribe_requested):
                                    writer.subscription_status = "rejected"
                                    writer.last_subscription_error_code = frame.error_code
                                    writer.last_subscription_error_message = frame.error_message
                                    writer.set_status("failed", force=True)
                                    failure_reason = "subscription_rejected"
                                    raise RecorderProtocolError(
                                        "server rejected the subscription for "
                                        f"{channel} (code={frame.error_code}: "
                                        f"{frame.error_message}); verify the symbol against the "
                                        "official markets list and the channel name in "
                                        f"{RAW_PROTOCOL_DOC_URL}")
                                # Documented errors answer one command by id and do not
                                # close the connection; an error for another (or no)
                                # request id is not our subscription being rejected.
                                writer.write_manifest(force=True)
                                continue
                            if frame.kind == FRAME_PUBLICATION:
                                if frame.channel != channel:
                                    writer.other_channel_publications_ignored += 1
                                    continue
                                trade = parse_trade_payload(frame.data)
                                if trade is None:
                                    writer.malformed += 1
                                    writer.write_manifest()
                                    continue
                                timestamp, price, quantity = trade
                                writer.trade_events += 1
                                writer.last_trade_at = timestamp.isoformat().replace("+00:00", "Z")
                                next_candle = CandleAccumulator.from_trade(
                                    timestamp, price, quantity, interval_seconds)
                                if (writer.last_written_start is not None
                                        and next_candle.start <= writer.last_written_start):
                                    # Already finalized by an earlier run of this output
                                    # file; rewriting it would duplicate a timestamp.
                                    writer.late_trades_ignored += 1
                                    writer.write_manifest()
                                    continue
                                if active is None:
                                    active = next_candle
                                elif next_candle.start == active.start:
                                    active.add(price, quantity)
                                elif next_candle.start > active.start:
                                    writer.write_candle(active)
                                    active = next_candle
                                else:
                                    # Documented trade channels carry no offset/sequence
                                    # number, so a late trade cannot be inserted into an
                                    # already-written candle; it is counted, not discarded
                                    # silently and not treated as a malformed payload.
                                    writer.late_trades_ignored += 1
                                writer.write_manifest()
                                continue
                            if frame.kind == FRAME_LEGACY_V1:
                                writer.legacy_frames += 1
                                writer.set_status("failed", force=True)
                                raise RecorderProtocolError(
                                    "received a deprecated v1 (Socket.IO/Engine.IO) frame from "
                                    f"{WALLEX_WS_URL}; this recorder implements only the "
                                    "documented v2 Centrifugo protocol")
                            if frame.kind == FRAME_MALFORMED:
                                writer.malformed += 1
                                writer.write_manifest()
                                continue
                            writer.unknown_frames += 1
                            writer.write_manifest()
                    if deadline is not None and now() >= deadline:
                        break
                    raise ConnectionError("websocket stream ended before the recorder deadline")
            except asyncio.CancelledError:
                # Ctrl+C or an external cancellation is an intentional stop, not a
                # connection failure; the manifest must not report a false failure.
                cancelled = True
                if active is not None:
                    writer.discarded_partial_candles += 1
                    active = None
                raise
            except RecorderProtocolError:
                if active is not None:
                    writer.discarded_partial_candles += 1
                    active = None
                # The raise site knows why it gave up; do not infer it afterwards.
                failure_reason = failure_reason or "protocol_error"
                raise
            except Exception as exc:
                writer.last_connection_error_type = type(exc).__name__
                writer.last_connection_error_message = _short(str(exc))
                close_code = _close_code(exc)
                if close_code is not None and close_code >= FATAL_CLOSE_CODE_MIN:
                    writer.fatal_close_code = close_code
                    failure_reason = "fatal_close_code"
                    writer.set_status("failed", force=True)
                    raise RecorderProtocolError(
                        f"server closed the connection with documented fatal code {close_code}; "
                        "retrying cannot fix a client-side protocol fault") from exc
                writer.connection_errors += 1
                if active is not None:
                    writer.discarded_partial_candles += 1
                    active = None
                consecutive_failures += 1
                writer.set_status("reconnecting")
                if consecutive_failures > max_reconnect_attempts:
                    failure_reason = "reconnect_limit"
                    writer.set_status("failed", force=True)
                    raise RuntimeError(
                        "WebSocket reconnect limit exceeded; inspect the recorder manifest") from None
                backoff = reconnect_backoff_seconds * (2 ** min(consecutive_failures - 1, 6))
                if deadline is not None:
                    remaining = deadline - now()
                    if remaining <= 0:
                        break
                    backoff = min(backoff, remaining)
                if backoff:
                    await asyncio.sleep(backoff)
    except BaseException:
        failure_reason = failure_reason or "error"
        raise
    finally:
        if active is not None:
            writer.discarded_partial_candles += 1
        if cancelled:
            writer.finish("stopped", "cancelled")
        elif failure_reason is not None:
            writer.finish("failed", failure_reason)
        else:
            reached_deadline = deadline is not None and now() >= deadline
            writer.finish("stopped", "runtime_limit" if reached_deadline else "interrupted")
    return writer.closed_candles


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wallex-candle-recorder", description="Record public Wallex trade messages into local OHLCV JSONL; no trading.")
    parser.add_argument("--symbol", required=True, help="Exact uppercase Spot symbol, e.g. BTCTMN (verify against the official markets list)")
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--output", default="data/candles.jsonl")
    parser.add_argument("--max-runtime-seconds", type=float, default=0, help="0 means run until interrupted")
    parser.add_argument("--reconnect-backoff-seconds", type=float, default=1.0)
    parser.add_argument("--max-reconnect-attempts", type=int, default=10)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        count = asyncio.run(record_trades(args.symbol, args.interval_seconds, args.output,
            max_runtime_seconds=args.max_runtime_seconds,
            reconnect_backoff_seconds=args.reconnect_backoff_seconds,
            max_reconnect_attempts=args.max_reconnect_attempts))
        print(json.dumps({"closed_candles_written": count, "output": args.output, "trading_enabled": False}))
        return 0
    except KeyboardInterrupt:
        print("recorder interrupted; partial candle was not written", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
