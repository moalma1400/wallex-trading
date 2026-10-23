"""Fail-closed activation and deterministic pre-trade checks for Feature 008.

This module performs no network I/O. Live execution requires an explicitly
reviewed policy file and complete evidence; no risk or market defaults exist.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Mapping


class ExecutionPolicyError(ValueError):
    """Activation or order-intent evidence is incomplete or invalid."""


def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ExecutionPolicyError(f"{field} must be an explicit decimal value")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise ExecutionPolicyError(f"{field} must be a valid decimal") from exc
    if not result.is_finite():
        raise ExecutionPolicyError(f"{field} must be finite")
    return result


def _utc(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.strip():
        raise ExecutionPolicyError(f"{field} must be an explicit ISO-8601 timestamp")
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ExecutionPolicyError(f"{field} is not valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ExecutionPolicyError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


@dataclass(frozen=True)
class RiskLimits:
    maximum_order_notional_tmn: Decimal
    maximum_asset_exposure_tmn: Decimal
    maximum_total_deployed_tmn: Decimal
    maximum_open_orders: int
    maximum_orders_per_window: int
    maximum_daily_loss_tmn: Decimal
    maximum_market_data_age_seconds: int
    maximum_spread_basis_points: Decimal
    maximum_total_cost_basis_points: Decimal

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "RiskLimits":
        required = (
            "maximum_order_notional_tmn",
            "maximum_asset_exposure_tmn",
            "maximum_total_deployed_tmn",
            "maximum_open_orders",
            "maximum_orders_per_window",
            "maximum_daily_loss_tmn",
            "maximum_market_data_age_seconds",
            "maximum_spread_basis_points",
            "maximum_total_cost_basis_points",
        )
        missing = [key for key in required if key not in raw or raw[key] is None]
        if missing:
            raise ExecutionPolicyError("Missing explicit risk limits: " + ", ".join(missing))
        values = {
            "maximum_order_notional_tmn": _decimal(raw["maximum_order_notional_tmn"], "maximum_order_notional_tmn"),
            "maximum_asset_exposure_tmn": _decimal(raw["maximum_asset_exposure_tmn"], "maximum_asset_exposure_tmn"),
            "maximum_total_deployed_tmn": _decimal(raw["maximum_total_deployed_tmn"], "maximum_total_deployed_tmn"),
            "maximum_open_orders": raw["maximum_open_orders"],
            "maximum_orders_per_window": raw["maximum_orders_per_window"],
            "maximum_daily_loss_tmn": _decimal(raw["maximum_daily_loss_tmn"], "maximum_daily_loss_tmn"),
            "maximum_market_data_age_seconds": raw["maximum_market_data_age_seconds"],
            "maximum_spread_basis_points": _decimal(raw["maximum_spread_basis_points"], "maximum_spread_basis_points"),
            "maximum_total_cost_basis_points": _decimal(raw["maximum_total_cost_basis_points"], "maximum_total_cost_basis_points"),
        }
        for key in ("maximum_open_orders", "maximum_orders_per_window", "maximum_market_data_age_seconds"):
            if isinstance(values[key], bool) or not isinstance(values[key], int) or values[key] <= 0:
                raise ExecutionPolicyError(f"{key} must be a positive integer")
        for key in (
            "maximum_order_notional_tmn",
            "maximum_asset_exposure_tmn",
            "maximum_total_deployed_tmn",
            "maximum_daily_loss_tmn",
            "maximum_spread_basis_points",
            "maximum_total_cost_basis_points",
        ):
            if values[key] < 0:
                raise ExecutionPolicyError(f"{key} must not be negative")
        if values["maximum_order_notional_tmn"] <= 0:
            raise ExecutionPolicyError("maximum_order_notional_tmn must be positive")
        return cls(**values)


@dataclass(frozen=True)
class LiveActivationPolicy:
    challenge_id: str
    activation_record_id: str
    live_execution_enabled: bool
    owner_activation_confirmed: bool
    emergency_stop_active: bool
    official_rules_url: str
    rules_verified: bool
    account_permissions_verified: bool
    allowed_markets_verified: bool
    risk_limits_verified: bool
    fees_verified: bool
    compliance_review_status: str
    challenge_start_utc: datetime
    challenge_cutoff_utc: datetime
    allowed_pairs: frozenset[str]
    allowed_quote_assets: frozenset[str]
    allowed_order_types: frozenset[str]
    risk_limits: RiskLimits

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> "LiveActivationPolicy":
        if raw.get("challenge_id") != "wallex-starcoach-agentic-ai-hackathon":
            raise ExecutionPolicyError("challenge_id does not match the configured competition")
        activation_id = raw.get("activation_record_id")
        if not isinstance(activation_id, str) or not activation_id.strip():
            raise ExecutionPolicyError("activation_record_id is required")
        if raw.get("live_execution_enabled") is not True:
            raise ExecutionPolicyError("live_execution_enabled must be explicitly true")
        if raw.get("owner_activation_confirmed") is not True:
            raise ExecutionPolicyError("owner_activation_confirmed must be explicitly true")
        if raw.get("emergency_stop_active") is not False:
            raise ExecutionPolicyError("emergency_stop_active must be explicitly false")
        rules_url = raw.get("official_rules_url")
        if not isinstance(rules_url, str) or not rules_url.startswith("https://"):
            raise ExecutionPolicyError("official_rules_url must be an HTTPS URL")
        for key in ("rules_verified", "account_permissions_verified", "allowed_markets_verified", "risk_limits_verified", "fees_verified"):
            if raw.get(key) is not True:
                raise ExecutionPolicyError(f"{key} must be explicitly true")
        if raw.get("compliance_review_status") != "APPROVED":
            raise ExecutionPolicyError("compliance_review_status must be APPROVED")
        start = _utc(raw.get("challenge_start_utc"), "challenge_start_utc")
        cutoff = _utc(raw.get("challenge_cutoff_utc"), "challenge_cutoff_utc")
        if cutoff <= start:
            raise ExecutionPolicyError("challenge cutoff must be after challenge start")
        pairs_raw = raw.get("allowed_pairs")
        quotes_raw = raw.get("allowed_quote_assets")
        types_raw = raw.get("allowed_order_types")
        if not isinstance(pairs_raw, list) or not pairs_raw:
            raise ExecutionPolicyError("allowed_pairs must be a non-empty explicit list")
        if not isinstance(quotes_raw, list) or not quotes_raw:
            raise ExecutionPolicyError("allowed_quote_assets must be a non-empty explicit list")
        if not isinstance(types_raw, list) or not types_raw:
            raise ExecutionPolicyError("allowed_order_types must be a non-empty verified list")
        pair_pattern = re.compile(r"^[A-Z0-9]+/[A-Z0-9]+$")
        if any(not isinstance(p, str) or not pair_pattern.fullmatch(p) for p in pairs_raw):
            raise ExecutionPolicyError("allowed_pairs must use normalized BASE/QUOTE syntax")
        if len(set(pairs_raw)) != len(pairs_raw):
            raise ExecutionPolicyError("allowed_pairs contains duplicates")
        for field, items in (("allowed_quote_assets", quotes_raw), ("allowed_order_types", types_raw)):
            if any(not isinstance(v, str) or not v.strip() for v in items):
                raise ExecutionPolicyError(f"{field} must contain non-empty strings")
        if len(set(quotes_raw)) != len(quotes_raw) or len(set(types_raw)) != len(types_raw):
            raise ExecutionPolicyError("quote assets and order types must not contain duplicates")
        limits = raw.get("risk_limits")
        if not isinstance(limits, Mapping):
            raise ExecutionPolicyError("risk_limits object is required")
        return cls(
            challenge_id=raw["challenge_id"],
            activation_record_id=activation_id.strip(),
            live_execution_enabled=True,
            owner_activation_confirmed=True,
            emergency_stop_active=False,
            official_rules_url=rules_url,
            rules_verified=True,
            account_permissions_verified=True,
            allowed_markets_verified=True,
            risk_limits_verified=True,
            fees_verified=True,
            compliance_review_status="APPROVED",
            challenge_start_utc=start,
            challenge_cutoff_utc=cutoff,
            allowed_pairs=frozenset(pairs_raw),
            allowed_quote_assets=frozenset(quotes_raw),
            allowed_order_types=frozenset(types_raw),
            risk_limits=RiskLimits.from_mapping(limits),
        )

    def assert_live_window(self, now: datetime | None = None) -> None:
        if not self.live_execution_enabled or not self.owner_activation_confirmed:
            raise ExecutionPolicyError("live execution has not been explicitly activated")
        if self.emergency_stop_active:
            raise ExecutionPolicyError("emergency stop is active")
        instant = now or datetime.now(timezone.utc)
        if instant.tzinfo is None or instant.utcoffset() is None:
            raise ExecutionPolicyError("current time must include timezone")
        instant = instant.astimezone(timezone.utc)
        if not (self.challenge_start_utc <= instant < self.challenge_cutoff_utc):
            raise ExecutionPolicyError("live execution is outside the verified challenge window")


def load_live_policy(path: str | Path) -> LiveActivationPolicy:
    """Load an operator-reviewed policy JSON; never fills missing values."""
    try:
        raw = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ExecutionPolicyError("activation policy cannot be read as JSON") from exc
    if not isinstance(raw, dict):
        raise ExecutionPolicyError("activation policy must be a JSON object")
    return LiveActivationPolicy.from_mapping(raw)


@dataclass(frozen=True)
class OrderIntent:
    symbol: str
    base_asset: str
    quote_asset: str
    side: str
    order_type: str
    price: Decimal
    quantity: Decimal
    market_observed_at: datetime
    market_is_spot: bool
    market_data_verified: bool
    market_constraints_verified: bool
    price_precision: int
    amount_precision: int
    price_step: Decimal
    quantity_step: Decimal
    minimum_quantity: Decimal
    minimum_notional_tmn: Decimal


def validate_order_intent(
    intent: OrderIntent,
    policy: LiveActivationPolicy,
    disabled_pairs: set[str] | frozenset[str],
    *,
    open_orders_count: int,
    orders_in_window: int,
    daily_loss_tmn: Decimal,
    spread_basis_points: Decimal,
    total_cost_basis_points: Decimal,
    current_asset_exposure_tmn: Decimal,
    total_deployed_tmn: Decimal,
    available_quote_balance_tmn: Decimal,
    available_base_quantity: Decimal,
    account_state_reconciled: bool,
    now: datetime | None = None,
) -> Decimal:
    """Return notional in TMN if allowed; otherwise raise a specific veto.

    Callers must source market/account observations from a verified adapter,
    not from an LLM or untrusted tool argument.
    """
    policy.assert_live_window(now)
    if intent.side not in {"BUY", "SELL"}:
        raise ExecutionPolicyError("side must be BUY or SELL")
    if intent.order_type not in policy.allowed_order_types:
        raise ExecutionPolicyError("order type is not in the verified policy allowlist")
    if intent.market_is_spot is not True:
        raise ExecutionPolicyError("only verified Spot markets are allowed")
    if intent.market_data_verified is not True:
        raise ExecutionPolicyError("verified market data is required")
    if account_state_reconciled is not True:
        raise ExecutionPolicyError("account and order state must be reconciled before execution")
    if intent.market_constraints_verified is not True:
        raise ExecutionPolicyError("verified price/quantity constraints are required")
    for field, value in (("price_precision", intent.price_precision), ("amount_precision", intent.amount_precision)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise ExecutionPolicyError(f"{field} must be a verified nonnegative integer")
    pair = f"{intent.base_asset}/{intent.quote_asset}"
    if pair not in policy.allowed_pairs:
        raise ExecutionPolicyError("market is not in the explicit verified allowlist")
    if pair in disabled_pairs:
        raise ExecutionPolicyError("market appears in the challenge disabled-pair registry")
    if intent.quote_asset not in policy.allowed_quote_assets:
        raise ExecutionPolicyError("quote asset is not explicitly enabled")
    if not intent.symbol or not re.fullmatch(r"[A-Za-z0-9]{2,40}", intent.symbol):
        raise ExecutionPolicyError("symbol format is invalid")
    if intent.symbol.upper() != (intent.base_asset + intent.quote_asset).upper():
        raise ExecutionPolicyError("symbol does not match the verified base/quote metadata")
    price = _decimal(intent.price, "price")
    quantity = _decimal(intent.quantity, "quantity")
    if price <= 0 or quantity <= 0:
        raise ExecutionPolicyError("price and quantity must be positive")
    price_step = _decimal(intent.price_step, "price_step")
    quantity_step = _decimal(intent.quantity_step, "quantity_step")
    minimum_quantity = _decimal(intent.minimum_quantity, "minimum_quantity")
    minimum_notional = _decimal(intent.minimum_notional_tmn, "minimum_notional_tmn")
    if price_step <= 0 or quantity_step <= 0 or minimum_quantity < 0 or minimum_notional < 0:
        raise ExecutionPolicyError("verified steps must be positive and minimums nonnegative")
    if price.normalize().as_tuple().exponent < -intent.price_precision:
        raise ExecutionPolicyError("price exceeds verified price precision")
    if quantity.normalize().as_tuple().exponent < -intent.amount_precision:
        raise ExecutionPolicyError("quantity exceeds verified amount precision")
    if price % price_step != 0 or quantity % quantity_step != 0:
        raise ExecutionPolicyError("price or quantity violates verified step size")
    if quantity < minimum_quantity:
        raise ExecutionPolicyError("quantity is below verified minimum quantity")
    observed = intent.market_observed_at
    if observed.tzinfo is None or observed.utcoffset() is None:
        raise ExecutionPolicyError("market observation timestamp must include timezone")
    instant = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    age = (instant - observed.astimezone(timezone.utc)).total_seconds()
    if age < 0 or age > policy.risk_limits.maximum_market_data_age_seconds:
        raise ExecutionPolicyError("market metadata/data is stale or timestamp is in the future")
    if isinstance(open_orders_count, bool) or not isinstance(open_orders_count, int) or open_orders_count < 0:
        raise ExecutionPolicyError("open_orders_count is invalid")
    if open_orders_count >= policy.risk_limits.maximum_open_orders:
        raise ExecutionPolicyError("maximum open-order count reached")
    if isinstance(orders_in_window, bool) or not isinstance(orders_in_window, int) or orders_in_window < 0:
        raise ExecutionPolicyError("orders_in_window is invalid")
    if orders_in_window >= policy.risk_limits.maximum_orders_per_window:
        raise ExecutionPolicyError("maximum order rate reached")
    loss = _decimal(daily_loss_tmn, "daily_loss_tmn")
    if loss < 0:
        raise ExecutionPolicyError("daily_loss_tmn must be nonnegative")
    if loss >= policy.risk_limits.maximum_daily_loss_tmn:
        raise ExecutionPolicyError("daily loss limit reached")
    spread = _decimal(spread_basis_points, "spread_basis_points")
    cost = _decimal(total_cost_basis_points, "total_cost_basis_points")
    if spread < 0 or cost < 0:
        raise ExecutionPolicyError("spread and cost estimates must be nonnegative")
    if spread > policy.risk_limits.maximum_spread_basis_points:
        raise ExecutionPolicyError("spread exceeds configured maximum")
    if cost > policy.risk_limits.maximum_total_cost_basis_points:
        raise ExecutionPolicyError("estimated total cost exceeds configured maximum")
    notional = price * quantity
    if intent.quote_asset != "TMN":
        raise ExecutionPolicyError("TMN notional conversion is not verified for this quote asset")
    if notional < minimum_notional:
        raise ExecutionPolicyError("order notional is below verified minimum notional")
    if notional > policy.risk_limits.maximum_order_notional_tmn:
        raise ExecutionPolicyError("order notional exceeds configured maximum")
    current_asset = _decimal(current_asset_exposure_tmn, "current_asset_exposure_tmn")
    deployed = _decimal(total_deployed_tmn, "total_deployed_tmn")
    available = _decimal(available_quote_balance_tmn, "available_quote_balance_tmn")
    if current_asset < 0 or deployed < 0 or available < 0:
        raise ExecutionPolicyError("exposure and available balance evidence must be nonnegative")
    base_available = _decimal(available_base_quantity, "available_base_quantity")
    if base_available < 0:
        raise ExecutionPolicyError("available base quantity must be nonnegative")
    estimated_cost = notional * cost / Decimal("10000")
    if intent.side == "BUY":
        if current_asset + notional > policy.risk_limits.maximum_asset_exposure_tmn:
            raise ExecutionPolicyError("order would exceed maximum asset exposure")
        if deployed + notional > policy.risk_limits.maximum_total_deployed_tmn:
            raise ExecutionPolicyError("order would exceed maximum total deployed capital")
        if available < notional + estimated_cost:
            raise ExecutionPolicyError("verified available quote balance is insufficient for order and estimated cost")
    elif base_available < quantity:
        raise ExecutionPolicyError("verified available base balance is insufficient for sell order")
    return notional
