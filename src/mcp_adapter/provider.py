# Smart98 Wallex MCP provider -- concrete implementation of MarketDataProvider.

from __future__ import annotations

import datetime
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, List, Optional, Tuple, cast

from . import (
    Candle,
    DataSource,
    Eligibility,
    EligibilityResult,
    InvalidDataError,
    MCPError,
    MCPTimeout,
    MarketDataProvider,
    MarketMeta,
    OrderBook,
    OrderBookLevel,
    PublicTrade,
    StaleDataError,
    Ticker,
)

logger = logging.getLogger(__name__)


TOOL_MARKETS = "wallex_basic_get_markets"
TOOL_SPOT_MARKETS = "wallex_spot_get_markets"
TOOL_CANDLES = "wallex_basic_candle_history"
TOOL_DEPTH = "wallex_basic_get_market_depth"
TOOL_TRADES = "wallex_basic_get_latest_trades"
TOOL_OTC_MARKETS = "wallex_otc_get_otcmarkets"
TOOL_SPOT_DEPTH = "wallex_spot_get_depth"
TOOL_MARGIN_MARKETS = "wallex_margin_get_markets"

INTERVAL_MAP: Dict[str, str] = {
    "1": "1m", "5": "5m", "15": "15m", "30": "30m",
    "60": "1h", "240": "4h", "720": "12h",
    "D": "1d", "W": "1w", "M": "1M",
}

INTERVAL_REVERSE: Dict[str, str] = {v: k for k, v in INTERVAL_MAP.items()}

MAX_TICKER_AGE_SECONDS = 60
MAX_ORDERBOOK_AGE_SECONDS = 30
MAX_CANDLE_AGE_SECONDS = 300

_mcp_invoke: Optional[Callable] = None


def set_mcp_invoker(invoker: Callable) -> None:
    global _mcp_invoke
    _mcp_invoke = invoker


def _call_mcp(tool: str, params: Optional[Dict[str, Any]] = None) -> Any:
    if _mcp_invoke is not None:
        return _mcp_invoke(tool, params or {})
    raise RuntimeError(
        f"MCP invoker not set. Environment must call set_mcp_invoker or "
        f"provide direct MCP tool access for: {tool}"
    )


def _safe_decimal(value: Any) -> Decimal:
    if isinstance(value, Decimal):
        return value
    try:
        return Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InvalidDataError(f"Cannot convert to Decimal: {value!r}") from exc


def _parse_timestamp(ts: int) -> datetime.datetime:
    return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)


def _parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    if ts_str.endswith("Z"):
        ts_str = ts_str[:-1] + "+00:00"
    return datetime.datetime.fromisoformat(ts_str)


def parse_market_meta(raw: Dict[str, Any]) -> MarketMeta:
    min_notional_raw = raw.get("otc_min_notional")
    min_notional: Optional[Decimal] = None
    if min_notional_raw is not None:
        try:
            min_notional = _safe_decimal(min_notional_raw)
        except InvalidDataError:
            min_notional = None
    flags = raw.get("flags", []) or []
    is_risky = "isRisky" in flags
    return MarketMeta(
        symbol=str(raw["symbol"]),
        base_asset=str(raw["base_asset"]),
        quote_asset=str(raw["quote_asset"]),
        is_spot=bool(raw.get("is_spot", False)),
        amount_precision=int(raw.get("amount_precision", 0)),
        price_precision=int(raw.get("price_precision", 0)),
        min_notional=min_notional,
        is_risky=is_risky,
        is_tmn_based=bool(raw.get("is_tmn_based", False)),
        is_usdt_based=bool(raw.get("is_usdt_based", False)),
        created_at=_parse_iso_timestamp(raw["created_at"]),
        source=DataSource.MCP_SMART98,
    )


def parse_candles(raw: Dict[str, Any], symbol: str, interval: str) -> list[Candle]:
    if raw.get("s") != "ok":
        raise InvalidDataError(f"Candle history returned non-ok status: {raw.get('s')}")

    timestamps = raw.get("t", [])
    opens = raw.get("o", [])
    highs = raw.get("h", [])
    lows = raw.get("l", [])
    closes = raw.get("c", [])
    volumes = raw.get("v", [])

    if not (len(timestamps) == len(opens) == len(highs) == len(lows) == len(closes) == len(volumes)):
        raise InvalidDataError(
            f"Candle arrays have inconsistent lengths: "
            f"t={len(timestamps)} o={len(opens)} h={len(highs)} "
            f"l={len(lows)} c={len(closes)} v={len(volumes)}"
        )

    candles = [
        Candle(
            timestamp=_parse_timestamp(t),
            open=_safe_decimal(o),
            high=_safe_decimal(h),
            low=_safe_decimal(l),
            close=_safe_decimal(c),
            volume=_safe_decimal(v),
            symbol=symbol,
            interval=interval,
            source=DataSource.MCP_SMART98,
        )
        for t, o, h, l, c, v in zip(timestamps, opens, highs, lows, closes, volumes)
    ]

    candles.sort(key=lambda c: c.timestamp)
    return candles


def parse_order_book(raw: Dict[str, Any], symbol: str) -> OrderBook:
    ask_raw = raw.get("ask", [])
    bid_raw = raw.get("bid", [])
    if not isinstance(ask_raw, list) or not isinstance(bid_raw, list):
        raise InvalidDataError("Order book ask/bid must be arrays")

    asks = tuple(
        OrderBookLevel(price=_safe_decimal(level["price"]), quantity=_safe_decimal(level["quantity"]))
        for level in ask_raw
    )
    bids = tuple(
        OrderBookLevel(price=_safe_decimal(level["price"]), quantity=_safe_decimal(level["quantity"]))
        for level in bid_raw
    )
    return OrderBook(symbol=symbol, asks=asks, bids=bids, source=DataSource.MCP_SMART98)


def parse_trades(raw: Dict[str, Any]) -> list[PublicTrade]:
    trades_raw = raw.get("latestTrades", [])
    if not isinstance(trades_raw, list):
        raise InvalidDataError("latestTrades must be an array")

    trades = []
    for t in trades_raw:
        trades.append(
            PublicTrade(
                symbol=str(t["symbol"]),
                price=_safe_decimal(t["price"]),
                quantity=_safe_decimal(t["quantity"]),
                is_buy=bool(t.get("isBuyOrder", False)),
                timestamp=_parse_iso_timestamp(t["timestamp"]),
                source=DataSource.MCP_SMART98,
            )
        )
    return trades


def parse_ticker_from_market(raw: Dict[str, Any]) -> Ticker:
    return Ticker(
        symbol=str(raw["symbol"]),
        bid=_safe_decimal(raw.get("fair_price", {}).get("bid", raw["price"])),
        ask=_safe_decimal(raw.get("fair_price", {}).get("ask", raw["price"])),
        last=_safe_decimal(raw["price"]),
        volume_24h=_safe_decimal(raw.get("volume_24h", 0)),
        change_24h=_safe_decimal(raw.get("change_24h", 0)),
        high_24h=_safe_decimal(raw.get("highest_24h_price", 0)),
        low_24h=_safe_decimal(raw.get("lowest_24h_price", 0)),
        source=DataSource.MCP_SMART98,
    )


def validate_candle_order(candles: list[Candle]) -> list[Candle]:
    if not candles:
        return candles

    sorted_candles = sorted(candles, key=lambda c: c.timestamp)
    interval_seconds = _interval_to_seconds(sorted_candles[0].interval)

    deduped = []
    seen_timestamps: set[datetime.datetime] = set()

    for c in sorted_candles:
        if c.timestamp in seen_timestamps:
            logger.warning(
                "Duplicate candle dropped: %s %s %s",
                c.symbol, c.interval, c.timestamp.isoformat()
            )
            continue
        seen_timestamps.add(c.timestamp)
        deduped.append(c)

    if len(deduped) < 2:
        return deduped

    for i in range(1, len(deduped)):
        delta = (deduped[i].timestamp - deduped[i - 1].timestamp).total_seconds()
        if delta > interval_seconds * 2:
            logger.warning(
                "Gap detected in %s %s: missing %s seconds between %s and %s",
                deduped[i].symbol,
                deduped[i].interval,
                delta - interval_seconds,
                deduped[i - 1].timestamp.isoformat(),
                deduped[i].timestamp.isoformat(),
            )

    return deduped


def _interval_to_seconds(interval: str) -> int:
    mapping = {
        "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
        "1h": 3600, "4h": 14400, "12h": 43200,
        "1d": 86400, "1w": 604800, "1M": 2592000,
    }
    return mapping.get(interval, 3600)


def check_staleness(retrieved_at: datetime.datetime, max_age_seconds: int) -> None:
    age = (datetime.datetime.now(datetime.timezone.utc) - retrieved_at).total_seconds()
    if age > max_age_seconds:
        raise StaleDataError(
            f"Data is {age:.0f}s old, exceeds max age of {max_age_seconds}s"
        )


def check_price_consistency(candle: Candle) -> None:
    if (
        candle.high < candle.low
        or candle.high < candle.open
        or candle.high < candle.close
        or candle.low > candle.open
        or candle.low > candle.close
    ):
        raise InvalidDataError(
            f"OHLC inconsistency in {candle.symbol} @ {candle.timestamp}: "
            f"O={candle.open} H={candle.high} L={candle.low} C={candle.close}"
        )


class MarketEligibilityGate:
    """Fail-closed eligibility gate for competition markets."""

    def __init__(self, competition_rules: Optional[Dict[str, Any]] = None):
        self._competition_rules = competition_rules or {}
        self._allowed: Dict[str, set] = {}
        self._prohibited: Dict[str, str] = {}

    def allow(self, symbol: str, competition: Optional[str] = None) -> None:
        key = symbol.upper()
        self._prohibited.pop(key, None)
        if competition:
            self._allowed.setdefault(key, set()).add(competition)
        else:
            self._allowed.setdefault(key, set())

    def prohibit(self, symbol: str, reason: str = "Explicitly prohibited") -> None:
        self._prohibited[symbol.upper()] = reason
        self._allowed.pop(symbol.upper(), None)

    def evaluate(
        self,
        meta: MarketMeta,
        competition: Optional[str] = None,
        retrieved_at: Optional[datetime.datetime] = None,
    ) -> EligibilityResult:
        symbol = meta.symbol

        if symbol in self._prohibited:
            return EligibilityResult(
                market=symbol,
                eligibility=Eligibility.PROHIBITED,
                reason=self._prohibited[symbol],
            )

        if not meta:
            return EligibilityResult(
                market=symbol,
                eligibility=Eligibility.NO_METADATA,
                reason="No market metadata available",
            )

        if not meta.is_spot:
            return EligibilityResult(
                market=symbol,
                eligibility=Eligibility.NOT_SPOT,
                reason=f"Market {symbol} is not Spot-tradable",
            )

        if competition:
            allowed_competitions = self._allowed.get(symbol)
            if allowed_competitions is None or competition not in allowed_competitions:
                return EligibilityResult(
                    market=symbol,
                    eligibility=Eligibility.UNKNOWN,
                    reason=f"Market {symbol} not explicitly allowed for {competition}",
                )

        if retrieved_at is not None:
            try:
                check_staleness(retrieved_at, MAX_TICKER_AGE_SECONDS)
            except StaleDataError as exc:
                return EligibilityResult(
                    market=symbol,
                    eligibility=Eligibility.STALE,
                    reason=str(exc),
                )

        return EligibilityResult(
            market=symbol,
            eligibility=Eligibility.ELIGIBLE,
            reason="All eligibility checks passed",
        )


class Smart98MCPProvider(MarketDataProvider):
    """Concrete MarketDataProvider backed by the Smart98 Wallex MCP connector."""

    def get_markets(self) -> list[MarketMeta]:
        raw_response = _call_mcp(TOOL_MARKETS)
        result = _get_result(raw_response)
        markets_raw = result.get("markets", [])
        return [parse_market_meta(m) for m in markets_raw]

    def get_candles(
        self,
        symbol: str,
        interval: str,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> list[Candle]:
        resolution = INTERVAL_REVERSE.get(interval)
        if resolution is None:
            raise ValueError(
                f"Unsupported interval: {interval}. "
                f"Supported: {', '.join(INTERVAL_MAP.values())}"
            )
        raw_response = _call_mcp(
            TOOL_CANDLES,
            {
                "symbol": symbol,
                "resolution": resolution,
                "from": int(start.timestamp()),
                "to": int(end.timestamp()),
            },
        )
        candles = parse_candles(raw_response, symbol, interval)
        return validate_candle_order(candles)

    def get_order_book(self, symbol: str) -> OrderBook:
        raw_response = _call_mcp(TOOL_DEPTH, {"symbol": symbol})
        result = _get_result(raw_response)
        ob = parse_order_book(result, symbol)
        check_staleness(ob.retrieved_at, MAX_ORDERBOOK_AGE_SECONDS)
        return ob

    def get_recent_trades(self, symbol: str) -> list[PublicTrade]:
        raw_response = _call_mcp(TOOL_TRADES, {"symbol": symbol})
        result = _get_result(raw_response)
        return parse_trades(result)

    def get_ticker(self, symbol: str) -> Ticker:
        markets = self.get_markets()
        for m in markets:
            if m.symbol == symbol:
                raw_response = _call_mcp(TOOL_MARKETS)
                result = _get_result(raw_response)
                for market_raw in result.get("markets", []):
                    if market_raw["symbol"] == symbol:
                        ticker = parse_ticker_from_market(market_raw)
                        check_staleness(ticker.retrieved_at, MAX_TICKER_AGE_SECONDS)
                        return ticker
        raise ValueError(f"Market not found: {symbol}")


def _get_result(raw: Any) -> dict:
    if not isinstance(raw, dict):
        raise InvalidDataError(f"Unexpected MCP response type: {type(raw)}")
    if not raw.get("success", True):
        msg = raw.get("message", "Unknown MCP error")
        raise MCPError(msg, raw.get("_tool", "unknown"))
    return raw.get("result", raw)
