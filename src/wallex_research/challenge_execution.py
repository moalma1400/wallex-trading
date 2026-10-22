"""Mode isolation for the challenge: intent recording only, never order submission."""
from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Callable


class ChallengeExecutionError(ValueError):
    """An unsupported execution mode was requested."""


class ExecutionMode(StrEnum):
    BACKTEST = "backtest"
    SHADOW = "shadow"
    DRY_RUN = "dry_run"
    LIVE = "live"


@dataclass(frozen=True, slots=True)
class DispatchResult:
    intent_id: str
    mode: ExecutionMode
    submitted: bool
    status: str
    reason_code: str

    def as_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "mode": self.mode.value,
            "submitted": self.submitted,
            "status": self.status,
            "reason_code": self.reason_code,
        }


def dispatch_order_intent(
    intent_id: str,
    mode: ExecutionMode | str,
    *,
    live_trading_enabled_by_default: bool = False,
    submit_order: Callable[..., Any] | None = None,
) -> DispatchResult:
    """Record-only dispatch for offline modes; LIVE always fails closed.

    `submit_order` exists only as an injection seam for a negative side-effect
    test. It is deliberately never invoked in any mode by this implementation.
    """
    if not isinstance(intent_id, str) or not intent_id.strip():
        raise ChallengeExecutionError("intent_id must be non-empty")
    try:
        selected = mode if isinstance(mode, ExecutionMode) else ExecutionMode(mode)
    except ValueError as exc:
        raise ChallengeExecutionError(f"unsupported execution mode: {mode!r}") from exc
    if live_trading_enabled_by_default is not False:
        raise ChallengeExecutionError("live trading cannot be enabled by this challenge feature")
    if selected is ExecutionMode.LIVE:
        return DispatchResult(intent_id, selected, False, "blocked", "LIVE_EXECUTION_NOT_IMPLEMENTED")
    if submit_order is not None and not callable(submit_order):
        raise ChallengeExecutionError("submit_order test seam must be callable when supplied")
    return DispatchResult(intent_id, selected, False, "recorded_only", "NO_ORDER_ADAPTER_IN_OFFLINE_FEATURE")
