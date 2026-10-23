"""Offline Wallex vs. CoinGecko reference-price reconciliation.

Roles are deliberately asymmetric: Wallex candles are the exchange-specific
observations used by the paper execution model, while CoinGecko supplies
independent reference / market-context prices only. The two providers'
prices are compared, never averaged or silently substituted for each other.

This module is pure and offline: it performs no network, account, or order
calls. All thresholds (maximum deviation, maximum staleness) and every
symbol/asset mapping are explicit caller inputs; nothing is inferred from
exchange documentation or selected on the caller's behalf.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

from .backtest import BacktestError, Candle


class ReconciliationError(ValueError):
    """Malformed provider input or invalid reconciliation configuration."""


# Quote suffixes recognised when a Wallex symbol has no separator. This is a
# parsing aid for symbol strings the caller already supplied; it is not a
# market-eligibility list and does not assert that any pair exists or trades.
_KNOWN_QUOTES = ("USDT", "USDC", "TMN", "IRT", "USD", "EUR", "BTC", "ETH")
_SEPARATORS = ("_", "-", "/")


def split_symbol(symbol: str) -> tuple[str, str]:
    """Split e.g. BTCUSDT / BTC_USDT / BTC-USDT into (base, quote)."""
    if not isinstance(symbol, str):
        raise ReconciliationError("symbol must be a string")
    cleaned = symbol.strip().upper()
    if not cleaned:
        raise ReconciliationError("symbol must be non-empty")
    for separator in _SEPARATORS:
        if separator in cleaned:
            parts = cleaned.split(separator)
            if len(parts) != 2 or not all(parts):
                raise ReconciliationError(f"cannot parse symbol {symbol!r}")
            return parts[0], parts[1]
    for quote in sorted(_KNOWN_QUOTES, key=len, reverse=True):
        if cleaned.endswith(quote) and len(cleaned) > len(quote):
            return cleaned[: -len(quote)], quote
    raise ReconciliationError(
        f"cannot determine quote currency of symbol {symbol!r}; "
        "supply it explicitly instead of guessing"
    )


def normalize_symbol(symbol: str) -> str:
    base, quote = split_symbol(symbol)
    return f"{base}/{quote}"


def _parse_timestamp(value: Any, field: str) -> datetime:
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            parsed = datetime.fromtimestamp(value, tz=timezone.utc)
        except (OverflowError, OSError, ValueError) as exc:
            raise ReconciliationError(f"{field} is not a valid UNIX time") from exc
    elif isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ReconciliationError(f"{field} must be ISO-8601") from exc
    else:
        raise ReconciliationError(f"{field} must be an ISO-8601 string or UNIX time")
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ReconciliationError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ReconciliationError(f"{field} must be a finite decimal")
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ReconciliationError(f"{field} must be a finite decimal") from exc
    if not parsed.is_finite():
        raise ReconciliationError(f"{field} must be a finite decimal")
    return parsed


def _iso(value: datetime) -> str:
    return value.isoformat().replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class PriceObservation:
    provider: str           # "wallex" | "coingecko"
    asset_id: str           # wallex symbol, or CoinGecko coin id
    base: str
    quote: str
    price: Decimal
    observed_at: datetime   # when the price was known, UTC
    source: str             # provenance label supplied by the caller

    def as_dict(self) -> dict[str, Any]:
        return {
            "provider": self.provider,
            "asset_id": self.asset_id,
            "pair": f"{self.base}/{self.quote}",
            "price": str(self.price),
            "observed_at_utc": _iso(self.observed_at),
            "source": self.source,
        }


def wallex_observations_from_candles(
    rows: Iterable[Mapping[str, Any]],
    *,
    symbol: str,
    interval_seconds: int,
    source: str = "wallex_candle_close",
) -> list[PriceObservation]:
    """Convert candle closes to observations timestamped at bucket close.

    A candle's close is only known when its bucket ends, so each
    observation is stamped ``bucket_start + interval_seconds``. Using the
    bucket start would leak future information into comparisons.
    """
    if isinstance(interval_seconds, bool) or not isinstance(interval_seconds, int) or interval_seconds < 1:
        raise ReconciliationError("interval_seconds must be a positive integer")
    base, quote = split_symbol(symbol)
    observations: list[PriceObservation] = []
    for row in rows:
        try:
            candle = Candle.from_mapping(row)
        except (BacktestError, ValueError, TypeError) as exc:
            raise ReconciliationError(f"invalid Wallex candle row: {exc}") from exc
        row_symbol = row.get("symbol")
        if isinstance(row_symbol, str) and row_symbol.strip():
            try:
                row_base_quote = split_symbol(row_symbol)
            except ReconciliationError:
                row_base_quote = None
            if row_base_quote is not None and row_base_quote != (base, quote):
                raise ReconciliationError("candle row symbol differs from requested symbol")
        start = _parse_timestamp(candle.timestamp, "candle timestamp")
        observations.append(PriceObservation(
            provider="wallex", asset_id=symbol.strip().upper(), base=base, quote=quote,
            price=candle.close, observed_at=start + timedelta(seconds=interval_seconds),
            source=source,
        ))
    observations.sort(key=lambda item: item.observed_at)
    return observations


def coingecko_observations_from_price_payload(
    payload: Mapping[str, Any],
    *,
    base_by_id: Mapping[str, str],
    fetched_at: Any,
    source: str = "coingecko_simple_price",
) -> list[PriceObservation]:
    """Normalize a CoinGecko ``/simple/price`` payload into observations.

    ``base_by_id`` maps CoinGecko coin IDs (e.g. ``bitcoin``) to base-asset
    symbols (e.g. ``BTC``). It is caller-supplied because identically named
    assets on different venues are not assumed to be the same market.
    ``last_updated_at`` (UNIX seconds, when the caller requested it) is the
    observation time; otherwise ``fetched_at`` is used and labelled.
    """
    if not isinstance(payload, Mapping):
        raise ReconciliationError("CoinGecko price payload must be an object")
    fallback_time = _parse_timestamp(fetched_at, "fetched_at")
    observations: list[PriceObservation] = []
    for coin_id, values in payload.items():
        if coin_id not in base_by_id:
            continue
        if not isinstance(values, Mapping):
            raise ReconciliationError(f"CoinGecko payload for {coin_id!r} must be an object")
        updated_raw = values.get("last_updated_at")
        observed_at = (
            _parse_timestamp(updated_raw, "last_updated_at")
            if updated_raw is not None else fallback_time
        )
        for key, value in values.items():
            if key == "last_updated_at" or key.endswith(("_market_cap", "_24h_vol", "_24h_change", "_24hr_change")):
                continue
            price = _decimal(value, f"CoinGecko price for {coin_id!r}")
            if price <= 0:
                raise ReconciliationError(f"CoinGecko price for {coin_id!r} must be positive")
            observations.append(PriceObservation(
                provider="coingecko", asset_id=str(coin_id),
                base=str(base_by_id[coin_id]).strip().upper(), quote=str(key).strip().upper(),
                price=price, observed_at=observed_at, source=source,
            ))
    observations.sort(key=lambda item: item.observed_at)
    return observations


def coingecko_observations_from_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    source: str = "coingecko_reference",
) -> list[PriceObservation]:
    """Normalize JSONL-style rows: coin_id, base, quote, price, timestamp."""
    observations: list[PriceObservation] = []
    for row in rows:
        base_value = row.get("base")
        quote_value = row.get("quote") or row.get("vs_currency")
        if base_value is None and row.get("symbol"):
            base_value, quote_value = split_symbol(str(row["symbol"]))
        if not base_value or not quote_value:
            raise ReconciliationError("CoinGecko row requires base/quote or a parseable symbol")
        price = _decimal(row.get("price"), "CoinGecko price")
        if price <= 0:
            raise ReconciliationError("CoinGecko price must be positive")
        observations.append(PriceObservation(
            provider="coingecko",
            asset_id=str(row.get("coin_id") or row.get("asset_id") or base_value),
            base=str(base_value).strip().upper(), quote=str(quote_value).strip().upper(),
            price=price,
            observed_at=_parse_timestamp(row.get("timestamp") or row.get("observed_at"), "timestamp"),
            source=str(row.get("source") or source),
        ))
    observations.sort(key=lambda item: item.observed_at)
    return observations


def reconcile(
    wallex: list[PriceObservation],
    coingecko: list[PriceObservation],
    *,
    max_deviation_bps: Any,
    max_staleness_seconds: int,
    allow_quote_mismatch: bool = False,
) -> dict[str, Any]:
    """Compare each Wallex observation with the latest prior CoinGecko one.

    Only CoinGecko observations at or before the Wallex observation time
    are eligible (no look-ahead). Quote currencies must match unless the
    caller explicitly allows a mismatch, in which case the comparison is
    flagged rather than treated as equivalent. Prices are never averaged.
    """
    threshold = _decimal(max_deviation_bps, "max_deviation_bps")
    if threshold < 0:
        raise ReconciliationError("max_deviation_bps cannot be negative")
    if isinstance(max_staleness_seconds, bool) or not isinstance(max_staleness_seconds, int) or max_staleness_seconds < 0:
        raise ReconciliationError("max_staleness_seconds must be a non-negative integer")

    comparisons: list[dict[str, Any]] = []
    counts: dict[str, int] = {}
    for wallex_obs in sorted(wallex, key=lambda item: item.observed_at):
        same_base = [obs for obs in coingecko if obs.base == wallex_obs.base]
        comparable = [obs for obs in same_base if obs.quote == wallex_obs.quote]
        quote_mismatch = False
        pool = comparable
        if not comparable and same_base and allow_quote_mismatch:
            pool = same_base
            quote_mismatch = True
        prior = [obs for obs in pool if obs.observed_at <= wallex_obs.observed_at]
        reference = prior[-1] if prior else None

        record: dict[str, Any] = {
            "wallex": wallex_obs.as_dict(),
            "coingecko": reference.as_dict() if reference else None,
            "reference_age_seconds": None,
            "deviation_bps": None,
            "quote_mismatch_allowed_by_caller": quote_mismatch and reference is not None,
        }
        if same_base and not comparable and not allow_quote_mismatch:
            record["status"] = "INCOMPARABLE_QUOTE"
            record["coingecko_quotes_seen"] = sorted({obs.quote for obs in same_base})
            record["fallback"] = "wallex_only; coingecko quote currency is not comparable and was not converted"
        elif reference is None:
            record["status"] = "MISSING_REFERENCE"
            record["fallback"] = "wallex_only; no coingecko observation at or before the wallex time"
        else:
            age = int((wallex_obs.observed_at - reference.observed_at).total_seconds())
            deviation = abs(wallex_obs.price - reference.price) / reference.price * Decimal("10000")
            record["reference_age_seconds"] = age
            record["deviation_bps"] = str(deviation)
            if age > max_staleness_seconds:
                record["status"] = "STALE_REFERENCE"
                record["fallback"] = "wallex_only; coingecko reference exceeds caller staleness limit"
            elif deviation > threshold:
                record["status"] = "MATERIAL_DEVIATION"
                record["fallback"] = "flagged for operator review; neither price was adjusted"
            else:
                record["status"] = "OK"
                record["fallback"] = "none"
        counts[record["status"]] = counts.get(record["status"], 0) + 1
        comparisons.append(record)

    def span(items: list[PriceObservation]) -> dict[str, Any]:
        if not items:
            return {"count": 0, "first_observed_at_utc": None, "last_observed_at_utc": None, "sources": []}
        ordered = sorted(items, key=lambda item: item.observed_at)
        return {
            "count": len(ordered),
            "first_observed_at_utc": _iso(ordered[0].observed_at),
            "last_observed_at_utc": _iso(ordered[-1].observed_at),
            "sources": sorted({item.source for item in ordered}),
        }

    return {
        "schema_version": 1,
        "mode": "offline_provider_reconciliation",
        "status": "OK" if comparisons and counts == {"OK": len(comparisons)} else "REVIEW",
        "provider_roles": {
            "wallex": "exchange-specific candles/prices used by the paper execution model",
            "coingecko": "independent reference / market-context prices only; never an execution price",
        },
        "inputs": {"wallex": span(wallex), "coingecko": span(coingecko)},
        "policy": {
            "max_deviation_bps": str(threshold),
            "max_staleness_seconds": max_staleness_seconds,
            "allow_quote_mismatch": allow_quote_mismatch,
            "look_ahead_prevention": "only coingecko observations at or before the wallex candle-close time are eligible",
            "on_missing_or_stale_reference": "proceed wallex-only and flag; never substitute, convert, or average prices",
        },
        "comparisons": comparisons,
        "summary": {"comparisons": len(comparisons), "by_status": counts},
        "live_trading_enabled": False,
        "order_submission_attempted": False,
        "caveats": [
            "offline comparison of supplied observations; no network calls were made by this function",
            "a small deviation does not prove either price is executable or that the feeds are complete",
            "identically named assets on different venues are not assumed to be the same market; mappings are caller-supplied",
            "synthetic or cached inputs must keep their provenance labels and are never fresh live data",
        ],
    }
