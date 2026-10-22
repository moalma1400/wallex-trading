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

    def test_empty_candles(self):
        empty = {"s": "ok", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
        candles = parse_candles(empty, "USDTTMN", "1h")
        assert candles == []

    def test_inconsistent_lengths(self):
        bad = {"s": "ok", "t": [1, 2], "o": ["1"], "h": ["1"], "l": ["1"], "c": ["1"], "v": ["1"]}
        with pytest.raises(InvalidDataError, match="inconsistent lengths"):
            parse_candles(bad, "USDTTMN", "1h")

    def test_non_ok_status(self):
        bad = {"s": "error", "t": [], "o": [], "h": [], "l": [], "c": [], "v": []}
        with pytest.raises(InvalidDataError, match="non-ok status"):
            parse_candles(bad, "USDTTMN", "1h")


class TestValidateCandleOrder:
    def test_deduplicates(self):
        dup = SAMPLE_CANDLE_RESPONSE.copy()
        dup["t"] = [1, 2, 2, 3]
        dup["o"] = ["10", "20", "20", "30"]
        dup["h"] = ["15", "25", "25", "35"]
        dup["l"] = ["5", "15", "15", "25"]
        dup["c"] = ["12", "22", "22", "32"]
        dup["v"] = ["100", "200", "200", "300"]
        candles = parse_candles(dup, "USDTTMN", "1h")
        validated = validate_candle_order(candles)
        assert len(validated) == 3
        assert validated[0].open == Decimal("10")

    def test_empty_list(self):
        assert validate_candle_order([]) == []

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


class TestTickerFromMarket:
    def test_extract_ticker(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
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


class TestEligibilityGate:
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
        result = gate.evaluate(meta, competition="elcamp")
        assert result.eligibility == Eligibility.ELIGIBLE

    def test_not_spot_blocked(self):
        gate = MarketEligibilityGate()
        meta = MarketMeta(
            symbol="FUTURES",
            base_asset="BTC",
            quote_asset="USDT",
            is_spot=False,
            amount_precision=0,
            price_precision=0,
            min_notional=None,
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
        gate.allow("USDTTMN")
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        stale_time = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=5)
        result = gate.evaluate(meta, retrieved_at=stale_time)
        assert result.eligibility == Eligibility.STALE

    def test_competition_specific_allow(self):
        gate = MarketEligibilityGate()
        gate.allow("USDTTMN", competition="elcamp")
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "USDTTMN"][0]
        )
        result = gate.evaluate(meta, competition="elcamp")
        assert result.eligibility == Eligibility.ELIGIBLE
        result2 = gate.evaluate(meta, competition="other")
        assert result2.eligibility == Eligibility.UNKNOWN

    def test_risky_default_prohibited(self):
        gate = configure_elcamp_gate()
        meta = parse_market_meta(
            [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "PUMPTMN"][0]
        )
        result = gate.evaluate(meta)
        assert result.eligibility == Eligibility.PROHIBITED
        assert "isRisky" in result.reason


class TestPrecision:
    def test_high_precision_preserved(self):
        raw = [m for m in SAMPLE_MARKET_RESPONSE["markets"] if m["symbol"] == "BTCTMN"][0]
        ticker = parse_ticker_from_market(raw)
        assert ticker.last > Decimal("0")

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

    def test_get_ticker_integration(self):
        provider = Smart98MCPProvider()
        with patch(
            "src.mcp_adapter.provider._call_mcp",
            return_value=SAMPLE_MARKET_RESPONSE,
        ):
            ticker = provider.get_ticker("USDTTMN")
        assert ticker.symbol == "USDTTMN"
        assert isinstance(ticker.last, Decimal)


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
