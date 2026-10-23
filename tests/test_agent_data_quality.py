import json
from wallex_agent.data_quality import audit_candles

def candle(ts, price="100", symbol="BTCUSDT", interval=60):
    return json.dumps({"timestamp":ts,"open":price,"high":price,"low":price,"close":price,
        "volume":"1","symbol":symbol,"interval_seconds":interval,"trade_count":1})

def test_clean_contiguous_dataset_is_ok():
    rows=[candle("2026-10-23T10:00:00Z"),candle("2026-10-23T10:01:00Z"),candle("2026-10-23T10:02:00Z")]
    report=audit_candles(rows,expected_symbol="BTCUSDT",expected_interval_seconds=60)
    assert report["status"]=="OK"
    assert report["input_rows_valid"]==3
    assert report["potential_gaps"]==0
    assert report["order_submission_attempted"] is False

def test_timestamp_gaps_are_review_not_automatically_invalid():
    rows=[candle("2026-10-23T10:00:00Z"),candle("2026-10-23T10:03:00Z")]
    report=audit_candles(rows,expected_interval_seconds=60)
    assert report["status"]=="REVIEW"
    assert report["potential_gaps"]==1
    assert report["potential_missing_buckets_known"]==2
    assert "no-trade intervals" in report["note"]

def test_duplicate_and_out_of_order_timestamps_are_errors():
    rows=[candle("2026-10-23T10:02:00Z"),candle("2026-10-23T10:02:00Z"),candle("2026-10-23T10:00:00Z")]
    report=audit_candles(rows,expected_interval_seconds=60)
    assert report["status"]=="INVALID"
    assert report["duplicate_timestamps"]==1
    assert report["out_of_order_timestamps"]==1

def test_invalid_json_ohlc_and_expected_symbol_mismatch_are_reported():
    rows=["{bad",candle("2026-10-23T10:00:00Z",price="0"),candle("2026-10-23T10:01:00Z",symbol="ETHUSDT")]
    report=audit_candles(rows,expected_symbol="BTCUSDT",expected_interval_seconds=60)
    assert report["status"]=="INVALID"
    assert report["invalid_records"]==2
    assert any(x["code"]=="SYMBOL_MISMATCH" for x in report["issues"])

def test_manifest_gap_flags_raise_review_even_when_rows_are_contiguous():
    rows=[candle("2026-10-23T10:00:00Z"),candle("2026-10-23T10:01:00Z")]
    report=audit_candles(rows,manifest={"gaps_possible_on_disconnect":True,"connection_errors":1})
    assert report["status"]=="REVIEW"
    assert any(x["code"]=="RECORDER_MANIFEST_REPORTS_CONNECTION_GAPS" for x in report["issues"])

def test_mixed_symbols_and_intervals_are_flagged():
    report=audit_candles([
        candle("2026-10-23T10:00:00Z",symbol="BTCUSDT",interval=60),
        candle("2026-10-23T10:02:00Z",symbol="ETHUSDT",interval=120),
    ])
    assert report["status"]=="INVALID"
    assert any(x["code"]=="MIXED_SYMBOLS" for x in report["issues"])
    assert any(x["code"]=="MIXED_INTERVALS" for x in report["issues"])
