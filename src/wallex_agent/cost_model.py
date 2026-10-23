"""Cost-adjusted short-window momentum assessment; emits no order intents."""
from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any

class CostModelError(ValueError):
    """Invalid or ungrounded cost-model input."""

def dec(value: Any, name: str) -> Decimal:
    if isinstance(value, bool):
        raise CostModelError(f"{name} must be a finite decimal")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise CostModelError(f"{name} must be a finite decimal") from exc
    if not result.is_finite():
        raise CostModelError(f"{name} must be a finite decimal")
    return result

@dataclass(frozen=True, slots=True)
class CostModelConfig:
    """Explicit operator/account inputs; there are no invented fee defaults."""
    fee_bps_per_side: Decimal
    slippage_bps_per_side: Decimal
    minimum_net_edge_bps: Decimal = Decimal("0")
    maximum_observation_gap_seconds: int = 180

    def __post_init__(self) -> None:
        for name in ("fee_bps_per_side", "slippage_bps_per_side", "minimum_net_edge_bps"):
            value = dec(getattr(self, name), name)
            if value < 0 or value > Decimal("10000"):
                raise CostModelError(f"{name} must be between 0 and 10000 basis points")
            object.__setattr__(self, name, value)
        if isinstance(self.maximum_observation_gap_seconds, bool) or not isinstance(self.maximum_observation_gap_seconds, int) or self.maximum_observation_gap_seconds < 1:
            raise CostModelError("maximum_observation_gap_seconds must be a positive integer")

def evaluate_momentum(*, previous_price: Any, current_price: Any, bid: Any, ask: Any,
                      elapsed_seconds: int, config: CostModelConfig) -> dict[str, Any]:
    """Assess observed upward price movement minus an explicit round-trip cost reserve.

    Cost reserve = observed full quoted spread + two-sided fee reserve + two-sided
    slippage reserve. This is a shadow research signal only; it does not predict
    future returns or account for queue position/depth or actual fill prices.
    """
    try:
        previous, current = dec(previous_price, "previous_price"), dec(current_price, "current_price")
        bid_value, ask_value = dec(bid, "bid"), dec(ask, "ask")
    except CostModelError as exc:
        return {"status": "INVALID_DATA", "reason": str(exc)}
    if elapsed_seconds <= 0:
        return {"status": "INVALID_TIME", "reason": "observations must have positive elapsed time"}
    if elapsed_seconds > config.maximum_observation_gap_seconds:
        return {"status": "STALE_BASELINE", "reason": "previous observation is older than configured window"}
    if min(previous, current, bid_value, ask_value) <= 0 or ask_value < bid_value:
        return {"status": "INVALID_DATA", "reason": "prices must be positive and ask must be >= bid"}
    gross = (current - previous) / previous * Decimal("10000")
    midpoint = (ask_value + bid_value) / Decimal("2")
    spread = (ask_value - bid_value) / midpoint * Decimal("10000")
    fees = config.fee_bps_per_side * 2
    slippage = config.slippage_bps_per_side * 2
    total = spread + fees + slippage
    net = gross - total
    if gross <= 0:
        status = "NON_POSITIVE_MOMENTUM"
    elif net <= config.minimum_net_edge_bps:
        status = "NET_EDGE_BELOW_COST"
    else:
        status = "WATCH_EDGE"
    return {
        "status": status,
        "gross_change_bps": str(gross.quantize(Decimal("0.01"))),
        "spread_cost_bps": str(spread.quantize(Decimal("0.01"))),
        "round_trip_fee_reserve_bps": str(fees.quantize(Decimal("0.01"))),
        "round_trip_slippage_reserve_bps": str(slippage.quantize(Decimal("0.01"))),
        "total_estimated_cost_bps": str(total.quantize(Decimal("0.01"))),
        "net_estimated_edge_bps": str(net.quantize(Decimal("0.01"))),
        "elapsed_seconds": elapsed_seconds,
        "order_submission_attempted": False,
    }
