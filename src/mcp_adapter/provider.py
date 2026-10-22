# Smart98 Wallex MCP provider -- concrete implementation of MarketDataProvider.

from __future__ import annotations

import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Dict, Optional

from . import (
    Candle,
    DataSource,
    Eligibility,
    EligibilityResult,
    InvalidDataError,
    MCPError,
    MarketDataProvider,
    MarketMeta,
    OrderBook,
    OrderBookLevel,
    PublicTrade,
    StaleDataError,
    Ticker,
)

TOOL_MARKETS = "wallex_basic_get_markets"
TOOL_CANDLES = "wallex_basic_candle_history"
TOOL_DEPTH = "wallex_basic_get_market_depth"
TOOL_TRADES = "wallex_basic_get_latest_trades"

INTERVAL_MAP: Dict[str, str] = {
    "1": "1m", "5": "5m", "15": "15m", "30": "30m",
    "60": "1h", "240": "4h", "720": "12h",
    "D": "1d", "W": "1w",
}

INTERVAL_REVERSE: Dict[str, str] = {v: k for k, v in INTERVAL_MAP.items()}

_mcp_invoke: Optional[Callable] = None


def set_mcp_invoker(invoker: Callable) -> None:
    if not callable(invoker):
        raise TypeError("MCP invoker must be callable")
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
    if isinstance(value, (bool, float)) or not isinstance(value, (Decimal, int, str)):
        raise InvalidDataError(f"Exact Decimal input required, got {type(value).__name__}")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise InvalidDataError(f"Cannot convert to Decimal: {value!r}") from exc
    if not result.is_finite():
        raise InvalidDataError(f"Non-finite Decimal value: {value!r}")
    return result


def _parse_timestamp(ts: int) -> datetime.datetime:
    if isinstance(ts, bool) or not isinstance(ts, int) or ts < 0:
        raise InvalidDataError("Candle timestamp must be a nonnegative integer Unix timestamp")
    try:
        return datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc)
    except (OverflowError, OSError, ValueError) as exc:
        raise InvalidDataError(f"Invalid Unix timestamp: {ts!r}") from exc


def _require_aware_utc(value: datetime.datetime, label: str) -> datetime.datetime:
    if not isinstance(value, datetime.datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise InvalidDataError(f"{label} must be timezone-aware")
    return value.astimezone(datetime.timezone.utc)


def _parse_iso_timestamp(ts_str: str) -> datetime.datetime:
    if not isinstance(ts_str, str):
        raise InvalidDataError("Timestamp must be an ISO-8601 string")
    normalized = ts_str[:-1] + "+00:00" if ts_str.endswith("Z") else ts_str
    try:
        parsed = datetime.datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise InvalidDataError(f"Invalid ISO-8601 timestamp: {ts_str!r}") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise InvalidDataError("Timestamp must include an explicit timezone")
    return parsed.astimezone(datetime.timezone.utc)


def parse_market_meta(
    raw: Dict[str, Any], *, retrieved_at: datetime.datetime | None = None,
    source_timestamp: datetime.datetime | None = None,
) -> MarketMeta:
    if not isinstance(raw, dict):
        raise InvalidDataError("Market metadata must be an object")
    required_strings = ("symbol", "base_asset", "quote_asset")
    for key in required_strings:
        if not isinstance(raw.get(key), str) or not raw[key].strip():
            raise InvalidDataError(f"Market metadata requires non-empty {key}")

    precisions: dict[str, int] = {}
    for key in ("amount_precision", "price_precision"):
        value = raw.get(key)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise InvalidDataError(f"Market metadata requires a nonnegative integer {key}")
        precisions[key] = value

    spot = raw.get("is_spot")
    if spot is not None and not isinstance(spot, bool):
        raise InvalidDataError("is_spot must be a boolean when supplied")
    market_type_enabled = raw.get("is_market_type_enable")
    if market_type_enabled is not None and not isinstance(market_type_enabled, bool):
        raise InvalidDataError("is_market_type_enable must be a boolean when supplied")

    flags = raw.get("flags", [])
    if not isinstance(flags, list) or any(not isinstance(flag, str) for flag in flags):
        raise InvalidDataError("market flags must be an array of strings")

    min_notional_raw = raw.get("otc_min_notional")
    min_notional = None if min_notional_raw is None else _safe_decimal(min_notional_raw)
    if min_notional is not None and min_notional < 0:
        raise InvalidDataError("otc_min_notional must be nonnegative")
    if retrieved_at is not None:
        retrieved_at = _require_aware_utc(retrieved_at, "market metadata retrieval time")
    if source_timestamp is not None:
        source_timestamp = _require_aware_utc(source_timestamp, "market metadata source timestamp")

    return MarketMeta(
        symbol=raw["symbol"].strip().upper(),
        base_asset=raw["base_asset"].strip().upper(),
        quote_asset=raw["quote_asset"].strip().upper(),
        is_spot=spot,
        amount_precision=precisions["amount_precision"],
        price_precision=precisions["price_precision"],
        otc_min_notional=min_notional,
        is_risky="isRisky" in flags,
        is_tmn_based=raw.get("is_tmn_based") is True,
        is_usdt_based=raw.get("is_usdt_based") is True,
        created_at=_parse_iso_timestamp(raw.get("created_at")),
        source=DataSource.MCP_SMART98,
        market_type_enabled=market_type_enabled,
        retrieved_at=retrieved_at,
        source_timestamp=source_timestamp,
    )


def parse_candles(raw: Dict[str, Any], symbol: str, interval: str) -> list[Candle]:
    if not isinstance(raw, dict):
        raise InvalidDataError("Candle history must be an object")
    if raw.get("s") != "ok":
        raise InvalidDataError(f"Candle history returned non-ok status: {raw.get('s')}")

    arrays = {key: raw.get(key) for key in ("t", "o", "h", "l", "c", "v")}
    if any(not isinstance(values, list) for values in arrays.values()):
        raise InvalidDataError("Candle fields t/o/h/l/c/v must all be arrays")
    timestamps, opens, highs, lows, closes, volumes = (arrays[key] for key in ("t", "o", "h", "l", "c", "v"))
    if not (len(timestamps) == len(opens) == len(highs) == len(lows) == len(closes) == len(volumes)):
        raise InvalidDataError(
            f"Candle arrays have inconsistent lengths: "
            f"t={len(timestamps)} o={len(opens)} h={len(highs)} "
            f"l={len(lows)} c={len(closes)} v={len(volumes)}"
        )
    if not timestamps:
        raise InvalidDataError("Candle history is empty; no market-data decision can be made")
    if not isinstance(symbol, str) or not symbol.strip():
        raise InvalidDataError("Candle symbol must be non-empty")
    _interval_to_seconds(interval)

    candles: list[Candle] = []
    for t, o, h, l, c, v in zip(timestamps, opens, highs, lows, closes, volumes):
        candle = Candle(
            timestamp=_parse_timestamp(t),
            open=_safe_decimal(o),
            high=_safe_decimal(h),
            low=_safe_decimal(l),
            close=_safe_decimal(c),
            volume=_safe_decimal(v),
            symbol=symbol.strip().upper(),
            interval=interval,
            source=DataSource.MCP_SMART98,
        )
        check_price_consistency(candle)
        candles.append(candle)
    return candles


def parse_order_book(
    raw: Dict[str, Any], symbol: str, *, source_timestamp: datetime.datetime | None = None,
) -> OrderBook:
    if not isinstance(raw, dict):
        raise InvalidDataError("Order book must be an object")
    ask_raw = raw.get("ask")
    bid_raw = raw.get("bid")
    if not isinstance(ask_raw, list) or not isinstance(bid_raw, list):
        raise InvalidDataError("Order book ask/bid must be arrays")
    if not ask_raw or not bid_raw:
        raise InvalidDataError("Order book requires non-empty ask and bid sides")

    def parse_side(levels: list[Any], side: str) -> tuple[OrderBookLevel, ...]:
        parsed: list[OrderBookLevel] = []
        for level in levels:
            if not isinstance(level, dict) or "price" not in level or "quantity" not in level:
                raise InvalidDataError(f"Order book {side} levels require price and quantity")
            price = _safe_decimal(level["price"])
            quantity = _safe_decimal(level["quantity"])
            if price <= 0 or quantity <= 0:
                raise InvalidDataError(f"Order book {side} price and quantity must be positive")
            parsed.append(OrderBookLevel(price=price, quantity=quantity))
        return tuple(parsed)

    asks = parse_side(ask_raw, "ask")
    bids = parse_side(bid_raw, "bid")
    if any(asks[i].price > asks[i + 1].price for i in range(len(asks) - 1)):
        raise InvalidDataError("Order book asks must be sorted ascending")
    if any(bids[i].price < bids[i + 1].price for i in range(len(bids) - 1)):
        raise InvalidDataError("Order book bids must be sorted descending")
    if bids[0].price >= asks[0].price:
        raise InvalidDataError("Order book is crossed or locked")
    if source_timestamp is not None:
        source_timestamp = _require_aware_utc(source_timestamp, "order-book source timestamp")
    return OrderBook(
        symbol=symbol.strip().upper(), asks=asks, bids=bids,
        retrieved_at=datetime.datetime.now(datetime.timezone.utc),
        source=DataSource.MCP_SMART98, source_timestamp=source_timestamp,
    )


def parse_trades(raw: Dict[str, Any]) -> list[PublicTrade]:
    trades_raw = raw.get("latestTrades", [])
    if not isinstance(trades_raw, list):
        raise InvalidDataError("latestTrades must be an array")

    trades = []
    for t in trades_raw:
        if not isinstance(t, dict):
            raise InvalidDataError("Each public trade must be an object")
        if not isinstance(t.get("symbol"), str) or not t["symbol"].strip():
            raise InvalidDataError("Public trade requires a non-empty symbol")
        if not isinstance(t.get("isBuyOrder"), bool):
            raise InvalidDataError("Public trade requires an explicit boolean isBuyOrder")
        price = _safe_decimal(t.get("price"))
        quantity = _safe_decimal(t.get("quantity"))
        if price <= 0 or quantity <= 0:
            raise InvalidDataError("Public trade price and quantity must be positive")
        trades.append(
            PublicTrade(
                symbol=t["symbol"].strip().upper(),
                price=price,
                quantity=quantity,
                is_buy=t["isBuyOrder"],
                timestamp=_parse_iso_timestamp(t.get("timestamp")),
                source=DataSource.MCP_SMART98,
            )
        )
    return trades


def parse_ticker_from_market(
    raw: Dict[str, Any], *, retrieved_at: datetime.datetime | None = None,
    source_timestamp: datetime.datetime | None = None,
) -> Ticker:
    if not isinstance(raw, dict) or not isinstance(raw.get("symbol"), str) or not raw["symbol"].strip():
        raise InvalidDataError("Ticker requires a non-empty symbol")
    required = ("price", "volume_24h", "change_24h", "highest_24h_price", "lowest_24h_price")
    missing = [key for key in required if key not in raw or raw[key] is None]
    if missing:
        raise InvalidDataError(f"Ticker missing required market fields: {', '.join(missing)}")
    fair_price = raw.get("fair_price")
    if fair_price is not None and not isinstance(fair_price, dict):
        raise InvalidDataError("fair_price must be an object when supplied")
    bid_raw = fair_price.get("bid") if fair_price else None
    ask_raw = fair_price.get("ask") if fair_price else None
    if fair_price is not None and ((bid_raw is None) != (ask_raw is None)):
        raise InvalidDataError("fair_price must contain both bid and ask or neither")
    bid = _safe_decimal(bid_raw) if bid_raw is not None else None
    ask = _safe_decimal(ask_raw) if ask_raw is not None else None
    last = _safe_decimal(raw["price"])
    volume = _safe_decimal(raw["volume_24h"])
    change = _safe_decimal(raw["change_24h"])
    high = _safe_decimal(raw["highest_24h_price"])
    low = _safe_decimal(raw["lowest_24h_price"])
    if min(last, high, low) <= 0 or volume < 0 or high < low or not low <= last <= high:
        raise InvalidDataError("Ticker values are nonpositive or internally inconsistent")
    if bid is not None and (bid <= 0 or (ask is not None and bid > ask)):
        raise InvalidDataError("Ticker bid/ask are invalid or crossed")
    if ask is not None and ask <= 0:
        raise InvalidDataError("Ticker ask must be positive")
    if retrieved_at is not None:
        retrieved_at = _require_aware_utc(retrieved_at, "ticker retrieval time")
    if source_timestamp is not None:
        source_timestamp = _require_aware_utc(source_timestamp, "ticker source timestamp")
    return Ticker(
        symbol=raw["symbol"].strip().upper(),
        bid=bid,
        ask=ask,
        last=last,
        volume_24h=volume,
        change_24h=change,
        high_24h=high,
        low_24h=low,
        retrieved_at=retrieved_at or datetime.datetime.now(datetime.timezone.utc),
        source=DataSource.MCP_SMART98,
        source_timestamp=source_timestamp,
    )


def validate_candle_order(candles: list[Candle]) -> list[Candle]:
    """Reject malformed sequences; never sort, deduplicate, or silently accept gaps."""
    if not candles:
        raise InvalidDataError("Candle sequence is empty")
    first = candles[0]
    interval_seconds = _interval_to_seconds(first.interval)
    previous = first
    for candle in candles:
        check_price_consistency(candle)
        if candle.symbol != first.symbol or candle.interval != first.interval:
            raise InvalidDataError("Candle sequence mixes symbols or intervals")
    for candle in candles[1:]:
        delta = (candle.timestamp - previous.timestamp).total_seconds()
        if delta <= 0:
            kind = "duplicate" if delta == 0 else "out-of-order"
            raise InvalidDataError(f"Candle sequence contains {kind} timestamps")
        if delta != interval_seconds:
            raise InvalidDataError(
                f"Candle sequence has an incomplete interval gap of {delta:g}s; expected {interval_seconds}s"
            )
        previous = candle
    return candles


def _interval_to_seconds(interval: str) -> int:
    mapping = {
        "1m": 60, "5m": 300, "15m": 900, "30m": 1800,
        "1h": 3600, "4h": 14400, "12h": 43200,
        "1d": 86400, "1w": 604800,
    }
    try:
        return mapping[interval]
    except KeyError as exc:
        raise InvalidDataError(f"Unsupported candle interval: {interval}") from exc


def check_staleness(
    retrieved_at: datetime.datetime,
    max_age_seconds: int,
    *,
    now: datetime.datetime | None = None,
) -> None:
    timestamp = _require_aware_utc(retrieved_at, "retrieved_at")
    current = _require_aware_utc(now or datetime.datetime.now(datetime.timezone.utc), "now")
    if isinstance(max_age_seconds, bool) or not isinstance(max_age_seconds, int) or max_age_seconds < 0:
        raise InvalidDataError("max_age_seconds must be a nonnegative integer")
    age = (current - timestamp).total_seconds()
    if age < 0:
        raise StaleDataError("Data timestamp is in the future")
    if age > max_age_seconds:
        raise StaleDataError(
            f"Data is {age:.0f}s old, exceeds max age of {max_age_seconds}s"
        )


def check_price_consistency(candle: Candle) -> None:
    _require_aware_utc(candle.timestamp, "candle timestamp")
    values = (candle.open, candle.high, candle.low, candle.close, candle.volume)
    if not all(value.is_finite() for value in values):
        raise InvalidDataError(f"Non-finite OHLCV value in {candle.symbol} @ {candle.timestamp}")
    if min(candle.open, candle.high, candle.low, candle.close) <= 0 or candle.volume < 0:
        raise InvalidDataError(f"OHLC must be positive and volume nonnegative in {candle.symbol} @ {candle.timestamp}")
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
    """Fail-closed metadata filter, not a complete challenge/order authorization gate.

    A positive result does not establish challenge enablement, orderability,
    verified precision semantics, account permission, or live authorization.
    """

    def __init__(self, competition_rules: Optional[Dict[str, Any]] = None):
        self._competition_rules = competition_rules or {}
        self._allowed: Dict[str, set[str]] = {}
        self._prohibited: Dict[str, str] = {}

    def allow(self, symbol: str, competition: str) -> None:
        if not isinstance(symbol, str) or not symbol.strip():
            raise ValueError("allowed market symbol must be non-empty")
        if not isinstance(competition, str) or not competition.strip():
            raise ValueError("allow-list entries require an explicit competition")
        key = symbol.strip().upper()
        self._prohibited.pop(key, None)
        self._allowed.setdefault(key, set()).add(competition.strip().casefold())

    def prohibit(self, symbol: str, reason: str = "Explicitly prohibited") -> None:
        key = symbol.strip().upper()
        self._prohibited[key] = reason
        self._allowed.pop(key, None)

    def evaluate(
        self,
        meta: Optional[MarketMeta],
        competition: Optional[str] = None,
        source_timestamp: Optional[datetime.datetime] = None,
        maximum_source_age_seconds: Optional[int] = None,
    ) -> EligibilityResult:
        if meta is None:
            return EligibilityResult(
                market="",
                eligibility=Eligibility.NO_METADATA,
                reason="No market metadata available",
            )
        symbol = meta.symbol.strip().upper()

        if symbol in self._prohibited:
            return EligibilityResult(symbol, Eligibility.PROHIBITED, self._prohibited[symbol])
        if meta.is_risky:
            return EligibilityResult(symbol, Eligibility.PROHIBITED, "Market metadata contains the isRisky flag")
        if meta.is_spot is None:
            return EligibilityResult(symbol, Eligibility.UNKNOWN, "Spot-market status is unknown")
        if meta.is_spot is False:
            return EligibilityResult(symbol, Eligibility.NOT_SPOT, f"Market {symbol} is not Spot-tradable")
        if meta.market_type_enabled is None:
            return EligibilityResult(symbol, Eligibility.UNKNOWN, "Market type enablement is unknown")
        if meta.market_type_enabled is False:
            return EligibilityResult(symbol, Eligibility.INACTIVE, "Market type is disabled")

        allowed_scopes = self._allowed.get(symbol)
        scope = competition.strip().casefold() if isinstance(competition, str) and competition.strip() else None
        if scope is None or allowed_scopes is None or scope not in allowed_scopes:
            return EligibilityResult(
                symbol,
                Eligibility.UNKNOWN,
                f"Market {symbol} is not explicitly allow-listed for {scope or 'an identified competition'}",
            )

        effective_source_timestamp = source_timestamp or meta.source_timestamp
        if effective_source_timestamp is None:
            return EligibilityResult(symbol, Eligibility.UNKNOWN, "Market source timestamp is unknown")
        if maximum_source_age_seconds is None:
            return EligibilityResult(symbol, Eligibility.UNKNOWN, "Maximum source-data age is unconfigured")
        try:
            check_staleness(effective_source_timestamp, maximum_source_age_seconds)
        except StaleDataError as exc:
            return EligibilityResult(symbol, Eligibility.STALE, str(exc))
        except InvalidDataError as exc:
            return EligibilityResult(symbol, Eligibility.UNKNOWN, str(exc))

        return EligibilityResult(
            symbol,
            Eligibility.ELIGIBLE,
            "Adapter metadata filter passed; challenge/order authorization is not established",
        )


class Smart98MCPProvider(MarketDataProvider):
    """Concrete MarketDataProvider backed by the Smart98 Wallex MCP connector."""

    def get_markets(self) -> list[MarketMeta]:
        raw_response = _call_mcp(TOOL_MARKETS)
        result = _get_result(raw_response)
        markets_raw = result.get("markets")
        if not isinstance(markets_raw, list) or not markets_raw:
            raise InvalidDataError("Market metadata response is missing a non-empty markets array")
        retrieved_at = datetime.datetime.now(datetime.timezone.utc)
        return [parse_market_meta(m, retrieved_at=retrieved_at) for m in markets_raw]

    def get_candles(
        self,
        symbol: str,
        interval: str,
        start: datetime.datetime,
        end: datetime.datetime,
    ) -> list[Candle]:
        resolution = INTERVAL_REVERSE.get(interval)
        if resolution is None:
            raise InvalidDataError(
                f"Unsupported interval: {interval}. "
                f"Supported: {', '.join(INTERVAL_MAP.values())}"
            )
        start_utc = _require_aware_utc(start, "candle query start")
        end_utc = _require_aware_utc(end, "candle query end")
        if start_utc >= end_utc:
            raise InvalidDataError("Candle query start must precede end")
        raw_response = _call_mcp(
            TOOL_CANDLES,
            {
                "symbol": symbol,
                "resolution": resolution,
                "from": int(start_utc.timestamp()),
                "to": int(end_utc.timestamp()),
            },
        )
        candles = validate_candle_order(parse_candles(raw_response, symbol, interval))
        if any(c.timestamp < start_utc or c.timestamp > end_utc for c in candles):
            raise InvalidDataError("Candle response contains timestamps outside the requested range")
        return candles

    def get_order_book(self, symbol: str) -> OrderBook:
        raw_response = _call_mcp(TOOL_DEPTH, {"symbol": symbol})
        result = _get_result(raw_response)
        return parse_order_book(result, symbol)

    def get_recent_trades(self, symbol: str) -> list[PublicTrade]:
        raw_response = _call_mcp(TOOL_TRADES, {"symbol": symbol})
        result = _get_result(raw_response)
        trades = parse_trades(result)
        requested = symbol.strip().upper()
        if any(trade.symbol != requested for trade in trades):
            raise InvalidDataError("Trade response contains a different market symbol")
        return trades

    def get_ticker(self, symbol: str) -> Ticker:
        raw_response = _call_mcp(TOOL_MARKETS)
        result = _get_result(raw_response)
        markets_raw = result.get("markets")
        if not isinstance(markets_raw, list):
            raise InvalidDataError("Ticker source does not contain a markets array")
        requested = symbol.strip().upper()
        market_raw = next(
            (market for market in markets_raw if isinstance(market, dict) and market.get("symbol") == requested),
            None,
        )
        if market_raw is None:
            raise InvalidDataError(f"Market not found: {requested}")
        retrieved_at = datetime.datetime.now(datetime.timezone.utc)
        # Local receipt time is not a substitute for source-event time.
        # The downstream eligibility/risk gates must treat absent source time as unknown.
        return parse_ticker_from_market(market_raw, retrieved_at=retrieved_at)


def _get_result(raw: Any) -> dict:
    if not isinstance(raw, dict):
        raise InvalidDataError(f"Unexpected MCP response type: {type(raw)}")
    success = raw.get("success")
    if "success" in raw and not isinstance(success, bool):
        raise InvalidDataError("MCP success marker must be boolean when supplied")
    if success is False:
        msg = raw.get("message", "Unknown MCP error")
        raise MCPError(str(msg), str(raw.get("_tool", "unknown")))
    result = raw.get("result", raw)
    if not isinstance(result, dict):
        raise InvalidDataError(f"Unexpected MCP result type: {type(result)}")
    return result
