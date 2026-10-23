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
