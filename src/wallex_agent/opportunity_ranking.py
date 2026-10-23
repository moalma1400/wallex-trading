"""Deterministic cost-aware ranking of shadow-only market assessments.

This module ranks observations that passed the existing deterministic market
screen and cost model. It never creates order intents and never calls a network.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping


def _finite_decimal(value: Any) -> Decimal | None:
    if isinstance(value, bool) or value is None:
        return None
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return result if result.is_finite() else None


def rank_opportunities(
    assessments: Iterable[Mapping[str, Any]],
    *,
    limit: int = 10,
    minimum_net_edge_bps: Any = "0",
) -> list[dict[str, Any]]:
    """Rank only screen-eligible WATCH_EDGE rows by net edge, then spread.

    "Opportunity" here means a candidate for further shadow evaluation, not a
    forecast, recommendation, executable edge, or order request. Missing or
    malformed costs fail closed. Input order is not used as a tie-breaker;
    symbol provides deterministic final ordering.
    """
    if isinstance(limit, bool) or not isinstance(limit, int) or limit < 1:
        raise ValueError("limit must be a positive integer")
    floor = _finite_decimal(minimum_net_edge_bps)
    if floor is None or floor < 0 or floor > Decimal("10000"):
        raise ValueError("minimum_net_edge_bps must be finite and between 0 and 10000")

    candidates: list[dict[str, Any]] = []
    for row in assessments:
        if not isinstance(row, Mapping) or row.get("eligible") is not True:
            continue
        cost = row.get("cost_adjusted_momentum")
        if not isinstance(cost, Mapping) or cost.get("status") != "WATCH_EDGE":
            continue
        edge = _finite_decimal(cost.get("net_estimated_edge_bps"))
        gross = _finite_decimal(cost.get("gross_change_bps"))
        spread_cost = _finite_decimal(cost.get("spread_cost_bps"))
        fees = _finite_decimal(cost.get("round_trip_fee_reserve_bps"))
        slippage = _finite_decimal(cost.get("round_trip_slippage_reserve_bps"))
        spread = _finite_decimal(row.get("spread_bps"))
        elapsed = cost.get("elapsed_seconds")
        symbol = row.get("symbol")
        if not isinstance(symbol, str) or not symbol.strip():
            continue
        if any(value is None for value in (edge, gross, spread_cost, fees, slippage, spread)):
            continue
        if edge <= floor or spread < 0:
            continue
        if isinstance(elapsed, bool) or not isinstance(elapsed, int) or elapsed < 1:
            continue
        candidates.append({
            "symbol": symbol.strip().upper(),
            "rank_score_net_edge_bps": str(edge.quantize(Decimal("0.01"))),
            "gross_change_bps": str(gross.quantize(Decimal("0.01"))),
            "estimated_spread_cost_bps": str(spread_cost.quantize(Decimal("0.01"))),
            "round_trip_fee_reserve_bps": str(fees.quantize(Decimal("0.01"))),
            "round_trip_slippage_reserve_bps": str(slippage.quantize(Decimal("0.01"))),
            "quoted_spread_bps": str(spread.quantize(Decimal("0.01"))),
            "observation_elapsed_seconds": elapsed,
            "price": row.get("price"),
            "reason": "screen_eligible_positive_cost_adjusted_observed_momentum",
            "mode": "shadow_candidate_only",
            "order_submission_attempted": False,
        })
    candidates.sort(key=lambda item: (
        -Decimal(item["rank_score_net_edge_bps"]),
        Decimal(item["quoted_spread_bps"]),
        item["symbol"],
    ))
    for index, candidate in enumerate(candidates[:limit], start=1):
        candidate["rank"] = index
    return candidates[:limit]
