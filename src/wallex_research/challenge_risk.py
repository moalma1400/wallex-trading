"""Offline fail-closed order-risk gates for the user-provided challenge brief.

Limits are intentionally unset until the operator/organizer supplies and reviews
them. This module validates intents only and has no order submission capability.
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from decimal import Decimal
from pathlib import Path
from typing import Any

from .challenge import ChallengePolicyError, _decimal, normalize_spot_pair


LIMIT_NAMES = (
    "maximum_order_notional_tmn",
    "maximum_asset_exposure_tmn",
    "maximum_total_deployed_tmn",
    "maximum_open_orders",
    "maximum_orders_per_window",
    "maximum_daily_loss_tmn",
    "maximum_peak_drawdown_percent",
    "maximum_consecutive_losses",
    "maximum_consecutive_errors",
    "maximum_market_data_age_seconds",
    "maximum_ai_signal_age_seconds",
    "maximum_spread_basis_points",
    "maximum_total_cost_basis_points",
    "maximum_slippage_basis_points",
    "maximum_liquidity_utilization_percent",
)


def load_challenge_risk_limits(path: str | Path) -> "ChallengeRiskLimits":
    """Load internal caps; unknown/null values remain unset and therefore veto orders."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ChallengePolicyError(f"cannot read challenge risk configuration: {exc}") from exc
    if not isinstance(data, dict) or data.get("evidence_status") != "PROVIDED_BY_CHALLENGE_BRIEF":
        raise ChallengePolicyError("challenge risk config must retain user-brief provenance")
    values = data.get("risk_limits")
    if not isinstance(values, dict):
        raise ChallengePolicyError("risk_limits must be a mapping")
    if values.get("evidence_status") not in {
        "OFFICIAL_SOURCE_VERIFIED", "INFERRED", "UNRESOLVED", "REQUIRES_ORGANIZER_CONFIRMATION"
    }:
        raise ChallengePolicyError("risk limits require explicit evidence status")
    if values.get("configuration_status") != "REVIEWED_INTERNAL":
        return ChallengeRiskLimits()
    return ChallengeRiskLimits(**{name: values.get(name) for name in LIMIT_NAMES})


@dataclass(frozen=True, slots=True)
class ChallengeRiskLimits:
    maximum_order_notional_tmn: Decimal | str | int | None = None
    maximum_asset_exposure_tmn: Decimal | str | int | None = None
    maximum_total_deployed_tmn: Decimal | str | int | None = None
    maximum_open_orders: int | None = None
    maximum_orders_per_window: int | None = None
    maximum_daily_loss_tmn: Decimal | str | int | None = None
    maximum_peak_drawdown_percent: Decimal | str | int | None = None
    maximum_consecutive_losses: int | None = None
    maximum_consecutive_errors: int | None = None
    maximum_market_data_age_seconds: int | None = None
    maximum_ai_signal_age_seconds: int | None = None
    maximum_spread_basis_points: Decimal | str | int | None = None
    maximum_total_cost_basis_points: Decimal | str | int | None = None
    maximum_slippage_basis_points: Decimal | str | int | None = None
    maximum_liquidity_utilization_percent: Decimal | str | int | None = None

    def __post_init__(self) -> None:
        for name in LIMIT_NAMES:
            value = getattr(self, name)
            if value is None:
                continue
            if name in {"maximum_open_orders", "maximum_orders_per_window", "maximum_consecutive_losses", "maximum_consecutive_errors", "maximum_market_data_age_seconds", "maximum_ai_signal_age_seconds"}:
                if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                    raise ChallengePolicyError(f"{name} must be a nonnegative integer")
            else:
                object.__setattr__(self, name, _decimal(value, name))

    @property
    def missing_limits(self) -> tuple[str, ...]:
        return tuple(name for name in LIMIT_NAMES if getattr(self, name) is None)


@dataclass(frozen=True, slots=True)
class RiskProposal:
    pair: str
    notional_tmn: Decimal | str | int
    asset_exposure_after_tmn: Decimal | str | int
    total_deployed_after_tmn: Decimal | str | int
    worst_case_loss_tmn: Decimal | str | int
    projected_drawdown_percent: Decimal | str | int
    estimated_spread_basis_points: Decimal | str | int
    estimated_slippage_basis_points: Decimal | str | int
    liquidity_utilization_percent: Decimal | str | int
    estimated_total_cost_basis_points: Decimal | str | int
    fees_known: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "pair", normalize_spot_pair(self.pair))
        for name in (
            "notional_tmn", "asset_exposure_after_tmn", "total_deployed_after_tmn",
            "worst_case_loss_tmn", "projected_drawdown_percent",
            "estimated_spread_basis_points", "estimated_slippage_basis_points",
            "liquidity_utilization_percent", "estimated_total_cost_basis_points",
        ):
            object.__setattr__(self, name, _decimal(getattr(self, name), name))
        if not isinstance(self.fees_known, bool):
            raise ChallengePolicyError("fees_known must be explicit true or false")


@dataclass(frozen=True, slots=True)
class RiskObservation:
    open_orders: int | None
    orders_in_window: int | None
    daily_loss_tmn: Decimal | str | int | None
    peak_drawdown_percent: Decimal | str | int | None
    consecutive_losses: int | None
    consecutive_errors: int | None
    market_data_age_seconds: int | None
    ai_signal_age_seconds: int | None
    account_reconciled: bool | None
    orders_reconciled: bool | None
    emergency_stop_active: bool | None

    def __post_init__(self) -> None:
        for name in ("open_orders", "orders_in_window", "consecutive_losses", "consecutive_errors", "market_data_age_seconds", "ai_signal_age_seconds"):
            value = getattr(self, name)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise ChallengePolicyError(f"{name} must be a nonnegative integer or unknown")
        for name in ("daily_loss_tmn", "peak_drawdown_percent"):
            value = getattr(self, name)
            if value is not None:
                object.__setattr__(self, name, _decimal(value, name))
        for name in ("account_reconciled", "orders_reconciled", "emergency_stop_active"):
            value = getattr(self, name)
            if value is not None and not isinstance(value, bool):
                raise ChallengePolicyError(f"{name} must be true, false, or unknown")


@dataclass(frozen=True, slots=True)
class RiskGateDecision:
    allowed: bool
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "reason_codes": list(self.reason_codes)}


def evaluate_challenge_risk(
    proposal: RiskProposal,
    observation: RiskObservation,
    limits: ChallengeRiskLimits,
    *,
    initial_capital_tmn: Decimal | str | int = "5000000",
) -> RiskGateDecision:
    """Evaluate caller-configured limits; missing evidence/limits block the intent."""
    capital = _decimal(initial_capital_tmn, "initial_capital_tmn")
    reasons: list[str] = [f"RISK_LIMIT_MISSING:{name}" for name in limits.missing_limits]
    order_limit = limits.maximum_order_notional_tmn
    if order_limit is not None and order_limit >= capital:
        reasons.append("MAX_ORDER_MUST_BE_LESS_THAN_INITIAL_CAPITAL")
    deployed_limit = limits.maximum_total_deployed_tmn
    if deployed_limit is not None and deployed_limit > capital:
        reasons.append("MAX_TOTAL_DEPLOYED_EXCEEDS_CHALLENGE_CAPITAL")
    asset_limit = limits.maximum_asset_exposure_tmn
    if asset_limit is not None and asset_limit > capital:
        reasons.append("MAX_ASSET_EXPOSURE_EXCEEDS_CHALLENGE_CAPITAL")

    _above(proposal.notional_tmn, order_limit, "ORDER_NOTIONAL_LIMIT_EXCEEDED", reasons)
    _above(proposal.asset_exposure_after_tmn, asset_limit, "ASSET_EXPOSURE_LIMIT_EXCEEDED", reasons)
    _above(proposal.total_deployed_after_tmn, deployed_limit, "TOTAL_DEPLOYED_LIMIT_EXCEEDED", reasons)
    if observation.daily_loss_tmn is None:
        reasons.append("DAILY_LOSS_STATE_UNKNOWN")
    elif limits.maximum_daily_loss_tmn is not None and observation.daily_loss_tmn + proposal.worst_case_loss_tmn > limits.maximum_daily_loss_tmn:
        reasons.append("DAILY_LOSS_LIMIT_EXCEEDED")
    if limits.maximum_peak_drawdown_percent is not None and proposal.projected_drawdown_percent > limits.maximum_peak_drawdown_percent:
        reasons.append("PROJECTED_DRAWDOWN_LIMIT_EXCEEDED")
    if observation.peak_drawdown_percent is None:
        reasons.append("DRAWDOWN_STATE_UNKNOWN")
    elif limits.maximum_peak_drawdown_percent is not None and observation.peak_drawdown_percent >= limits.maximum_peak_drawdown_percent:
        reasons.append("DRAWDOWN_STOP_REACHED")

    _count_gate(observation.open_orders, limits.maximum_open_orders, "OPEN_ORDER_COUNT_UNKNOWN", "MAX_OPEN_ORDERS_REACHED", reasons)
    _count_gate(observation.orders_in_window, limits.maximum_orders_per_window, "ORDER_RATE_STATE_UNKNOWN", "MAX_ORDERS_PER_WINDOW_REACHED", reasons)
    _count_gate(observation.consecutive_losses, limits.maximum_consecutive_losses, "LOSS_COOLDOWN_STATE_UNKNOWN", "LOSS_COOLDOWN_ACTIVE", reasons)
    _count_gate(observation.consecutive_errors, limits.maximum_consecutive_errors, "ERROR_COOLDOWN_STATE_UNKNOWN", "ERROR_COOLDOWN_ACTIVE", reasons)
    _count_gate(observation.market_data_age_seconds, limits.maximum_market_data_age_seconds, "MARKET_DATA_FRESHNESS_UNKNOWN", "MARKET_DATA_STALE", reasons)
    _count_gate(observation.ai_signal_age_seconds, limits.maximum_ai_signal_age_seconds, "AI_SIGNAL_FRESHNESS_UNKNOWN", "AI_SIGNAL_STALE", reasons)
    _above(proposal.estimated_spread_basis_points, limits.maximum_spread_basis_points, "SPREAD_LIMIT_EXCEEDED", reasons)
    _above(proposal.estimated_slippage_basis_points, limits.maximum_slippage_basis_points, "SLIPPAGE_LIMIT_EXCEEDED", reasons)
    _above(proposal.liquidity_utilization_percent, limits.maximum_liquidity_utilization_percent, "LIQUIDITY_UTILIZATION_LIMIT_EXCEEDED", reasons)
    _above(proposal.estimated_total_cost_basis_points, limits.maximum_total_cost_basis_points, "TOTAL_COST_LIMIT_EXCEEDED", reasons)
    if observation.account_reconciled is not True:
        reasons.append("ACCOUNT_RECONCILIATION_NOT_CONFIRMED")
    if observation.orders_reconciled is not True:
        reasons.append("OPEN_ORDERS_NOT_RECONCILED")
    if observation.emergency_stop_active is not False:
        reasons.append("EMERGENCY_STOP_ACTIVE_OR_UNKNOWN")
    if not proposal.fees_known:
        reasons.append("FEE_MODEL_UNKNOWN")
    return RiskGateDecision(not reasons, tuple(dict.fromkeys(reasons)))


def _above(value: Decimal, maximum: Decimal | int | None, code: str, reasons: list[str]) -> None:
    if maximum is None:
        return
    if value > maximum:
        reasons.append(code)


def _count_gate(value: int | None, maximum: int | None, unknown: str, exceeded: str, reasons: list[str]) -> None:
    if value is None or maximum is None:
        reasons.append(unknown)
    elif value >= maximum:
        reasons.append(exceeded)
