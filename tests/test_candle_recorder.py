"""Offline, deterministic tests for the public trade candle recorder.

Every wire frame used here is taken from the official Wallex v2 documentation:

* raw protocol frames, errors and close codes:
  https://developers.wallex.ir/docs/socket-raw-protocol
* public trade channel and payload:
  https://developers.wallex.ir/docs/socket-trade
* channel names and the deprecated v1 transport:
  https://developers.wallex.ir/docs/socket-intro

No test opens a socket or needs credentials, and no fixture is presented as a
live capture. Live behaviour is not established by these tests; see
``docs/agent/CANDLE-RECORDER.md`` for the runtime verification status.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest

from wallex_agent.candle_recorder import (
    FRAME_HANDSHAKE,
    FRAME_LEGACY_V1,
    FRAME_MALFORMED,
    FRAME_PUBLICATION,
    FRAME_SERVER_ERROR,
    FRAME_SERVER_PING,
    FRAME_SUBSCRIPTION_ACK,
    FRAME_UNKNOWN,
    CandleAccumulator,
    CandleWriter,
    RecorderProtocolError,
    classify_server_message,
    parse_trade_payload,
    record_trades,
    split_messages,
    trade_channel,
    validate_symbol,
)

SYMBOL = "BTCTMN"
CHANNEL = f"public:{SYMBOL}@trade"
BLOCK = object()   # blocks like a real socket until the recorder cancels recv()
STOP = object()    # reports the recorder's own timeout immediately (no sleeping)
NON_TEXT = object()  # delivers a frame that is neither str nor bytes


class FakeClock:
    """Monotonic-like clock that advances a fixed step per call.

    Injecting it lets deadline-driven tests finish deterministically in
    microseconds instead of depending on wall-clock timing.
    """

    def __init__(self, step=0.01, start=0.0):
        self.value = start
        self.step = step

    def __call__(self):
        self.value += self.step
        return self.value


# --------------------------------------------------------------------------
# Documented frames
# --------------------------------------------------------------------------
def publication(price="15791249224", quantity="0.000243", timestamp="2026-08-25T16:38:23Z",
                channel=CHANNEL, **extra):
    """The documented ``push`` envelope for a public trade channel."""
    data = {"isBuyOrder": True, "quantity": quantity, "price": price, "timestamp": timestamp}
    data.update(extra)
    return {"push": {"channel": channel, "pub": {"data": data}}}


def connect_reply(request_id=1, ping=25):
    return {"id": request_id, "connect": {"client": "5f194d9b-57fb-45d8-bd2d-6efe83edf0ac",
                                          "ping": ping, "pong": True}}


def subscribe_ack(request_id=2):
    return {"id": request_id, "subscribe": {}}


def error_frame(request_id=2, code=102, message="unknown channel"):
    return {"id": request_id, "error": {"code": code, "message": message}}


class FakeWebSocket:
    """Scripted stand-in for one WebSocket connection."""

    def __init__(self, script):
        self.script = list(script)
        self.sent = []
        self.closed = 0
        self.deadline_fired = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.closed += 1
        return False

    async def send(self, value):
        self.sent.append(value)

    async def recv(self):
        if self.deadline_fired:
            # Once the recorder's own deadline has fired, keep reporting it:
            # the recorder is expected to exit its loop on the next check.
            raise asyncio.TimeoutError("simulated recorder deadline")
        if not self.script:
            raise OSError("synthetic disconnect")
        item = self.script.pop(0)
        if item is BLOCK:
            # Cancelled by the recorder's deadline via asyncio.wait_for.
            await asyncio.sleep(3600)
        if item is STOP:
            # The recorder's own timer fired before the next frame arrived.
            self.deadline_fired = True
            raise asyncio.TimeoutError("simulated recorder deadline")
        if item is NON_TEXT:
            return 1234
        if isinstance(item, BaseException):
            raise item
        return item if isinstance(item, (str, bytes)) else json.dumps(item)


def connector_for(*sockets):
    queued = list(sockets)
    calls = []

    def connector(*args, **kwargs):
        calls.append((args, kwargs))
        if not queued:
            raise AssertionError("connector called more times than the script provides")
        return queued.pop(0)

    connector.calls = calls
    return connector


def read_manifest(tmp_path, name="candles.jsonl"):
    return json.loads((tmp_path / f"{name}.manifest.json").read_text(encoding="utf-8"))


def sent_json(websocket):
    return [json.loads(value) for value in websocket.sent]


# --------------------------------------------------------------------------
# Protocol classification
# --------------------------------------------------------------------------
def test_documented_connect_reply_is_classified_as_handshake_not_trade():
    frame = classify_server_message(json.dumps(connect_reply()))
    assert frame.kind == FRAME_HANDSHAKE
    assert frame.request_id == 1
    assert frame.server_ping_seconds == 25


def test_documented_subscription_ack_is_classified_as_ack():
    frame = classify_server_message(json.dumps(subscribe_ack()))
    assert frame.kind == FRAME_SUBSCRIPTION_ACK
    assert frame.request_id == 2


def test_documented_trade_publication_is_recognized_and_parsed():
    frame = classify_server_message(json.dumps(publication()))
    assert frame.kind == FRAME_PUBLICATION
    assert frame.channel == CHANNEL
    parsed = parse_trade_payload(frame.data)
    assert parsed is not None
    stamp, price, quantity = parsed
    assert stamp == datetime(2026, 8, 25, 16, 38, 23, tzinfo=timezone.utc)
    assert price == Decimal("15791249224")
    assert quantity == Decimal("0.000243")


def test_documented_error_frames_are_classified_as_server_errors():
    frame = classify_server_message(json.dumps(error_frame(code=102, message="unknown channel")))
    assert frame.kind == FRAME_SERVER_ERROR
    assert frame.request_id == 2
    assert (frame.error_code, frame.error_message) == (102, "unknown channel")

    # The deprecated v1 transport documents a string error body; still an error.
    legacy_style = classify_server_message(json.dumps({"error": "invalid subscribe request"}))
    assert legacy_style.kind == FRAME_SERVER_ERROR
    assert legacy_style.error_message == "invalid subscribe request"


def test_documented_heartbeat_is_an_empty_object():
    assert classify_server_message("{}").kind == FRAME_SERVER_PING
    assert classify_server_message("  {}  ").kind == FRAME_SERVER_PING
    # An empty object is a heartbeat, never a trade and never malformed.
    assert classify_server_message("{}").data is None


def test_valid_but_unrecognized_events_are_not_counted_as_malformed():
    for payload in ({"id": 9, "history": {}}, {"id": 10, "unsubscribe": {}}, [1, 2, 3], "text", None, 42):
        frame = classify_server_message(json.dumps(payload))
        assert frame.kind in {FRAME_UNKNOWN, FRAME_LEGACY_V1}, payload


def test_malformed_or_structurally_invalid_frames_are_rejected():
    for raw in ("{bad", "", "not json", b"\xff\xfe", 12345):
        assert classify_server_message(raw).kind == FRAME_MALFORMED, raw
    for payload in (
        {"push": "not-an-object"},
        {"push": {"channel": CHANNEL}},
        {"push": {"channel": CHANNEL, "pub": {"data": "not-an-object"}}},
        {"push": {"pub": {"data": {}}}},
        {"connect": []},
        {"subscribe": []},
    ):
        assert classify_server_message(json.dumps(payload)).kind == FRAME_MALFORMED, payload


def test_deprecated_engineio_handshake_is_recognized_separately():
    """The observed legacy ``/ws`` handshake must never be read as trade data."""
    legacy = {"sid": "redacted", "upgrades": [], "pingInterval": 20000,
              "pingTimeout": 30000, "maxPayload": 1048576}
    assert classify_server_message(json.dumps(legacy)).kind == FRAME_LEGACY_V1
    # The deprecated v1 publication envelope is also recognized as legacy.
    legacy_trade = [f"{SYMBOL}@trade", {"isBuyOrder": True, "quantity": "1", "price": "2",
                                       "timestamp": "2026-08-25T16:38:23Z"}]
    assert classify_server_message(json.dumps(legacy_trade)).kind == FRAME_LEGACY_V1


def test_split_messages_handles_multiple_messages_per_frame():
    frame = json.dumps(subscribe_ack()) + "\n" + "{}" + "\n\n"
    assert split_messages(frame) == [json.dumps(subscribe_ack()), "{}"]
    assert split_messages(b'{"a":1}\n{"b":2}') == ['{"a":1}', '{"b":2}']
    with pytest.raises(UnicodeDecodeError):
        split_messages(b"\xff\xfe")
    with pytest.raises(TypeError):
        split_messages(1234)  # type: ignore[arg-type]


def test_trade_payload_validation_rejects_invalid_data():
    good = {"price": "100", "quantity": "1", "timestamp": "2026-08-25T16:38:23Z"}
    assert parse_trade_payload(good) is not None
    for broken in (
        {**good, "price": "NaN"},
        {**good, "price": "0"},
        {**good, "price": "-1"},
        {**good, "price": None},
        {**good, "price": {"nested": 1}},
        {**good, "quantity": "0"},
        {**good, "quantity": "Infinity"},
        {**good, "timestamp": None},
        {**good, "timestamp": 1766800000},
        {**good, "timestamp": "2026-08-25T16:38:23"},
        {**good, "timestamp": "not-a-time"},
        {"price": "1", "quantity": "1"},
        None,
        "not-a-mapping",
    ):
        assert parse_trade_payload(broken) is None, broken


def test_trade_payload_normalizes_offsets_to_utc():
    parsed = parse_trade_payload({"price": "10", "quantity": "2",
                                  "timestamp": "2026-10-23T12:00:01+02:00"})
    assert parsed is not None
    assert parsed[0] == datetime(2026, 10, 23, 10, 0, 1, tzinfo=timezone.utc)


def test_trade_channel_and_symbol_validation_follow_documented_alphabet():
    assert trade_channel("BTCTMN") == "public:BTCTMN@trade"
    assert validate_symbol("USDT-TMN_X1") == "USDT-TMN_X1"
    for bad in ("btctmn", "BTC:USDT", "BTC@trade", "private:user#1", "", "-BTC", "A" * 33, "BTC USDT"):
        with pytest.raises(ValueError):
            validate_symbol(bad)


def test_numeric_json_price_and_quantity_keep_decimal_precision():
    """A JSON number must not pass through a binary float on the way to OHLCV."""
    raw = ('{"push": {"channel": "' + CHANNEL + '", "pub": {"data": {'
           '"isBuyOrder": true, "price": 15791249224.123456789012345, '
           '"quantity": 0.000243000000000000001, "timestamp": "2026-08-25T16:38:23Z"}}}}')
    frame = classify_server_message(raw)
    assert frame.kind == FRAME_PUBLICATION
    parsed = parse_trade_payload(frame.data)
    assert parsed is not None
    _, price, quantity = parsed
    assert str(price) == "15791249224.123456789012345"
    assert str(quantity) == "0.000243000000000000001"


def test_numeric_request_ids_are_still_accepted():
    frame = classify_server_message('{"id": 1.0, "connect": {"client": "x", "ping": 25}}')
    assert frame.kind == FRAME_HANDSHAKE
    assert frame.request_id == 1


def test_unsolicited_subscription_ack_is_not_accepted_as_our_subscription(tmp_path):
    """A documented ack shape with the wrong id proves nothing about our channel."""
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([connect_reply(request_id=1), subscribe_ack(request_id=99), STOP])
    with pytest.raises(RuntimeError, match="reconnect limit exceeded"):
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                  reconnect_backoff_seconds=0, max_reconnect_attempts=0,
                                  ack_timeout_seconds=0.05, clock=FakeClock()))

    manifest = read_manifest(tmp_path)
    assert manifest["subscription_status"] == "pending"
    assert manifest["subscription_acknowledged"] is False
    assert manifest["subscription_ack_frames_received"] == 0
    assert manifest["unknown_frames_ignored"] == 1


def test_command_error_for_another_channel_does_not_abort_the_recorder(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        error_frame(request_id=7, code=106, message="limit exceeded"),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0,
                                        clock=FakeClock(), ack_timeout_seconds=1.0))

    manifest = read_manifest(tmp_path)
    assert written == 1
    assert manifest["server_error_frames_received"] == 1
    assert manifest["last_server_error"]["code"] == 106
    assert manifest["subscription_status"] == "acknowledged"
    assert manifest["status"] == "stopped"


def test_non_text_frame_is_counted_as_malformed_without_crashing(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(), b"\xff\xfe", NON_TEXT,
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0,
                                        clock=FakeClock(), ack_timeout_seconds=1.0))

    manifest = read_manifest(tmp_path)
    assert written == 1
    assert manifest["malformed_or_unmatched_messages"] == 2
    assert manifest["status"] == "stopped"


def test_oversized_and_noisy_server_text_is_bounded_in_the_manifest(tmp_path):
    output = tmp_path / "candles.jsonl"
    noisy = "x" * 5000 + "\nsecond line"
    socket = FakeWebSocket([connect_reply(), subscribe_ack(),
                            error_frame(request_id=7, code=999, message=noisy), STOP])
    asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                              max_runtime_seconds=1.0, reconnect_backoff_seconds=0,
                              clock=FakeClock(), ack_timeout_seconds=1.0))

    manifest = read_manifest(tmp_path)
    stored = manifest["last_server_error"]["message"]
    assert len(stored) <= 200 and "\n" not in stored


def test_wrong_connect_ack_id_is_not_accepted_as_a_handshake(tmp_path):
    """The documented connect reply must carry our own command id."""
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([connect_reply(request_id=7), subscribe_ack(request_id=99), STOP])
    with pytest.raises(RuntimeError, match="reconnect limit exceeded"):
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                  reconnect_backoff_seconds=0, max_reconnect_attempts=0,
                                  ack_timeout_seconds=0.05, clock=FakeClock()))

    manifest = read_manifest(tmp_path)
    assert manifest["handshake_frames_received"] == 0
    assert manifest["subscription_ack_frames_received"] == 0
    assert manifest["subscription_acknowledged"] is False
    assert manifest["subscription_status"] == "pending"
    assert manifest["unknown_frames_ignored"] == 2
    assert manifest["last_connection_error_type"] == "TimeoutError"


def test_handshake_timeout_closes_the_socket(tmp_path):
    """A setup failure must not leak the connection."""
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([BLOCK])
    with pytest.raises(RuntimeError, match="reconnect limit exceeded"):
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                  reconnect_backoff_seconds=0, max_reconnect_attempts=0,
                                  ack_timeout_seconds=0.05))
    assert socket.closed == 1
    manifest = read_manifest(tmp_path)
    assert manifest["connection_count"] == 1
    assert manifest["transport_frames_received"] == 0
    assert manifest["status"] == "failed"
    assert not output.exists()


def test_heartbeat_silence_reconnects_and_is_recorded(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([connect_reply(), subscribe_ack(), BLOCK])
    with pytest.raises(RuntimeError, match="reconnect limit exceeded"):
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                  reconnect_backoff_seconds=0, max_reconnect_attempts=0,
                                  ack_timeout_seconds=5.0, heartbeat_timeout_seconds=0.05))

    manifest = read_manifest(tmp_path)
    assert manifest["connection_errors"] == 1
    assert manifest["last_connection_error_type"] == "TimeoutError"
    assert "no frames received" in manifest["last_connection_error_message"]
    assert manifest["subscription_acknowledged"] is True   # it *was* acknowledged
    assert manifest["gaps_possible_on_disconnect"] is True
    assert socket.closed == 1


def test_reconnect_resends_connect_and_subscribe(tmp_path):
    output = tmp_path / "candles.jsonl"
    first = FakeWebSocket([connect_reply(), subscribe_ack(), OSError("synthetic disconnect")])
    second = FakeWebSocket([connect_reply(), subscribe_ack(), STOP])
    asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(first, second),
                              max_runtime_seconds=1.0, reconnect_backoff_seconds=0,
                              clock=FakeClock(), ack_timeout_seconds=1.0))

    for socket in (first, second):
        commands = sent_json(socket)
        assert commands[0] == {"id": 1, "connect": {}}
        assert commands[1] == {"id": 2, "subscribe": {"channel": CHANNEL}}
    manifest = read_manifest(tmp_path)
    assert manifest["connection_count"] == 2
    assert manifest["reconnect_count"] == 1
    assert manifest["subscription_status"] == "acknowledged"


def test_cancellation_during_connection_setup_is_clean(tmp_path):
    """SIGINT while waiting for the subscribe ack must not leave resources behind."""
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([connect_reply(), BLOCK])   # subscribe is never acknowledged

    async def scenario():
        task = asyncio.create_task(record_trades(
            SYMBOL, 60, output, connector=connector_for(socket), clock=FakeClock(),
            reconnect_backoff_seconds=0))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    manifest = read_manifest(tmp_path)
    assert manifest["status"] == "stopped"
    assert manifest["stop_reason"] == "cancelled"
    assert manifest["subscription_status"] == "pending"
    assert manifest["subscription_acknowledged"] is False
    assert manifest["connection_errors"] == 0
    assert socket.closed == 1
    assert not output.exists()


# --------------------------------------------------------------------------
# Candle aggregation
# --------------------------------------------------------------------------
def test_bucket_aggregation_produces_correct_ohlcv():
    candle = CandleAccumulator.from_trade(
        datetime(2026, 10, 23, 10, 0, 1, tzinfo=timezone.utc), Decimal("100"), Decimal("2"), 60)
    candle.add(Decimal("103"), Decimal("1.5"))
    candle.add(Decimal("99"), Decimal("3"))
    candle.add(Decimal("101"), Decimal("0.5"))
    result = candle.as_dict(SYMBOL)
    assert result["timestamp"] == "2026-10-23T10:00:00Z"
    assert result["open"] == "100"       # first trade in the bucket
    assert result["high"] == "103"
    assert result["low"] == "99"
    assert result["close"] == "101"      # last trade in the bucket
    assert result["volume"] == "7.0"     # base-asset quantity sum
    assert result["trade_count"] == 4
    assert result["symbol"] == SYMBOL
    assert result["interval_seconds"] == 60
    assert result["source"] == "wallex_public_trade_websocket"


def test_utc_bucket_alignment_for_non_aligned_trades():
    stamp = datetime(2026, 10, 23, 10, 7, 42, tzinfo=timezone.utc)
    assert CandleAccumulator.from_trade(stamp, Decimal("1"), Decimal("1"), 60).start.isoformat() \
        == "2026-10-23T10:07:00+00:00"
    assert CandleAccumulator.from_trade(stamp, Decimal("1"), Decimal("1"), 300).start.isoformat() \
        == "2026-10-23T10:05:00+00:00"
    # The same instant expressed in a +03:00 zone must land in the same UTC bucket.
    other_zone = datetime(2026, 10, 23, 13, 7, 42, tzinfo=timezone(timedelta(hours=3)))
    assert CandleAccumulator.from_trade(other_zone, Decimal("1"), Decimal("1"), 60).start.isoformat() \
        == "2026-10-23T10:07:00+00:00"


# --------------------------------------------------------------------------
# End-to-end recorder behaviour with a scripted connection
# --------------------------------------------------------------------------
def test_candle_is_finalized_only_when_a_later_bucket_arrives(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(),
        subscribe_ack(),
        publication(price="100", quantity="2", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:00:31Z"),
        publication(price="102", quantity="3", timestamp="2026-10-23T10:01:05Z"),
        STOP,
    ])
    connector = connector_for(socket)

    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector,
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                                        ack_timeout_seconds=1.0, heartbeat_timeout_seconds=30))

    assert written == 1
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert len(rows) == 1
    assert rows[0]["timestamp"] == "2026-10-23T10:00:00Z"
    assert rows[0]["open"] == "100" and rows[0]["high"] == "101"
    assert rows[0]["low"] == "100" and rows[0]["close"] == "101"
    assert rows[0]["volume"] == "3" and rows[0]["trade_count"] == 2

    manifest = read_manifest(tmp_path)
    assert manifest["status"] == "stopped"
    assert manifest["stop_reason"] == "runtime_limit"
    assert manifest["subscription_status"] == "acknowledged"
    assert manifest["closed_candles_written_this_run"] == 1
    assert manifest["discarded_partial_candles"] == 1
    assert manifest["live_trade_received"] is True
    # Both documented client commands were sent, in order.
    commands = sent_json(socket)
    assert commands[0] == {"id": 1, "connect": {}}
    assert commands[1] == {"id": 2, "subscribe": {"channel": CHANNEL}}


def test_no_candle_file_is_created_when_only_a_partial_bucket_is_seen(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        STOP,
    ])
    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                                        ack_timeout_seconds=1.0))

    assert written == 0
    assert not output.exists()
    manifest = read_manifest(tmp_path)
    assert manifest["closed_candles_written_this_run"] == 0
    assert manifest["trade_events_received"] == 1
    assert manifest["discarded_partial_candles"] == 1
    assert manifest["last_closed_candle_utc"] is None


def test_one_transport_frame_can_carry_several_documented_messages(tmp_path):
    """The official samples split every frame on newlines before dispatching."""
    output = tmp_path / "candles.jsonl"
    frame = "\n".join([
        json.dumps(connect_reply()),
        json.dumps(subscribe_ack()),
        json.dumps(publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z")),
        json.dumps(publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z")),
    ])
    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(FakeWebSocket([frame, STOP])),
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                                        ack_timeout_seconds=1.0))

    assert written == 1
    manifest = read_manifest(tmp_path)
    assert manifest["transport_frames_received"] == 1
    assert manifest["messages_received"] == 4
    assert manifest["handshake_frames_received"] == 1
    assert manifest["subscription_ack_frames_received"] == 1
    assert manifest["trade_events_received"] == 2
    assert manifest["malformed_or_unmatched_messages"] == 0


def test_documented_heartbeat_is_answered_with_an_empty_object(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket(["{}", connect_reply(), subscribe_ack(), "{}", STOP])
    asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                              max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                              ack_timeout_seconds=1.0))

    assert socket.sent.count("{}") == 2
    manifest = read_manifest(tmp_path)
    assert manifest["server_ping_frames_received"] == 2
    assert manifest["server_pongs_sent"] == 2
    assert manifest["transport_frames_received"] == 4
    assert manifest["messages_received"] == 4
    assert manifest["server_ping_interval_seconds"] == 25


def test_subscription_rejection_is_fatal_and_recorded(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([connect_reply(), error_frame(request_id=2, code=102)])
    connector = connector_for(socket)

    with pytest.raises(RecorderProtocolError) as excinfo:
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector,
                                  max_runtime_seconds=5, reconnect_backoff_seconds=0))

    assert "102" in str(excinfo.value) and "unknown channel" in str(excinfo.value)
    assert len(connector.calls) == 1, "a documented rejection must not be retried"
    manifest = read_manifest(tmp_path)
    assert manifest["status"] == "failed"
    assert manifest["stop_reason"] == "subscription_rejected"
    assert manifest["subscription_status"] == "rejected"
    assert manifest["last_subscription_error_code"] == 102
    assert manifest["last_subscription_error_message"] == "unknown channel"
    assert manifest["last_server_error"]["code"] == 102
    assert socket.closed == 1, "the rejected session must still be closed"
    assert not output.exists()


def test_publication_for_another_symbol_cannot_create_a_candle(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        publication(channel="public:ETHUSDT@trade", price="100", quantity="1",
                    timestamp="2026-10-23T10:00:01Z"),
        STOP,
    ])
    asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                              max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                              ack_timeout_seconds=1.0))

    assert not output.exists()
    manifest = read_manifest(tmp_path)
    assert manifest["other_channel_publications_ignored"] == 1
    assert manifest["trade_events_received"] == 0
    assert manifest["malformed_or_unmatched_messages"] == 0


def test_malformed_messages_are_counted_without_ending_the_session(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        "{bad",
        json.dumps(publication(price="NaN")),
        {"id": 77, "futureFeature": {}},
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                                        ack_timeout_seconds=1.0))

    manifest = read_manifest(tmp_path)
    assert written == 1
    assert manifest["malformed_or_unmatched_messages"] == 2
    assert manifest["unknown_frames_ignored"] == 1
    assert manifest["trade_events_received"] == 2
    assert manifest["connection_errors"] == 0


def test_late_trade_is_counted_separately_from_malformed_data(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        publication(price="99", quantity="1", timestamp="2026-10-23T10:00:59Z"),  # late
        STOP,
    ])
    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                                        ack_timeout_seconds=1.0))

    manifest = read_manifest(tmp_path)
    assert written == 1
    assert manifest["late_or_out_of_order_trades_ignored"] == 1
    assert manifest["malformed_or_unmatched_messages"] == 0
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    # The already-written bucket is never modified in place.
    assert rows[0]["open"] == "100" and rows[0]["close"] == "100"
    assert rows[0]["trade_count"] == 1


def test_duplicate_trades_in_the_same_bucket_are_aggregated(tmp_path):
    """Trade channels carry no offset/sequence field, so duplicates cannot be deduplicated."""
    output = tmp_path / "candles.jsonl"
    duplicate = publication(price="100", quantity="2", timestamp="2026-10-23T10:00:05Z")
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(), duplicate, duplicate,
        publication(price="100", quantity="1", timestamp="2026-10-23T10:01:05Z"),
        STOP,
    ])
    asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                              max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                              ack_timeout_seconds=1.0))
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert rows[0]["trade_count"] == 2
    assert rows[0]["volume"] == "4"


def test_legacy_v1_transport_frame_fails_closed(tmp_path):
    output = tmp_path / "candles.jsonl"
    legacy = {"sid": "redacted", "upgrades": [], "pingInterval": 20000,
              "pingTimeout": 30000, "maxPayload": 1048576}
    connector = connector_for(FakeWebSocket([legacy]))
    with pytest.raises(RecorderProtocolError) as excinfo:
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector,
                                  max_runtime_seconds=5, reconnect_backoff_seconds=0))
    assert "deprecated v1" in str(excinfo.value)
    assert len(connector.calls) == 1
    manifest = read_manifest(tmp_path)
    assert manifest["legacy_v1_frames_ignored"] == 1
    assert manifest["status"] == "failed"


def test_connection_failures_are_bounded_and_manifest_is_finalized(tmp_path):
    output = tmp_path / "connect-fail.jsonl"
    calls = []

    class FailedConnection:
        async def __aenter__(self):
            raise OSError("synthetic connect failure")

        async def __aexit__(self, *args):
            return False

    def connector(*args, **kwargs):
        calls.append(1)
        return FailedConnection()

    with pytest.raises(RuntimeError, match="reconnect limit exceeded"):
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector,
                                  reconnect_backoff_seconds=0, max_reconnect_attempts=2))

    assert len(calls) == 3
    manifest = read_manifest(tmp_path, "connect-fail.jsonl")
    assert manifest["connection_errors"] == 3
    assert manifest["connection_count"] == 0
    assert manifest["status"] == "failed"
    assert manifest["stop_reason"] == "reconnect_limit"
    assert manifest["gaps_possible_on_disconnect"] is True
    assert manifest["last_connection_error_type"] == "OSError"
    assert not output.exists()


def test_reconnect_is_observable_and_discards_the_partial_candle(tmp_path):
    output = tmp_path / "candles.jsonl"
    first = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        OSError("synthetic disconnect"),
    ])
    second = FakeWebSocket([connect_reply(), subscribe_ack(), STOP])
    connector = connector_for(first, second)

    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector,
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                                        ack_timeout_seconds=1.0))

    assert written == 0
    assert len(connector.calls) == 2
    manifest = read_manifest(tmp_path)
    assert manifest["connection_count"] == 2
    assert manifest["reconnect_count"] == 1
    assert manifest["connection_errors"] == 1
    assert manifest["gaps_possible_on_disconnect"] is True
    # The partial candle is dropped at the disconnect; the second connection
    # receives no trade, so nothing else is discarded at shutdown.
    assert manifest["discarded_partial_candles"] == 1
    assert manifest["status"] == "stopped"
    # Both connections were closed through their context manager, not leaked.
    assert first.closed == 1 and second.closed == 1


def test_fatal_close_code_is_never_retried(tmp_path):
    class FatalClose(Exception):
        def __init__(self, code):
            super().__init__(f"connection closed with code {code}")
            self.code = code

    output = tmp_path / "candles.jsonl"
    connector = connector_for(FakeWebSocket([connect_reply(), subscribe_ack(), FatalClose(3501)]))
    with pytest.raises(RecorderProtocolError, match="3501"):
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector,
                                  max_runtime_seconds=5, reconnect_backoff_seconds=0))

    assert len(connector.calls) == 1
    manifest = read_manifest(tmp_path)
    assert manifest["fatal_close_code"] == 3501
    assert manifest["gaps_possible_on_disconnect"] is True
    assert manifest["status"] == "failed"
    assert manifest["stop_reason"] == "fatal_close_code"


def test_missing_subscription_ack_times_out_without_claiming_subscription(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([connect_reply(), STOP])
    with pytest.raises(RuntimeError, match="reconnect limit exceeded"):
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                  reconnect_backoff_seconds=0, max_reconnect_attempts=0,
                                  ack_timeout_seconds=0.05, clock=FakeClock()))

    assert socket.closed == 1
    manifest = read_manifest(tmp_path)
    assert manifest["handshake_frames_received"] >= 1
    assert manifest["subscription_ack_frames_received"] == 0
    assert manifest["subscription_status"] == "pending"
    assert manifest["subscription_acknowledged"] is False
    assert manifest["connection_errors"] == 1
    assert manifest["last_connection_error_type"] == "TimeoutError"


def test_cancellation_is_reported_as_an_intentional_stop(tmp_path):
    """Ctrl+C must not be recorded as a connection failure."""
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        BLOCK,
    ])

    async def scenario():
        task = asyncio.create_task(record_trades(
            SYMBOL, 60, output, connector=connector_for(socket), clock=FakeClock(),
            reconnect_backoff_seconds=0, ack_timeout_seconds=1.0))
        await asyncio.sleep(0.05)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(scenario())
    manifest = read_manifest(tmp_path)
    assert manifest["status"] == "stopped"
    assert manifest["stop_reason"] == "cancelled"
    assert manifest["connection_errors"] == 0
    assert manifest["discarded_partial_candles"] == 1
    assert socket.closed == 1


def test_zero_trade_run_reports_an_honest_manifest(tmp_path):
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([connect_reply(), subscribe_ack(), STOP])
    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                        max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                                        ack_timeout_seconds=1.0))

    assert written == 0
    assert not output.exists()
    manifest = read_manifest(tmp_path)
    assert manifest["schema_version"] == 2
    assert manifest["protocol"] == "wallex-centrifugo-v2-raw"
    assert manifest["channel"] == CHANNEL
    assert manifest["websocket_url"] == "wss://api.wallex.ir/connection/websocket"
    assert manifest["closed_candles_written_this_run"] == 0
    assert manifest["trade_events_received"] == 0
    assert manifest["malformed_or_unmatched_messages"] == 0
    assert manifest["connection_count"] == 1
    assert manifest["connection_errors"] == 0
    assert manifest["gaps_possible_on_disconnect"] is False
    assert manifest["subscription_status"] == "acknowledged"
    assert manifest["subscription_acknowledged"] is True
    assert manifest["live_trade_received"] is False
    assert manifest["status"] == "stopped"
    assert manifest["started_at_utc"].endswith("Z")
    assert manifest["updated_at_utc"].endswith("Z")


def test_runtime_limit_expires_on_the_real_clock(tmp_path):
    """Guards the production code path: no injected clock, real asyncio deadline."""
    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        BLOCK,
    ])
    written = asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                                        max_runtime_seconds=0.5, reconnect_backoff_seconds=0,
                                        ack_timeout_seconds=5.0))

    assert written == 0
    assert not output.exists()
    manifest = read_manifest(tmp_path)
    assert manifest["status"] == "stopped"
    assert manifest["stop_reason"] == "runtime_limit"
    assert manifest["trade_events_received"] == 1
    assert manifest["connection_errors"] == 0
    assert manifest["discarded_partial_candles"] == 1


def test_manifest_keeps_the_fields_downstream_audit_reads(tmp_path):
    from wallex_agent.data_quality import audit_file

    output = tmp_path / "candles.jsonl"
    socket = FakeWebSocket([
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(socket),
                              max_runtime_seconds=1.0, reconnect_backoff_seconds=0, clock=FakeClock(),
                              ack_timeout_seconds=1.0))

    manifest = read_manifest(tmp_path)
    for key in ("symbol", "interval_seconds", "status", "closed_candles_written_this_run",
                "malformed_or_unmatched_messages", "connection_count", "reconnect_count",
                "connection_errors", "discarded_partial_candles",
                "gaps_possible_on_disconnect", "last_closed_candle_utc"):
        assert key in manifest, key

    audit = audit_file(output, expected_symbol=SYMBOL, expected_interval_seconds=60)
    assert audit["status"] in {"OK", "REVIEW"}
    assert audit["input_rows_valid"] == 1
    assert audit["manifest"]["symbol"] == SYMBOL
    assert audit["manifest"]["closed_candles_written_this_run"] == 1


def _run_session(output, script, clock=None):
    return asyncio.run(record_trades(SYMBOL, 60, output, connector=connector_for(FakeWebSocket(script)),
                                     max_runtime_seconds=1.0, reconnect_backoff_seconds=0,
                                     clock=clock or FakeClock(), ack_timeout_seconds=1.0))


def test_restart_never_duplicates_an_already_written_bucket(tmp_path):
    """A restart appends; a late trade for a closed bucket must not rewrite it."""
    output = tmp_path / "candles.jsonl"
    _run_session(output, [
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    first = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["timestamp"] for row in first] == ["2026-10-23T10:00:00Z"]

    # Restart: a late trade in the already-finalized bucket must be ignored, and the
    # first bucket seen after a restart stays open until a later bucket arrives.
    _run_session(output, [
        connect_reply(), subscribe_ack(),
        publication(price="999", quantity="5", timestamp="2026-10-23T10:00:30Z"),
        publication(price="102", quantity="1", timestamp="2026-10-23T10:02:01Z"),
        publication(price="103", quantity="1", timestamp="2026-10-23T10:03:01Z"),
        STOP,
    ])

    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["timestamp"] for row in rows] == [
        "2026-10-23T10:00:00Z", "2026-10-23T10:02:00Z"]
    # The first candle is untouched by the late duplicate.
    assert rows[0]["open"] == "100" and rows[0]["close"] == "100" and rows[0]["volume"] == "1"

    manifest = read_manifest(tmp_path)
    assert manifest["resumed_from_existing_output"] is True
    assert manifest["previous_last_closed_candle_utc"] == "2026-10-23T10:00:00Z"
    assert manifest["late_or_out_of_order_trades_ignored"] == 1
    assert manifest["closed_candles_written_this_run"] == 1

    # The whole file still passes the downstream gates (this is the regression).
    from wallex_agent.backtest import load_candles
    from wallex_agent.data_quality import audit_file

    load_candles(rows)
    assert audit_file(output, expected_symbol=SYMBOL,
                      expected_interval_seconds=60)["status"] in {"OK", "REVIEW"}
    assert "DUPLICATE_TIMESTAMP" not in {
        issue["code"] for issue in audit_file(output, expected_symbol=SYMBOL)["issues"]}


def test_corrupt_tail_fails_closed_instead_of_appending(tmp_path):
    output = tmp_path / "candles.jsonl"
    output.write_text('{"timestamp":"2026-10-23T10:00:00Z","open":"1","high":"1","low":"1",'
                      '"close":"1","volume":"1","symbol":"BTCTMN"}\n{"timestamp": "2026-',
                      encoding="utf-8")
    calls = []

    def connector(*args, **kwargs):
        calls.append(1)
        raise AssertionError("must not connect when the existing file is damaged")

    original = output.read_bytes()
    with pytest.raises(ValueError, match="cannot be read"):
        asyncio.run(record_trades(SYMBOL, 60, output, connector=connector))
    assert calls == []
    # The damaged file is refused and left byte-for-byte untouched; no manifest is written.
    assert output.read_bytes() == original
    assert not (tmp_path / "candles.jsonl.manifest.json").exists()


def test_empty_existing_file_is_treated_as_a_fresh_run(tmp_path):
    output = tmp_path / "candles.jsonl"
    output.write_text("", encoding="utf-8")
    written = _run_session(output, [
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    assert written == 1
    manifest = read_manifest(tmp_path)
    assert manifest["resumed_from_existing_output"] is False
    assert manifest["previous_last_closed_candle_utc"] is None


def test_watermark_is_read_from_a_large_recording_tail(tmp_path):
    output = tmp_path / "candles.jsonl"
    pad = [json.dumps({"timestamp": f"2026-10-22T{hour:02d}:{minute:02d}:00Z", "open": "1",
                       "high": "1", "low": "1", "close": "1", "volume": "1",
                       "symbol": SYMBOL, "interval_seconds": 60})
           for hour in range(24) for minute in range(60)]
    last = json.dumps({"timestamp": "2026-10-23T09:59:00Z", "open": "1", "high": "1", "low": "1",
                       "close": "1", "volume": "1", "symbol": SYMBOL, "interval_seconds": 60})
    output.write_text("\n".join(pad + [last]) + "\n", encoding="utf-8")
    assert output.stat().st_size > 65536

    written = _run_session(output, [
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T09:59:30Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    assert written == 0
    manifest = read_manifest(tmp_path)
    assert manifest["previous_last_closed_candle_utc"] == "2026-10-23T09:59:00Z"
    assert manifest["late_or_out_of_order_trades_ignored"] == 1


def test_writer_creates_the_manifest_before_any_candle(tmp_path):
    CandleWriter(tmp_path / "candles.jsonl", SYMBOL, 60)
    manifest = read_manifest(tmp_path)
    assert manifest["status"] == "starting"
    assert manifest["closed_candles_written_this_run"] == 0
    assert not (tmp_path / "candles.jsonl").exists()


def test_existing_recording_without_final_newline_is_read_and_appended_safely(tmp_path):
    """A crashed/hand-edited file may lack the trailing newline; do not glue records."""
    output = tmp_path / "candles.jsonl"
    first = json.dumps({"timestamp": "2026-10-23T10:00:00Z", "open": "100", "high": "100",
                        "low": "100", "close": "100", "volume": "1", "symbol": SYMBOL,
                        "interval_seconds": 60, "trade_count": 1})
    output.write_text(first, encoding="utf-8")          # no trailing newline
    assert not output.read_text(encoding="utf-8").endswith("\n")

    written = _run_session(output, [
        connect_reply(), subscribe_ack(),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        publication(price="102", quantity="1", timestamp="2026-10-23T10:02:01Z"),
        STOP,
    ])

    assert written == 1
    lines = output.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        json.loads(line)                                  # every line stays parseable
    assert json.loads(lines[0])["timestamp"] == "2026-10-23T10:00:00Z"
    assert json.loads(lines[1])["timestamp"] == "2026-10-23T10:01:00Z"
    assert read_manifest(tmp_path)["previous_last_closed_candle_utc"] == "2026-10-23T10:00:00Z"


def test_whitespace_only_existing_file_is_treated_as_fresh(tmp_path):
    output = tmp_path / "candles.jsonl"
    output.write_text("\n\n   \n", encoding="utf-8")
    written = _run_session(output, [
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    assert written == 1
    manifest = read_manifest(tmp_path)
    assert manifest["resumed_from_existing_output"] is False
    assert manifest["previous_last_closed_candle_utc"] is None


def test_bucket_older_than_the_watermark_is_ignored_after_restart(tmp_path):
    output = tmp_path / "candles.jsonl"
    _run_session(output, [
        connect_reply(), subscribe_ack(),
        publication(price="100", quantity="1", timestamp="2026-10-23T10:00:01Z"),
        publication(price="101", quantity="1", timestamp="2026-10-23T10:01:01Z"),
        STOP,
    ])
    _run_session(output, [
        connect_reply(), subscribe_ack(),
        publication(price="5", quantity="9", timestamp="2026-10-23T09:59:59Z"),  # older bucket
        publication(price="102", quantity="1", timestamp="2026-10-23T10:02:01Z"),
        publication(price="103", quantity="1", timestamp="2026-10-23T10:03:01Z"),
        STOP,
    ])
    rows = [json.loads(line) for line in output.read_text().splitlines()]
    assert [row["timestamp"] for row in rows] == [
        "2026-10-23T10:00:00Z", "2026-10-23T10:02:00Z"]
    assert rows[0]["volume"] == "1"
    assert read_manifest(tmp_path)["late_or_out_of_order_trades_ignored"] == 1


def test_bucket_boundaries_and_fractional_timestamps():
    exact = datetime(2026, 10, 23, 10, 1, 0, tzinfo=timezone.utc)
    assert CandleAccumulator.from_trade(exact, Decimal("1"), Decimal("1"), 60).start.isoformat() \
        == "2026-10-23T10:01:00+00:00"
    just_before = datetime(2026, 10, 23, 10, 0, 59, 999999, tzinfo=timezone.utc)
    assert CandleAccumulator.from_trade(just_before, Decimal("1"), Decimal("1"), 60).start.isoformat() \
        == "2026-10-23T10:00:00+00:00"
    negative_offset = datetime(2026, 10, 23, 5, 0, 30, tzinfo=timezone(timedelta(hours=-5)))
    assert CandleAccumulator.from_trade(negative_offset, Decimal("1"), Decimal("1"), 60).start.isoformat() \
        == "2026-10-23T10:00:00+00:00"
    # Fractional seconds in the documented ISO timestamp must not shift the bucket.
    parsed = parse_trade_payload({"price": "1", "quantity": "1",
                                  "timestamp": "2026-10-23T10:00:59.999999Z"})
    assert parsed is not None and parsed[0].microsecond == 999999


# --------------------------------------------------------------------------
# CLI validation
# --------------------------------------------------------------------------
@pytest.mark.parametrize("argv", [
    ["--symbol", "btctmn", "--output", "x.jsonl"],
    ["--symbol", "BTC:USDT", "--output", "x.jsonl"],
    ["--symbol", "", "--output", "x.jsonl"],
    ["--symbol", "BTCTMN", "--interval-seconds", "0", "--output", "x.jsonl"],
    ["--symbol", "BTCTMN", "--interval-seconds", "86401", "--output", "x.jsonl"],
    ["--symbol", "BTCTMN", "--max-runtime-seconds", "-1", "--output", "x.jsonl"],
    ["--symbol", "BTCTMN", "--max-reconnect-attempts", "-1", "--output", "x.jsonl"],
    ["--symbol", "BTCTMN", "--reconnect-backoff-seconds", "-1", "--output", "x.jsonl"],
])
def test_cli_rejects_invalid_parameters(argv, capsys):
    from wallex_agent.candle_recorder import main

    assert main(argv) == 2
    assert "error:" in capsys.readouterr().err


def test_cli_help_documents_the_supported_symbol_example(capsys):
    from wallex_agent.candle_recorder import build_parser

    with pytest.raises(SystemExit) as excinfo:
        build_parser().parse_args(["--help"])
    assert excinfo.value.code == 0
    assert "BTCTMN" in capsys.readouterr().out


def test_invalid_parameters_are_rejected_before_connecting(tmp_path):
    calls = []

    def connector(*args, **kwargs):  # pragma: no cover - must never run
        calls.append(1)
        raise AssertionError("validation must happen before any connection")

    with pytest.raises(ValueError):
        asyncio.run(record_trades("btctmn", 60, tmp_path / "o.jsonl", connector=connector))
    with pytest.raises(ValueError):
        asyncio.run(record_trades(SYMBOL, 0, tmp_path / "o.jsonl", connector=connector))
    with pytest.raises(ValueError):
        asyncio.run(record_trades(SYMBOL, 60, tmp_path / "o.jsonl", connector=connector,
                                  max_runtime_seconds=-1))
    assert calls == []
    assert not (tmp_path / "o.jsonl.manifest.json").exists()
