"""Deterministic, order-free Spot screening. This is not a profitability claim."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

class ScreeningError(ValueError):
    """Invalid screening configuration or market data."""

def _decimal(value: Any, name: str) -> Decimal:
    if isinstance(value, bool) or not isinstance(value, (str, int, float, Decimal)):
        raise ScreeningError(f"{name} must be numeric")
    try:
        value = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ScreeningError(f"{name} must be numeric") from exc
    if not value.is_finite():
        raise ScreeningError(f"{name} must be finite")
    return value

@dataclass(frozen=True, slots=True)
class ScreenConfig:
    quote_asset: str
    minimum_change_24h_raw: Decimal = Decimal("0")
    maximum_spread_bps: Decimal = Decimal("80")
    allowed_symbols: frozenset[str] = frozenset()

    def __post_init__(self) -> None:
        quote = self.quote_asset.strip().upper() if isinstance(self.quote_asset, str) else ""
        if not quote or not quote.isalnum():
            raise ScreeningError("quote_asset must be an explicit alphanumeric asset code")
        object.__setattr__(self, "quote_asset", quote)
        object.__setattr__(self, "minimum_change_24h_raw", _decimal(self.minimum_change_24h_raw, "minimum_change_24h_raw"))
        spread = _decimal(self.maximum_spread_bps, "maximum_spread_bps")
        if spread < 0 or spread > Decimal("10000"):
            raise ScreeningError("maximum_spread_bps must be between 0 and 10000")
        object.__setattr__(self, "maximum_spread_bps", spread)
        symbols = frozenset(s.strip().upper() for s in self.allowed_symbols if isinstance(s, str) and s.strip())
        if any(not s.isalnum() for s in symbols):
            raise ScreeningError("allowed_symbols must contain alphanumeric symbols")
        object.__setattr__(self, "allowed_symbols", symbols)

@dataclass(frozen=True, slots=True)
class MarketAssessment:
    symbol: str
    eligible: bool
    reason_codes: tuple[str, ...]
    price: str | None = None
    change_24h_raw: str | None = None
    spread_bps: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {"symbol": self.symbol, "status": "WATCH" if self.eligible else "SKIP",
                "eligible": self.eligible, "reason_codes": list(self.reason_codes),
                "price": self.price, "change_24h_raw": self.change_24h_raw,
                "spread_bps": self.spread_bps}

def _safe_text(value: Any) -> str | None:
    return str(value) if value is not None and not isinstance(value, (dict, list, bool)) else None

def _assess(market: Mapping[str, Any], config: ScreenConfig) -> MarketAssessment:
    raw_symbol = market.get("symbol", "")
    symbol = raw_symbol.strip().upper() if isinstance(raw_symbol, str) else ""
    if not symbol:
        return MarketAssessment("UNKNOWN", False, ("MISSING_SYMBOL",))
    reasons = []
    if market.get("is_spot") is not True:
        reasons.append("NOT_ACTIVE_SPOT")
    quote = market.get("quote_asset")
    if not isinstance(quote, str) or quote.strip().upper() != config.quote_asset:
        reasons.append("QUOTE_ASSET_MISMATCH")
    if config.allowed_symbols and symbol not in config.allowed_symbols:
        reasons.append("SYMBOL_NOT_ALLOWLISTED")
    fair = market.get("fair_price")
    if not isinstance(fair, Mapping):
        return MarketAssessment(symbol, False, tuple(reasons + ["MISSING_BID_ASK"]),
                                _safe_text(market.get("price")), _safe_text(market.get("change_24h")))
    try:
        bid, ask = _decimal(fair.get("bid"), "fair_price.bid"), _decimal(fair.get("ask"), "fair_price.ask")
        price, change = _decimal(market.get("price"), "price"), _decimal(market.get("change_24h"), "change_24h")
    except ScreeningError:
        return MarketAssessment(symbol, False, tuple(reasons + ["INVALID_NUMERIC_MARKET_DATA"]),
                                _safe_text(market.get("price")), _safe_text(market.get("change_24h")))
    if bid <= 0 or ask <= 0 or price <= 0 or ask < bid:
        return MarketAssessment(symbol, False, tuple(reasons + ["INVALID_BID_ASK_OR_PRICE"]), str(price), str(change))
    spread = (ask - bid) / ((ask + bid) / Decimal("2")) * Decimal("10000")
    if spread > config.maximum_spread_bps:
        reasons.append("SPREAD_ABOVE_SCREENING_LIMIT")
    if change <= config.minimum_change_24h_raw:
        reasons.append("CHANGE_BELOW_SCREENING_THRESHOLD")
    return MarketAssessment(symbol, not reasons, tuple(reasons or ["SCREENING_MATCH_ONLY"]), str(price),
                            str(change), str(spread.quantize(Decimal("0.01"))))

def assess_markets(markets: Iterable[Mapping[str, Any]], config: ScreenConfig) -> list[MarketAssessment]:
    """List WATCH candidates first; no order intent or BUY/SELL advice is produced."""
    results = [_assess(m, config) for m in markets if isinstance(m, Mapping)]
    results.sort(key=lambda x: (not x.eligible,
        -(Decimal(x.change_24h_raw) if x.eligible and x.change_24h_raw else Decimal("-Infinity")),
        Decimal(x.spread_bps) if x.spread_bps is not None else Decimal("Infinity"), x.symbol))
    return results
