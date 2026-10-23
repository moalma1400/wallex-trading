"""Record Wallex public trade WebSocket messages as local OHLCV candles."""
from __future__ import annotations
import argparse
import asyncio
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Sequence

WALLEX_WS_URL = "wss://api.wallex.ir/connection/websocket"
TRADE_DOC_URL = "https://developers.wallex.ir/socket/trade"
SOCKET_DOC_URL = "https://developers.wallex.ir/socket"
MAX_APPLICATION_PONGS_PER_CONNECTION = 100

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

def is_application_ping(message: str | bytes) -> bool:
    """Recognize legacy PING and the observed empty-object v2 heartbeat."""
    try:
        text = message.decode("utf-8") if isinstance(message, bytes) else message
        if not isinstance(text, str):
            return False
        if text.strip().upper() == "PING":
            return True
        payload = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return False
    return payload == "PING" or payload == ["PING"] or payload == {}


def parse_trade_message(
    message: str | bytes, symbol: str
) -> tuple[datetime, Decimal, Decimal] | None:
    """Parse a legacy trade envelope or a Centrifugo v2 public trade push."""
    try:
        text = message.decode("utf-8") if isinstance(message, bytes) else message
        payload = json.loads(text)
    except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
        return None

    trade = None
    if isinstance(payload, dict):
        push = payload.get("push")
        if isinstance(push, dict) and push.get("channel") == f"public:{symbol}@trade":
            pub = push.get("pub")
            if isinstance(pub, dict) and isinstance(pub.get("data"), dict):
                trade = pub["data"]

    # Retain legacy parsing for compatibility with the existing tests.
    if (
        trade is None
        and isinstance(payload, list)
        and len(payload) == 2
        and payload[0] == f"{symbol}@trade"
        and isinstance(payload[1], dict)
    ):
        trade = payload[1]

    if trade is None:
        return None

    try:
        price = _decimal(trade.get("price"), "price")
        quantity = _decimal(trade.get("quantity"), "quantity")
        stamp = trade.get("timestamp")
        if not isinstance(stamp, str):
            return None
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        parsed = parsed.astimezone(timezone.utc)
        if price <= 0 or quantity <= 0:
            return None
        return parsed, price, quantity
    except (ValueError, TypeError, OverflowError):
        return None

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
    """Append closed candles and maintain a source, freshness, and connection manifest."""
    def __init__(self, output: str | Path, symbol: str, interval_seconds: int) -> None:
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.symbol = symbol
        self.interval_seconds = interval_seconds
        self.manifest_path = self.output.with_suffix(self.output.suffix + ".manifest.json")
        self.started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.written = 0
        self.malformed = 0
        self.last_candle: str | None = None
        self.connection_count = 0
        self.reconnect_count = 0
        self.connection_errors = 0
        self.application_pongs = 0
        self.discarded_partial_candles = 0
        self._write_manifest("starting")

    def write_candle(self, candle: CandleAccumulator) -> None:
        record = candle.as_dict(self.symbol)
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        self.written += 1
        self.last_candle = record["timestamp"]
        self._write_manifest("recording")

    def _write_manifest(self, status: str, last_error_type: str | None = None) -> None:
        manifest = {
            "schema_version": 1, "symbol": self.symbol, "interval_seconds": self.interval_seconds,
            "websocket_url": WALLEX_WS_URL, "documentation_url": TRADE_DOC_URL,
            "socket_documentation_url": SOCKET_DOC_URL,
            "started_at_utc": self.started_at,
            "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "status": status, "closed_candles_written_this_run": self.written,
            "malformed_or_unmatched_messages": self.malformed, "last_closed_candle_utc": self.last_candle,
            "connection_count": self.connection_count, "reconnect_count": self.reconnect_count,
            "connection_errors": self.connection_errors, "application_pongs_sent": self.application_pongs,
            "discarded_partial_candles": self.discarded_partial_candles,
            "gaps_possible_on_disconnect": self.connection_errors > 0 or self.reconnect_count > 0,
            "last_connection_error_type": last_error_type,
        }
        self.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

async def record_trades(symbol: str, interval_seconds: int, output: str | Path, *,
                        max_runtime_seconds: float = 0,
                        connector: Callable[..., Any] | None = None,
                        clock: Callable[[], float] | None = None,
                        reconnect_backoff_seconds: float = 1.0,
                        max_reconnect_attempts: int = 10) -> int:
    """Record a public feed with bounded reconnects, recording possible data gaps.

    Application PING frames receive at most 100 PONG messages on one socket,
    matching the published Socket overview limit. Outages discard the active
    incomplete candle; no missing data is fabricated or backfilled.
    """
    if not symbol or not symbol.isascii() or not symbol.replace("_", "").isalnum() or symbol.upper() != symbol:
        raise ValueError("symbol must be an uppercase alphanumeric Wallex market symbol")
    if not 1 <= interval_seconds <= 86400:
        raise ValueError("interval-seconds must be between 1 and 86400")
    if max_runtime_seconds < 0:
        raise ValueError("max-runtime-seconds cannot be negative")
    if reconnect_backoff_seconds < 0:
        raise ValueError("reconnect-backoff-seconds cannot be negative")
    if isinstance(max_reconnect_attempts, bool) or not isinstance(max_reconnect_attempts, int) or max_reconnect_attempts < 0:
        raise ValueError("max-reconnect-attempts must be a non-negative integer")
    if connector is None:
        try:
            from websockets.asyncio.client import connect
        except ImportError as exc:
            raise RuntimeError("install project dependencies including websockets") from exc
        connector = connect

    now = clock or time.monotonic
    writer = CandleWriter(output, symbol, interval_seconds)
    active: CandleAccumulator | None = None
    deadline = now() + max_runtime_seconds if max_runtime_seconds else None
    consecutive_failures = 0
    last_error_type: str | None = None
    try:
        while deadline is None or now() < deadline:
            try:
                async with connector(WALLEX_WS_URL, open_timeout=15, close_timeout=5,
                                     ping_interval=20, ping_timeout=20, max_size=1_000_000) as websocket:
                    writer.connection_count += 1
                    if writer.connection_count > 1:
                        writer.reconnect_count += 1
                    writer._write_manifest("recording", last_error_type)
                    await websocket.send(json.dumps({"id": 1, "connect": {}}))

                    # Wait for the matching connect acknowledgement. Bound the
                    # wait even when the recorder is configured to run forever.
                    connect_deadline = now() + 15
                    while True:
                        remaining = connect_deadline - now()
                        if deadline is not None:
                            remaining = min(remaining, deadline - now())
                        if remaining <= 0:
                            raise TimeoutError("Centrifugo connect acknowledgement timed out")
                        reply = await asyncio.wait_for(websocket.recv(), timeout=remaining)
                        try:
                            control = json.loads(
                                reply.decode("utf-8") if isinstance(reply, bytes) else reply
                            )
                        except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
                            writer.malformed += 1
                            continue

                        if isinstance(control, dict) and control.get("id") == 1:
                            if "error" in control:
                                raise ConnectionError("Centrifugo connect command failed")
                            if "connect" in control:
                                break

                        if is_application_ping(reply):
                            await websocket.send("{}" if control == {} else "PONG")
                            writer.application_pongs += 1

                    await websocket.send(json.dumps({
                        "id": 2,
                        "subscribe": {"channel": f"public:{symbol}@trade"}
                    }))
                    pongs_this_connection = 0
                    subscription_confirmed = False
                    subscription_deadline = now() + 15
                    while True:
                        remaining = None
                        if deadline is not None:
                            remaining = deadline - now()
                            if remaining <= 0:
                                break

                        # Do not silently record an unconfirmed subscription.
                        # Continue processing early trade pushes if any arrive.
                        if not subscription_confirmed:
                            ack_remaining = subscription_deadline - now()
                            if ack_remaining <= 0:
                                raise TimeoutError(
                                    "Centrifugo subscription acknowledgement timed out"
                                )
                            timeout = ack_remaining if remaining is None else min(
                                remaining, ack_remaining
                            )
                            try:
                                message = await asyncio.wait_for(
                                    websocket.recv(), timeout=timeout
                                )
                            except asyncio.TimeoutError:
                                if deadline is not None and now() >= deadline:
                                    break
                                raise TimeoutError(
                                    "Centrifugo subscription acknowledgement timed out"
                                ) from None
                        elif remaining is not None:
                            try:
                                message = await asyncio.wait_for(
                                    websocket.recv(), timeout=remaining
                                )
                            except asyncio.TimeoutError:
                                break
                        else:
                            message = await websocket.recv()

                        if is_application_ping(message):
                            if pongs_this_connection >= MAX_APPLICATION_PONGS_PER_CONNECTION:
                                raise ConnectionError("application ping limit reached")
                            try:
                                heartbeat = json.loads(
                                    message.decode("utf-8") if isinstance(message, bytes) else message
                                )
                            except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
                                heartbeat = "PING"
                            await websocket.send("{}" if heartbeat == {} else "PONG")
                            pongs_this_connection += 1
                            writer.application_pongs += 1
                            writer._write_manifest("recording", last_error_type)
                            continue
                        trade = parse_trade_message(message, symbol)
                        if trade is None:
                            try:
                                event = json.loads(
                                    message.decode("utf-8") if isinstance(message, bytes) else message
                                )
                            except (json.JSONDecodeError, UnicodeDecodeError, TypeError):
                                event = None

                            if isinstance(event, dict):
                                if event.get("id") == 2:
                                    if "error" in event:
                                        raise ConnectionError(
                                            "Centrifugo subscription command failed"
                                        )
                                    if "subscribe" in event:
                                        subscription_confirmed = True
                                        continue
                                    raise ConnectionError(
                                        "Unexpected Centrifugo subscription acknowledgement"
                                    )
                                # Other command acknowledgements, pushes for unrelated
                                # channels and protocol control objects aren't trades.
                                if "id" in event or "push" in event or event == {}:
                                    continue

                            writer.malformed += 1
                            continue
                        timestamp, price, quantity = trade
                        consecutive_failures = 0
                        next_candle = CandleAccumulator.from_trade(timestamp, price, quantity, interval_seconds)
                        if active is None:
                            active = next_candle
                        elif next_candle.start == active.start:
                            active.add(price, quantity)
                        elif next_candle.start > active.start:
                            writer.write_candle(active)
                            active = next_candle
                        else:
                            writer.malformed += 1
                    if deadline is not None and now() >= deadline:
                        break
                    # A clean but unexpected stream end is also a disconnect.
                    raise ConnectionError("websocket stream ended before recorder deadline")
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                last_error_type = type(exc).__name__
                writer.connection_errors += 1
                if active is not None:
                    writer.discarded_partial_candles += 1
                    active = None
                consecutive_failures += 1
                writer._write_manifest("reconnecting", last_error_type)
                if consecutive_failures > max_reconnect_attempts:
                    raise RuntimeError("WebSocket reconnect limit exceeded; inspect the recorder manifest") from None
                if deadline is not None:
                    remaining = deadline - now()
                    if remaining <= 0:
                        break
                    await asyncio.sleep(min(reconnect_backoff_seconds * (2 ** min(consecutive_failures - 1, 6)), remaining))
                elif reconnect_backoff_seconds:
                    await asyncio.sleep(reconnect_backoff_seconds * (2 ** min(consecutive_failures - 1, 6)))
    finally:
        if active is not None:
            writer.discarded_partial_candles += 1
        writer._write_manifest("stopped", last_error_type)
    return writer.written

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wallex-candle-recorder", description="Record public Wallex trade messages into local OHLCV JSONL; no trading.")
    parser.add_argument("--symbol", required=True, help="Exact uppercase Spot symbol, e.g. BTCUSDT")
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
