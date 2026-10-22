# Unit tests for the Smart98 Wallex MCP adapter.

from __future__ import annotations

import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest

from src.mcp_adapter import (
    Candle,
    DataSource,
    InvalidDataError,
    MarketDataProvider,
    MarketMeta,
    StaleDataError,
)
from src.mcp_adapter.provider import (
    Smart98MCPProvider,
    check_staleness,
    parse_candles,
    parse_market_meta,
    parse_order_book,
    parse_ticker_from_market,
    parse_trades,
    validate_candle_order,
    _get_result,
    MarketEligibilityGate,
    Eligibility,
)
from src.mcp_adapter.eligibility import configure_elcamp_gate
from tests.fixtures.mcp_responses import (
    SAMPLE_CANDLE_RESPONSE,
    SAMPLE_DEPTH_RESPONSE,
    SAMPLE_MARKET_RESPONSE,
    SAMPLE_TRADES_RESPONSE,
)


def exact_ticker_fixture(raw):
    result = raw.copy()
    for key in ("price", "volume_24h", "change_24h", "highest_24h_price", "lowest_24h_price"):
        if key in result:
            result[key] = str(result[key])
    if isinstance(result.get("fair_price"), dict):
        result["fair_price"] = {key: str(value) for key, value in result["fair_price"].items()}
    return result


class TestParseMarketMeta:
    def test_spot_market(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        meta = parse_market_meta(raw)
        assert meta.symbol == "USDTTMN"
        assert meta.base_asset == "USDT"
        assert meta.quote_asset == "TMN"
        assert meta.is_spot is True
        assert meta.amount_precision == 2
        assert meta.price_precision == 0
        assert meta.is_risky is False
        assert meta.is_tmn_based is True
        assert meta.is_usdt_based is False
        assert meta.source == DataSource.MCP_SMART98

    def test_risky_market(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "PUMPTMN"][0]
        meta = parse_market_meta(raw)
        assert meta.is_risky is True
        assert meta.is_spot is True

    def test_btc_precision(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "BTCTMN"][0]
        meta = parse_market_meta(raw)
        assert meta.amount_precision == 8
        assert meta.price_precision == 0

    def test_missing_or_coerced_precision_is_rejected(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0].copy()
        raw.pop("price_precision")
        with pytest.raises(InvalidDataError, match="price_precision"):
            parse_market_meta(raw)
        raw["price_precision"] = True
        with pytest.raises(InvalidDataError, match="price_precision"):
            parse_market_meta(raw)

    def test_boolean_strings_are_not_coerced(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0].copy()
        raw["is_spot"] = "false"
        with pytest.raises(InvalidDataError, match="is_spot"):
            parse_market_meta(raw)

    def test_otc_minimum_is_not_mislabeled_as_spot_minimum(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0].copy()
        raw["otc_min_notional"] = "50000"
        meta = parse_market_meta(raw)
        assert meta.otc_min_notional == Decimal("50000")


class TestParseCandles:
    def test_parse_candles(self):
        candles = parse_candles(SAMPLE_CANDLE_RESPONSE, "USDTTMN", "1h")
        assert len(candles) == 4
        for c in candles:
            assert c.symbol == "USDTTMN"
            assert c.interval == "1h"
            assert c.source == DataSource.MCP_SMART98

    def test_chonological_order(self):
        candles = parse_candles(SAMPLE_CANDLE_RESPONSE, "USDTTMN", "1h")
        for i in range(1, len(candles)):
            assert candles[i].timestamp > candles[i - 1].timestamp

    def test_empty_candles_are_rejected(self):
        empty = {"s": "ok", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
        with pytest.raises(InvalidDataError, match="empty"):
            parse_candles(empty, "USDTTMN", "1h")

    def test_inconsistent_lengths(self):
        bad = {"s": "ok", "t": [1, 2], "o": ["1"], "h": ["1"], "l": ["1"], "c": ["1"], "v": ["1"]}
        with pytest.raises(InvalidDataError, match="inconsistent lengths"):
            parse_candles(bad, "USDTTMN", "1h")

    def test_non_ok_status(self):
        bad = {"s": "error", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
        with pytest.raises(InvalidDataError, match="non-ok status"):
            parse_candles(bad, "USDTTMN", "1h")

    def test_invalid_ohlc_and_nonfinite_values_are_rejected(self):
        bad_ohlc = SAMPLE_CANDLE_RESPONSE.copy()
        bad_ohlc["h"] = ["1", "1", "1", "1"]
        with pytest.raises(InvalidDataError, match="OHLC"):
            parse_candles(bad_ohlc, "USDTTMN", "1h")
        nonfinite = SAMPLE_CANDLE_RESPONSE.copy()
        nonfinite["c"] = ["NaN", "1", "1", "1"]
        with pytest.raises(InvalidDataError, match="Non-finite"):
            parse_candles(nonfinite, "USDTTMN", "1h")


class TestValidateCandleOrder:
    def test_duplicate_candles_are_rejected(self):
        dup = SAMPLE_CANDLE_RESPONSE.copy()
        dup["t"] = [1729440000, 1729443600, 1729443600, 1729450800]
        candles = parse_candles(dup, "USDTTMN", "1h")
        with pytest.raises(InvalidDataError, match="duplicate"):
            validate_candle_order(candles)

    def test_gaps_are_rejected_instead_of_only_logged(self):
        gap = SAMPLE_CANDLE_RESPONSE.copy()
        gap["t"] = [1729440000, 1729443600, 1729454400, 1729458000]
        candles = parse_candles(gap, "USDTTMN", "1h")
        with pytest.raises(InvalidDataError, match="incomplete interval gap"):
            validate_candle_order(candles)

    def test_empty_list_is_rejected(self):
        with pytest.raises(InvalidDataError, match="empty"):
            validate_candle_order([])

    def test_out_of_order_is_rejected_without_sorting(self):
        unsorted = SAMPLE_CANDLE_RESPONSE.copy()
        unsorted["t"] = [1729443600, 1729440000, 1729447200, 1729450800]
        candles = parse_candles(unsorted, "USDTTMN", "1h")
        with pytest.raises(InvalidDataError, match="out-of-order"):
            validate_candle_order(candles)

    def test_preserves_order(self):
        candles = parse_candles(SAMPLE_CANDLE_RESPONSE, "USDTTMN", "1h")
        validated = validate_candle_order(candles)
        assert validated[0].timestamp <= validated[-1].timestamp


class TestParseOrderBook:
    def test_parse_book(self):
        ob = parse_order_book(SAMPLE_DEPTH_RESPONSE, "USDTTMN")
        assert ob.symbol == "USDTTMN"
        assert len(ob.asks) == 3
        assert len(ob.bids) == 3
        assert ob.asks[0].price == Decimal("266655")
        assert ob.asks[0].quantity == Decimal("25.02")
        assert ob.bids[0].price == Decimal("266651")

    def test_non_list_bid_ask(self):
        with pytest.raises(InvalidDataError, match="must be arrays"):
            parse_order_book({"ask": {}, "bid": {}}, "USDTTMN")

    def test_empty_or_crossed_book_is_rejected(self):
        with pytest.raises(InvalidDataError, match="non-empty"):
            parse_order_book({"ask": [], "bid": []}, "USDTTMN")
        crossed = {
            "ask": [dict(SAMPLE_DEPTH_RESPONSE["ask"][0])],
            "bid": [dict(SAMPLE_DEPTH_RESPONSE["bid"][0])],
        }
        crossed["bid"][0]["price"] = "266700"
        with pytest.raises(InvalidDataError, match="crossed or locked"):
            parse_order_book(crossed, "USDTTMN")

    def test_unsorted_book_side_is_rejected(self):
        unsorted = {
            "ask": [dict(level) for level in SAMPLE_DEPTH_RESPONSE["ask"]],
            "bid": [dict(level) for level in SAMPLE_DEPTH_RESPONSE["bid"]],
        }
        unsorted["ask"][0]["price"] = "266900"
        with pytest.raises(InvalidDataError, match="asks must be sorted"):
            parse_order_book(unsorted, "USDTTMN")


class TestParseTrades:
    def test_parse_trades(self):
        trades = parse_trades(SAMPLE_TRADES_RESPONSE)
        assert len(trades) == 3
        for t in trades:
            assert t.symbol == "USDTTMN"
            assert isinstance(t.price, Decimal)
            assert isinstance(t.quantity, Decimal)
            assert isinstance(t.is_buy, bool)

    def test_buy_sell_side(self):
        trades = parse_trades(SAMPLE_TRADES_RESPONSE)
        assert trades[0].is_buy is True
        assert trades[2].is_buy is False

    def test_missing_or_coerced_side_is_rejected(self):
        raw = SAMPLE_TRADES_RESPONSE.copy()
        raw["latestTrades"] = [SAMPLE_TRADES_RESPONSE["latestTrades"][0].copy()]
        raw["latestTrades"][0]["isBuyOrder"] = "false"
        with pytest.raises(InvalidDataError, match="explicit boolean"):
            parse_trades(raw)


class TestTickerFromMarket:
    def test_extract_ticker(self):
        raw = exact_ticker_fixture([m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0])
        ticker = parse_ticker_from_market(raw)
        assert ticker.symbol == "USDTTMN"
        assert isinstance(ticker.bid, Decimal)
        assert isinstance(ticker.last, Decimal)
        assert isinstance(ticker.volume_24h, Decimal)


class TestStaleness:
    def test_fresh_data(self):
        t = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=5)
        check_staleness(t, 60)

    def test_stale_data(self):
        t = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(seconds=120)
        with pytest.raises(StaleDataError, match="exceeds max age"):
            check_staleness(t, 60)

    def test_future_and_naive_timestamps_are_rejected(self):
        future = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(seconds=1)
        with pytest.raises(StaleDataError, match="future"):
            check_staleness(future, 60)
        with pytest.raises(InvalidDataError, match="timezone-aware"):
            check_staleness(datetime.datetime.now(), 60)


class TestEligibilityGate:
    def test_allow_requires_explicit_competition(self):
        gate = MarketEligibilityGate()
        with pytest.raises(ValueError, match="explicit competition"):
            gate.allow("USDTTMN", competition="")

    def test_unknown_by_default(self):
        gate = MarketEligibilityGate()
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        result = gate.evaluate(meta)
        assert result.eligibility == Eligibility.UNKNOWN

    def test_eligible_when_allowed(self):
        gate = MarketEligibilityGate()
        gate.allow("USDTTMN", competition="elcamp")
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        source_timestamp = datetime.datetime.now(datetime.timezone.utc)
        result = gate.evaluate(meta, competition="elcamp", source_timestamp=source_timestamp, maximum_source_age_seconds=60)
        assert result.eligibility == Eligibility.ELIGIBLE
        assert "authorization is not established" in result.reason

    def test_not_spot_blocked(self):
        gate = MarketEligibilityGate()
        meta = MarketMeta(
            symbol="FUTURES",
            base_asset="BTC",
            quote_asset="USDT",
            is_spot=False,
            amount_precision=0,
            price_precision=0,
            otc_min_notional=None,
            is_risky=False,
            is_tmn_based=False,
            is_usdt_based=False,
            created_at=datetime.datetime(2020, 1, 1, tzinfo=datetime.timezone.utc),
        )
        result = gate.evaluate(meta)
        assert result.eligibility == Eligibility.NOT_SPOT

    def test_prohibited_blocked(self):
        gate = MarketEligibilityGate()
        gate.prohibit("USDTTMN", reason="Test prohibition")
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        result = gate.evaluate(meta)
        assert result.eligibility == Eligibility.PROHIBITED

    def test_stale_data_blocked(self):
        gate = MarketEligibilityGate()
        gate.allow("USDTTMN", competition="elcamp")
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        stale_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
        result = gate.evaluate(meta, competition="elcamp", source_timestamp=stale_time, maximum_source_age_seconds=60)
        assert result.eligibility == Eligibility.STALE

    def test_competition_specific_allow(self):
        gate = MarketEligibilityGate()
        gate.allow("USDTTMN", competition="elcamp")
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        source_timestamp = datetime.datetime.now(datetime.timezone.utc)
        result = gate.evaluate(meta, competition="elcamp", source_timestamp=source_timestamp, maximum_source_age_seconds=60)
        assert result.eligibility == Eligibility.ELIGIBLE
        result2 = gate.evaluate(meta, competition="other", source_timestamp=source_timestamp, maximum_source_age_seconds=60)
        assert result2.eligibility == Eligibility.UNKNOWN

    def test_inactive_market_blocked_even_when_allow_listed(self):
        gate = MarketEligibilityGate()
        gate.allow("USDTTMN", competition="elcamp")
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0].copy()
        raw["is_market_type_enable"] = False
        meta = parse_market_meta(raw, retrieved_at=datetime.datetime.now(datetime.timezone.utc))
        result = gate.evaluate(meta, competition="elcamp")
        assert result.eligibility == Eligibility.INACTIVE

    def test_missing_freshness_blocks_even_when_allow_listed(self):
        gate = MarketEligibilityGate()
        gate.allow("USDTTMN", competition="elcamp")
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        meta = parse_market_meta(raw)
        result = gate.evaluate(meta, competition="elcamp")
        assert result.eligibility == Eligibility.UNKNOWN
        assert "source timestamp" in result.reason

    def test_missing_age_policy_blocks_current_source_timestamp(self):
        gate = MarketEligibilityGate()
        gate.allow("USDTTMN", competition="elcamp")
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        result = gate.evaluate(
            meta, competition="elcamp",
            source_timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        assert result.eligibility == Eligibility.UNKNOWN
        assert "unconfigured" in result.reason

    def test_future_metadata_time_is_not_fresh(self):
        gate = MarketEligibilityGate()
        gate.allow("USDTTMN", competition="elcamp")
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        future_time = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=1)
        result = gate.evaluate(meta, competition="elcamp", source_timestamp=future_time, maximum_source_age_seconds=60)
        assert result.eligibility == Eligibility.STALE

    def test_risky_default_prohibited(self):
        gate = configure_elcamp_gate()
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "PUMPTMN"][0]
        )
        result = gate.evaluate(meta)
        assert result.eligibility == Eligibility.PROHIBITED
        assert "isRisky" in result.reason


class TestPrecision:
    def test_high_precision_preserved_without_fabricating_bid_ask(self):
        raw = exact_ticker_fixture([m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "BTCTMN"][0])
        ticker = parse_ticker_from_market(raw)
        assert ticker.last > Decimal("0")
        assert ticker.bid is None
        assert ticker.ask is None
        assert ticker.source_timestamp is None

    def test_float_market_values_are_rejected_as_inexact(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0].copy()
        with pytest.raises(InvalidDataError, match="Exact Decimal input"):
            parse_ticker_from_market(raw)

    def test_partial_fair_price_is_rejected(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0].copy()
        raw["fair_price"] = {"bid": "1"}
        with pytest.raises(InvalidDataError, match="both bid and ask"):
            parse_ticker_from_market(raw)

    def test_prices_as_strings_not_floats(self):
        candles = parse_candles(SAMPLE_CANDLE_RESPONSE, "USDTTMN", "1h")
        for c in candles:
            assert isinstance(c.open, Decimal)


class TestSmart98MCPProvider:
    def test_provider_implements_interface(self):
        provider = Smart98MCPProvider()
        assert isinstance(provider, MarketDataProvider)

    def test_get_markets_integration(self):
        provider = Smart98MCPProvider()
        with patch(
            "src.mcp_adapter.provider._call_mcp",
            return_value=SAMPLE_MARKET_RESPONSE,
        ):
            markets = provider.get_markets()
        assert len(markets) > 0
        assert all(isinstance(m, MarketMeta) for m in markets)
        assert any(m.symbol == "USDTTMN" for m in markets)
        assert all(m.retrieved_at is not None for m in markets)
        assert all(m.source_timestamp is None for m in markets)

    def test_get_candles_integration(self):
        provider = Smart98MCPProvider()
        with patch(
            "src.mcp_adapter.provider._call_mcp",
            return_value=SAMPLE_CANDLE_RESPONSE,
        ):
            candles = provider.get_candles(
                "USDTTMN",
                "1h",
                datetime.datetime(2024, 10, 20, tzinfo=datetime.timezone.utc),
                datetime.datetime(2024, 10, 21, tzinfo=datetime.timezone.utc),
            )
        assert len(candles) == 4
        assert candles[0].symbol == "USDTTMN"

    def test_get_order_book_integration(self):
        provider = Smart98MCPProvider()
        with patch(
            "src.mcp_adapter.provider._call_mcp",
            return_value=SAMPLE_DEPTH_RESPONSE,
        ):
            ob = provider.get_order_book("USDTTMN")
        assert ob.symbol == "USDTTMN"
        assert len(ob.asks) == 3
        assert ob.source_timestamp is None

    def test_get_ticker_uses_one_mcp_call_and_keeps_source_time_unknown(self):
        provider = Smart98MCPProvider()
        response = SAMPLE_MARKET_RESPONSE.copy()
        response["markets"] = [
            exact_ticker_fixture(market) for market in SAMPLE_MARKET_RESPONSE["markets"]
        ]
        with patch(
            "src.mcp_adapter.provider._call_mcp",
            return_value=response,
        ) as invoke:
            ticker = provider.get_ticker("USDTTMN")
        assert ticker.symbol == "USDTTMN"
        assert isinstance(ticker.last, Decimal)
        assert ticker.retrieved_at.tzinfo is not None
        assert ticker.source_timestamp is None
        assert invoke.call_count == 1


class TestMCPResponseValidation:
    def test_success_marker_must_be_boolean(self):
        with pytest.raises(InvalidDataError, match="must be boolean"):
            _get_result({"success": "false", "result": {}})

    def test_nested_result_must_be_object(self):
        with pytest.raises(InvalidDataError, match="result type"):
            _get_result({"success": True, "result": []})

    def test_null_success_marker_is_not_treated_as_success(self):
        with pytest.raises(InvalidDataError, match="must be boolean"):
            _get_result({"success": None, "result": {}})


class TestNoDirectApiBypass:
    def test_provider_no_raw_rest_url(self):
        import inspect
        from src.mcp_adapter import provider as provider_module
        source = inspect.getsource(provider_module)
        assert "api.wallex.ir" not in source, (
            "Provider must not reference Wallex production URLs directly"
        )

    def test_no_order_execution_in_imports(self):
        import src.mcp_adapter as adapter
        assert not any(
            "order" in name.lower() and "post" in name.lower() or "delete" in name.lower()
            for name in dir(adapter)
        )
