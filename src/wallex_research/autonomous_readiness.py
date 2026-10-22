"""Fail-closed readiness policy for autonomous challenge trading.

This module only evaluates a supplied evidence snapshot. It has no network,
credential, Smart98, Wallex, or order-submission implementation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping


REQUIRED_EVIDENCE = (
    "official_rules_verified",
    "challenge_window_verified",
    "allowed_spot_markets_verified",
    "dedicated_account_verified",
    "least_privilege_permissions_verified",
    "smart98_contract_verified",
    "order_tool_schemas_verified",
    "risk_limits_configured",
    "risk_tests_passed",
    "idempotency_and_timeout_tests_passed",
    "reconciliation_tests_passed",
    "audit_and_kill_switch_verified",
    "compliance_review_complete",
    "owner_activation_recorded",
)


@dataclass(frozen=True, slots=True)
class Readiness:
    ready: bool
    reason_codes: tuple[str, ...]

    def as_dict(self) -> dict[str, Any]:
        return {"ready": self.ready, "reason_codes": list(self.reason_codes)}


def evaluate_live_readiness(
    evidence: Mapping[str, Any],
    *,
    kill_switch_enabled: bool,
    challenge_window_active: bool,
    configuration_hash: str | None,
    tool_contract_version: str | None,
) -> Readiness:
    """Allow readiness only when every required gate is explicitly true.

    This is a policy evaluator, not an order authorization token and not a
    live adapter. Callers must re-evaluate immediately before each dispatch.
    """
    reasons: list[str] = []
    if kill_switch_enabled is not False:
        reasons.append("KILL_SWITCH_ACTIVE_OR_UNKNOWN")
    if challenge_window_active is not True:
        reasons.append("CHALLENGE_WINDOW_INACTIVE_OR_UNKNOWN")
    for key in REQUIRED_EVIDENCE:
        if evidence.get(key) is not True:
            reasons.append("MISSING_OR_UNVERIFIED_" + key.upper())
    if not isinstance(configuration_hash, str) or not configuration_hash.strip():
        reasons.append("CONFIGURATION_HASH_MISSING")
    if not isinstance(tool_contract_version, str) or not tool_contract_version.strip():
        reasons.append("TOOL_CONTRACT_VERSION_MISSING")
    return Readiness(not reasons, tuple(reasons))
