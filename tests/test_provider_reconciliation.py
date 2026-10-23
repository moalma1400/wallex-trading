"""Offline tests for Wallex vs. CoinGecko reference-price reconciliation.

All inputs are synthetic values created in this file or in clearly labeled
synthetic fixtures. No network access occurs.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from wallex_agent.provider_reconciliation import (
    PriceObservation,
    ReconciliationError,
    coingecko_observations_from_price_payload,
    coingecko_observations_from_rows,
    normalize_symbol,
    reconcile,
    split_symbol,
    wallex_observations_from_candles,
)
from wallex_agent.reconciliation_cli import main as reconcile_main

FIXTURES = Path(__file__).parent / "fixtures"
T0 = datetime(2026, 1, 1, 0, 1, tzinfo=timezone.utc)


def obs(provider, base, quote, price, at, source="synthetic_test"):
    from decimal import Decimal
    return PriceObservation(provider, "x", base, quote, Decimal(str(price)), at, source)


@pytest.mark.parametrize(
    "raw,pair",
    [
        ("BTCUSDT", ("BTC", "USDT")),
        ("btc_usdt", ("BTC", "USDT")),
        ("BTC-USDT", ("BTC", "USDT")),
        ("BTC/USDT", ("BTC", "USDT")),
        ("USDTTMN", ("USDT", "TMN")),
    ],
)
def test_split_symbol(raw, pair):
    assert split_symbol(raw) == pair
    assert normalize_symbol(raw) == f"{pair[0]}/{pair[1]}"


@pytest.mark.parametrize("raw", ["", "BTC", "NOTAPAIR", "BTC__USDT", 123])
def test_split_symbol_rejects_unparseable(raw):
    with pytest.raises(ReconciliationError):
        split_symbol(raw)


def candle_row(minute, close):
    return {
        "timestamp": f"2026-01-01T00:{minute:02d}:00Z",
        "open": close, "high": close, "low": close, "close": close,
        "volume": "1", "symbol": "BTCUSDT", "interval_seconds": 60,
    }


def test_wallex_observation_is_timestamped_at_bucket_close():
    observations = wallex_observations_from_candles(
        [candle_row(0, "100")], symbol="BTCUSDT", interval_seconds=60,
    )
    assert observations[0].observed_at == T0  # 00:00 bucket closes at 00:01
    assert (observations[0].base, observations[0].quote) == ("BTC", "USDT")


def test_wallex_row_symbol_mismatch_rejected():
    with pytest.raises(ReconciliationError, match="differs"):
        wallex_observations_from_candles(
            [candle_row(0, "100")], symbol="ETHUSDT", interval_seconds=60,
        )


def run(wallex, coingecko, **kwargs):
    kwargs.setdefault("max_deviation_bps", "100")
    kwargs.setdefault("max_staleness_seconds", 600)
    return reconcile(wallex, coingecko, **kwargs)


def statuses(report):
    return [c["status"] for c in report["comparisons"]]


def test_matching_reference_is_ok():
    report = run([obs("wallex", "BTC", "USDT", "100.05", T0)],
                 [obs("coingecko", "BTC", "USDT", "100", T0)])
    assert report["status"] == "OK"
    assert statuses(report) == ["OK"]
    assert report["live_trading_enabled"] is False


def test_future_reference_is_never_used_look_ahead_prevention():
    from datetime import timedelta
    report = run([obs("wallex", "BTC", "USDT", "100", T0)],
                 [obs("coingecko", "BTC", "USDT", "100", T0 + timedelta(minutes=1))])
    assert statuses(report) == ["MISSING_REFERENCE"]
    assert report["comparisons"][0]["coingecko"] is None


def test_stale_reference_is_flagged_not_used_as_fresh():
    from datetime import timedelta
    report = run([obs("wallex", "BTC", "USDT", "100", T0)],
                 [obs("coingecko", "BTC", "USDT", "100", T0 - timedelta(hours=1))])
    assert statuses(report) == ["STALE_REFERENCE"]
    assert report["comparisons"][0]["reference_age_seconds"] == 3600


def test_material_deviation_is_flagged_with_both_prices_preserved():
    report = run([obs("wallex", "BTC", "USDT", "110", T0)],
                 [obs("coingecko", "BTC", "USDT", "100", T0)])
    assert statuses(report) == ["MATERIAL_DEVIATION"]
    comparison = report["comparisons"][0]
    assert comparison["wallex"]["price"] == "110"
    assert comparison["coingecko"]["price"] == "100"


def test_quote_mismatch_is_incomparable_by_default():
    report = run([obs("wallex", "BTC", "USDT", "100", T0)],
                 [obs("coingecko", "BTC", "USD", "100", T0)])
    assert statuses(report) == ["INCOMPARABLE_QUOTE"]
    assert report["comparisons"][0]["coingecko_quotes_seen"] == ["USD"]


def test_quote_mismatch_compares_only_with_explicit_caller_opt_in():
    report = run([obs("wallex", "BTC", "USDT", "100", T0)],
                 [obs("coingecko", "BTC", "USD", "100", T0)],
                 allow_quote_mismatch=True)
    assert statuses(report) == ["OK"]
    assert report["comparisons"][0]["quote_mismatch_allowed_by_caller"] is True


def test_missing_provider_falls_back_to_wallex_only_and_says_so():
    report = run([obs("wallex", "BTC", "USDT", "100", T0)], [])
    assert statuses(report) == ["MISSING_REFERENCE"]
    assert "wallex_only" in report["comparisons"][0]["fallback"]
    assert report["inputs"]["coingecko"]["count"] == 0


def test_invalid_thresholds_rejected():
    with pytest.raises(ReconciliationError):
        reconcile([], [], max_deviation_bps="-1", max_staleness_seconds=60)
    with pytest.raises(ReconciliationError):
        reconcile([], [], max_deviation_bps="10", max_staleness_seconds=-1)
    with pytest.raises(ReconciliationError):
        reconcile([], [], max_deviation_bps="nan", max_staleness_seconds=60)


def test_price_payload_adapter_uses_last_updated_and_skips_non_price_keys():
    epoch = int(T0.timestamp())
    payload = {"bitcoin": {"usdt": 100.5, "usdt_market_cap": 9, "usdt_24h_change": 1,
                           "last_updated_at": epoch},
               "unknown": {"usdt": 1}}
    observations = coingecko_observations_from_price_payload(
        payload, base_by_id={"bitcoin": "BTC"}, fetched_at="2026-01-02T00:00:00Z",
    )
    assert len(observations) == 1
    assert observations[0].observed_at == T0
    assert observations[0].quote == "USDT"
    assert str(observations[0].price) == "100.5"


@pytest.mark.parametrize("price", [True, "nan", "inf", 0, -5, "x"])
def test_price_payload_adapter_rejects_malformed_prices(price):
    with pytest.raises(ReconciliationError):
        coingecko_observations_from_price_payload(
            {"bitcoin": {"usd": price}}, base_by_id={"bitcoin": "BTC"},
            fetched_at="2026-01-01T00:00:00Z",
        )


def test_rows_adapter_and_naive_timestamp_rejection():
    rows = [{"coin_id": "bitcoin", "base": "BTC", "quote": "USDT", "price": "100",
             "timestamp": "2026-01-01T00:01:00Z"}]
    assert coingecko_observations_from_rows(rows)[0].provider == "coingecko"
    rows[0]["timestamp"] = "2026-01-01T00:01:00"
    with pytest.raises(ReconciliationError, match="timezone"):
        coingecko_observations_from_rows(rows)


def test_synthetic_fixtures_reconcile_ok_under_demonstration_thresholds(tmp_path):
    output = tmp_path / "reconciliation.json"
    rc = reconcile_main([
        "--wallex-candles", str(FIXTURES / "synthetic_20x1m_candles.jsonl"),
        "--symbol", "BTCUSDT", "--interval-seconds", "60",
        "--coingecko-file", str(FIXTURES / "synthetic_coingecko_reference.jsonl"),
        "--max-deviation-bps", "500", "--max-staleness-seconds", "600",
        "--output", str(output),
    ])
    assert rc == 0
    report = json.loads(output.read_text(encoding="utf-8"))
    assert report["status"] == "OK"
    assert report["summary"]["comparisons"] == 20
    sources = report["inputs"]["wallex"]["sources"] + report["inputs"]["coingecko"]["sources"]
    assert sources  # provenance recorded; fixture rows stay labeled in their files


def test_cli_requires_mapping_for_payload_files(tmp_path):
    payload = tmp_path / "price.json"
    payload.write_text(json.dumps({"bitcoin": {"usd": 100, "last_updated_at": 1767225660}}))
    rc = reconcile_main([
        "--wallex-candles", str(FIXTURES / "synthetic_20x1m_candles.jsonl"),
        "--symbol", "BTCUSDT", "--interval-seconds", "60",
        "--coingecko-file", str(payload),
        "--max-deviation-bps", "500", "--max-staleness-seconds", "600",
    ])
    assert rc == 2
