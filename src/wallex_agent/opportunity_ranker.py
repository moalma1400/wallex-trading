"""Deterministic ranking of already-screened, cost-adjusted shadow candidates."""
from __future__ import annotations

from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping


def _finite_decimal(value: Any) -> Decimal | None:
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        return None
    return number if number.is_finite() else None


def rank_cost_adjusted_opportunities(
    assessments: Iterable[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Rank eligible WATCH_EDGE assessments by net estimated edge, then spread.

    This ranks historical/current observations for research only. It does not
    create a buy/sell instruction, infer missing costs, or submit orders.
    Rows without explicit eligible=True, WATCH_EDGE status, finite net edge,
    and finite non-negative spread are excluded from the candidate list.
    """
    ranked: list[dict[str, Any]] = []
    for row in assessments:
        if row.get("eligible") is not True:
            continue
        cost = row.get("cost_adjusted_momentum")
        if not isinstance(cost, Mapping) or cost.get("status") != "WATCH_EDGE":
            continue
        edge = _finite_decimal(cost.get("net_estimated_edge_bps"))
        spread = _finite_decimal(row.get("spread_bps"))
        symbol = row.get("symbol")
        if edge is None or spread is None or spread < 0 or not isinstance(symbol, str) or not symbol.strip():
            continue
        if edge <= 0:
            continue
        ranked.append({
            "symbol": symbol.strip().upper(),
            "status": "SHADOW_CANDIDATE",
            "net_estimated_edge_bps": str(edge),
            "spread_bps": str(spread),
            "reason": "positive observed net edge after configured cost reserve; research-only",
            "order_submission_attempted": False,
        })
    ranked.sort(key=lambda item: (
        -Decimal(item["net_estimated_edge_bps"]),
        Decimal(item["spread_bps"]),
        item["symbol"],
    ))
    for index, item in enumerate(ranked, start=1):
        item["rank"] = index
    return ranked
