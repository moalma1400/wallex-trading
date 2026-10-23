import json
from datetime import datetime, timezone
from decimal import Decimal
from wallex_agent.candle_recorder import CandleAccumulator, parse_trade_message

def message(symbol, price, qty, stamp):
    return json.dumps([f"{symbol}@trade", {"price":price,"quantity":qty,"timestamp":stamp}])

def test_parses_documented_trade_message_and_normalizes_utc():
    parsed=parse_trade_message(message("BTCUSDT","100.25","0.5","2026-10-23T10:00:01+02:00"),"BTCUSDT")
    assert parsed is not None
    stamp, price, qty=parsed
    assert stamp == datetime(2026,10,23,8,0,1,tzinfo=timezone.utc)
    assert price==Decimal("100.25") and qty==Decimal("0.5")

def test_rejects_invalid_wrong_symbol_naive_or_nonpositive_trade():
    assert parse_trade_message("{bad","BTCUSDT") is None
    assert parse_trade_message(message("ETHUSDT","1","1","2026-10-23T10:00:00Z"),"BTCUSDT") is None
    assert parse_trade_message(message("BTCUSDT","NaN","1","2026-10-23T10:00:00Z"),"BTCUSDT") is None
    assert parse_trade_message(message("BTCUSDT","1","0","2026-10-23T10:00:00Z"),"BTCUSDT") is None
    assert parse_trade_message(message("BTCUSDT","1","1","2026-10-23T10:00:00"),"BTCUSDT") is None

def test_aggregates_open_high_low_close_volume_and_count():
    first=CandleAccumulator.from_trade(datetime(2026,10,23,10,0,1,tzinfo=timezone.utc),Decimal("100"),Decimal("2"),60)
    first.add(Decimal("103"),Decimal("1.5"))
    first.add(Decimal("99"),Decimal("3"))
    first.add(Decimal("101"),Decimal("0.5"))
    result=first.as_dict("BTCUSDT")
    assert result["timestamp"]=="2026-10-23T10:00:00Z"
    assert result["open"]=="100" and result["high"]=="103" and result["low"]=="99" and result["close"]=="101"
    assert result["volume"]=="7.0" and result["trade_count"]==4

def test_out_of_order_and_incomplete_candle_contract_is_documented():
    # Candle writer is intentionally called only when the next bucket begins.
    candle=CandleAccumulator.from_trade(datetime(2026,10,23,10,0,1,tzinfo=timezone.utc),Decimal("100"),Decimal("1"),60)
    assert candle.start.second==0
    assert candle.as_dict("BTCUSDT")["source"]=="wallex_public_trade_websocket"


def test_application_ping_recognition_is_separate_from_trade_parsing():
    from wallex_agent.candle_recorder import is_application_ping
    assert is_application_ping("PING")
    assert is_application_ping(b" PING ")
    assert is_application_ping(json.dumps(["PING"]))
    assert not is_application_ping(message("BTCUSDT", "100", "1", "2026-10-23T10:00:00Z"))


def test_recorder_replies_to_ping_and_marks_gap_after_disconnect(tmp_path):
    import asyncio
    from pathlib import Path
    from wallex_agent.candle_recorder import record_trades

    class FakeWebSocket:
        def __init__(self, messages):
            self.messages = list(messages)
            self.sent = []
        async def __aenter__(self):
            return self
        async def __aexit__(self, *args):
            return False
        async def send(self, value):
            self.sent.append(value)
        async def recv(self):
            if not self.messages:
                raise OSError("synthetic disconnect")
            item = self.messages.pop(0)
            if isinstance(item, Exception):
                raise item
            return item

    first = FakeWebSocket([
        json.dumps({
            "id": 1,
            "connect": {
                "client": "fake-client",
                "version": "fake",
                "ping": 25,
                "pong": True,
            },
        }),
        "PING",
        json.dumps({
            "id": 2,
            "subscribe": {},
        }),
        message("BTCUSDT", "100", "2", "2026-10-23T10:00:01Z"),
        message("BTCUSDT", "101", "1", "2026-10-23T10:01:01Z"),
        OSError("synthetic disconnect"),
    ])
    calls = []
    def connector(*args, **kwargs):
        calls.append((args, kwargs))
        return first

    output = tmp_path / "candles.jsonl"
    try:
        asyncio.run(record_trades("BTCUSDT", 60, output, connector=connector,
            reconnect_backoff_seconds=0, max_reconnect_attempts=0))
        assert False, "reconnect limit should fail closed after the first disconnect"
    except RuntimeError as exc:
        assert "reconnect limit exceeded" in str(exc)

    assert any(value == "PONG" for value in first.sent)
    assert json.loads(output.read_text().splitlines()[0])["timestamp"] == "2026-10-23T10:00:00Z"
    manifest = json.loads((tmp_path / "candles.jsonl.manifest.json").read_text())
    assert manifest["application_pongs_sent"] == 1
    assert manifest["connection_errors"] == 1
    assert manifest["gaps_possible_on_disconnect"] is True
    assert manifest["discarded_partial_candles"] == 1
    assert manifest["status"] == "stopped"


def test_reconnect_limit_counts_repeated_short_lived_connect_failures(tmp_path):
    import asyncio
    from wallex_agent.candle_recorder import record_trades

    calls = []
    class FailedConnection:
        async def __aenter__(self):
            raise OSError("synthetic connect failure")
        async def __aexit__(self, *args):
            return False
    def connector(*args, **kwargs):
        calls.append(1)
        return FailedConnection()

    output = tmp_path / "connect-fail.jsonl"
    try:
        asyncio.run(record_trades("BTCUSDT", 60, output, connector=connector,
            reconnect_backoff_seconds=0, max_reconnect_attempts=2))
        assert False, "reconnect limit must stop repeated connection failures"
    except RuntimeError as exc:
        assert "reconnect limit exceeded" in str(exc)
    assert len(calls) == 3
    manifest = json.loads((tmp_path / "connect-fail.jsonl.manifest.json").read_text())
    assert manifest["connection_errors"] == 3
    assert manifest["connection_count"] == 0
    assert manifest["gaps_possible_on_disconnect"] is True


def test_subscription_error_fails_closed(tmp_path):
    import asyncio
    from wallex_agent.candle_recorder import record_trades

    class FakeWebSocket:
        def __init__(self):
            self.messages = [
                json.dumps({
                    "id": 1,
                    "connect": {
                        "client": "fake-client",
                        "version": "fake",
                        "ping": 25,
                        "pong": True,
                    },
                }),
                json.dumps({
                    "id": 2,
                    "error": {
                        "code": 103,
                        "message": "synthetic subscription failure",
                    },
                }),
            ]
            self.sent = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def send(self, value):
            self.sent.append(value)

        async def recv(self):
            if not self.messages:
                raise OSError("unexpected receive after subscription error")
            return self.messages.pop(0)

    websocket = FakeWebSocket()

    def connector(*args, **kwargs):
        return websocket

    output = tmp_path / "subscription-error.jsonl"

    try:
        asyncio.run(record_trades(
            "BTCUSDT",
            60,
            output,
            connector=connector,
            reconnect_backoff_seconds=0,
            max_reconnect_attempts=0,
        ))
        assert False, "subscription failure must not be treated as success"
    except RuntimeError as exc:
        assert "reconnect limit exceeded" in str(exc)

    commands = [
        json.loads(value)
        for value in websocket.sent
        if isinstance(value, str) and value.startswith("{")
    ]
    assert any(
        command.get("subscribe", {}).get("channel") == "public:BTCUSDT@trade"
        for command in commands
    )
    manifest = json.loads(
        (tmp_path / "subscription-error.jsonl.manifest.json").read_text()
    )
    assert manifest["connection_errors"] == 1
    assert manifest["status"] == "stopped"


def test_subscription_ack_timeout_fails_closed(tmp_path):
    import asyncio
    from wallex_agent.candle_recorder import record_trades

    class FakeWebSocket:
        def __init__(self):
            self.messages = [
                json.dumps({
                    "id": 1,
                    "connect": {
                        "client": "fake-client",
                        "version": "fake",
                        "ping": 25,
                        "pong": True,
                    },
                }),
            ]
            self.sent = []

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            return False

        async def send(self, value):
            self.sent.append(value)

        async def recv(self):
            if self.messages:
                return self.messages.pop(0)
            raise asyncio.TimeoutError()

    websocket = FakeWebSocket()

    def connector(*args, **kwargs):
        return websocket

    output = tmp_path / "subscription-timeout.jsonl"

    try:
        asyncio.run(record_trades(
            "BTCUSDT",
            60,
            output,
            connector=connector,
            reconnect_backoff_seconds=0,
            max_reconnect_attempts=0,
        ))
        assert False, "missing subscription acknowledgement must fail closed"
    except RuntimeError as exc:
        assert "reconnect limit exceeded" in str(exc)

    manifest = json.loads(
        (tmp_path / "subscription-timeout.jsonl.manifest.json").read_text()
    )
    assert manifest["connection_errors"] == 1
    assert manifest["status"] == "stopped"
    assert manifest["last_connection_error_type"] == "TimeoutError"
