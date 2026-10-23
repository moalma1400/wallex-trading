"""Offline-only tests for Feature 008 activation and mediated execution."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal

import pytest

from wallex_mcp.execution_client import (
    ExecutionClientError,
    OrderOutcomeUnknown,
    MediatedExecutionClient,
    OrderRiskEvidence,
    VerifiedExecutionToolContract,
)
from wallex_mcp.execution_policy import (
    ExecutionPolicyError,
    LiveActivationPolicy,
    OrderIntent,
    validate_order_intent,
)


NOW = datetime(2026, 10, 23, 12, 0, tzinfo=timezone.utc)


def valid_policy_mapping():
    return {
        "challenge_id": "wallex-starcoach-agentic-ai-hackathon",
        "activation_record_id": "TEST-ONLY-NOT-A-LIVE-AUTHORIZATION",
        "official_rules_url": "https://example.invalid/contest-rules",
        "rules_verified": True,
        "account_permissions_verified": True,
        "allowed_markets_verified": True,
        "risk_limits_verified": True,
        "compliance_review_status": "APPROVED",
        "challenge_start_utc": "2026-10-23T00:00:00Z",
        "challenge_cutoff_utc": "2026-10-24T00:00:00Z",
        "allowed_pairs": ["ABC/TMN"],
        "allowed_quote_assets": ["TMN"],
        "allowed_order_types": ["TEST-LIMIT"],
        "risk_limits": {
            "maximum_order_notional_tmn": "100000",
            "maximum_open_orders": 5,
            "maximum_orders_per_window": 10,
            "maximum_daily_loss_tmn": "20000",
            "maximum_market_data_age_seconds": 30,
            "maximum_spread_basis_points": "50",
            "maximum_total_cost_basis_points": "100",
        },
    }


def valid_intent():
    return OrderIntent(
        symbol="ABCTMN",
        base_asset="ABC",
        quote_asset="TMN",
        side="BUY",
        order_type="TEST-LIMIT",
        price=Decimal("10"),
        quantity=Decimal("100"),
        market_observed_at=NOW,
        market_is_spot=True,
        market_constraints_verified=True,
        price_precision=2,
        amount_precision=2,
        price_step=Decimal("0.01"),
        quantity_step=Decimal("0.01"),
        minimum_quantity=Decimal("0.01"),
        minimum_notional_tmn=Decimal("100"),
    )


def contract(**changes):
    values = {
        "place_order_tool": "wallex.place_order",
        "get_order_tool": "wallex.get_order",
        "source_url": "https://example.invalid/verified-tool-contract",
        "version": "test-contract-v1",
        "verified": True,
    }
    values.update(changes)
    return VerifiedExecutionToolContract(**values)


def test_policy_requires_every_activation_gate():
    raw = valid_policy_mapping()
    raw["account_permissions_verified"] = False
    with pytest.raises(ExecutionPolicyError, match="account_permissions_verified"):
        LiveActivationPolicy.from_mapping(raw)


def test_policy_rejects_missing_numeric_risk_limits():
    raw = valid_policy_mapping()
    raw["risk_limits"]["maximum_order_notional_tmn"] = None
    with pytest.raises(ExecutionPolicyError, match="Missing explicit risk limits"):
        LiveActivationPolicy.from_mapping(raw)


def test_valid_order_intent_passes_offline_policy():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    notional = validate_order_intent(
        valid_intent(), policy, set(),
        open_orders_count=0, orders_in_window=0,
        daily_loss_tmn=Decimal("0"),
        spread_basis_points=Decimal("10"),
        total_cost_basis_points=Decimal("20"),
        now=NOW,
    )
    assert notional == Decimal("1000")


@pytest.mark.parametrize(
    ("intent_changes", "disabled", "match"),
    [
        ({"market_is_spot": False}, set(), "only verified Spot"),
        ({"quote_asset": "USDT"}, set(), "not in the explicit verified allowlist"),
        ({}, {"ABC/TMN"}, "disabled-pair registry"),
        ({"quantity": Decimal("20000")}, set(), "notional exceeds"),
        ({"market_observed_at": datetime(2026, 10, 23, 11, 0, tzinfo=timezone.utc)}, set(), "stale"),
        ({"side": "WITHDRAW"}, set(), "side must be BUY or SELL"),
    ],
)
def test_order_intent_fails_closed(intent_changes, disabled, match):
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    intent = replace(valid_intent(), **intent_changes)
    with pytest.raises(ExecutionPolicyError, match=match):
        validate_order_intent(
            intent, policy, disabled,
            open_orders_count=0, orders_in_window=0,
            daily_loss_tmn=Decimal("0"),
            spread_basis_points=Decimal("10"),
            total_cost_basis_points=Decimal("20"),
            now=NOW,
        )


def test_order_outside_challenge_window_is_blocked():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    with pytest.raises(ExecutionPolicyError, match="outside the verified challenge window"):
        policy.assert_live_window(datetime(2026, 10, 24, 0, 0, tzinfo=timezone.utc))


def test_unverified_tool_contract_is_rejected():
    with pytest.raises(ExecutionClientError, match="explicitly verified"):
        contract(verified=False)


def test_order_intent_delegates_only_to_verified_mediation_tool():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    calls = []

    def fake_invoke(name, arguments):
        calls.append((name, arguments))
        return {"success": True, "result": {"clientOrderId": arguments["client_id"]}}

    client = MediatedExecutionClient(policy, contract(), fake_invoke, disabled_pairs=set())
    evidence = OrderRiskEvidence(0, 0, Decimal("0"), Decimal("10"), Decimal("20"))
    result = client.create_order(
        client_id="cid-1", intent=valid_intent(), risk_evidence=evidence, now=NOW,
    )
    assert result["success"] is True
    assert len(calls) == 1
    assert calls[0][0] == "wallex.place_order"
    assert calls[0][1]["price"] == "10"
    assert "api_key" not in calls[0][1]
    assert "x-api-key" not in calls[0][1]


def test_mediated_order_timeout_is_ambiguous_and_never_retried():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    calls = []

    def fake_invoke(name, arguments):
        calls.append((name, arguments))
        raise TimeoutError("synthetic timeout")

    client = MediatedExecutionClient(policy, contract(), fake_invoke, disabled_pairs=set())
    evidence = OrderRiskEvidence(0, 0, Decimal("0"), Decimal("10"), Decimal("20"))
    with pytest.raises(OrderOutcomeUnknown, match="reconcile"):
        client.create_order(
            client_id="cid-1", intent=valid_intent(), risk_evidence=evidence, now=NOW,
        )
    assert len(calls) == 1


def test_order_reconciliation_is_available_after_cutoff():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    calls = []

    def fake_invoke(name, arguments):
        calls.append((name, arguments))
        return {"success": True, "result": {"clientOrderId": arguments["client_id"]}}

    client = MediatedExecutionClient(policy, contract(), fake_invoke, disabled_pairs=set())
    result = client.get_order("cid-1")
    assert result["success"] is True
    assert calls[0][0] == "wallex.get_order"


def test_tool_name_is_validated():
    with pytest.raises(ExecutionClientError, match="place_order_tool"):
        contract(place_order_tool="https://untrusted.example")


def test_blocked_risk_never_calls_execution_tool():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    calls = []

    def fake_invoke(name, arguments):
        calls.append((name, arguments))
        return {"success": True, "result": {}}

    client = MediatedExecutionClient(policy, contract(), fake_invoke, disabled_pairs={"ABC/TMN"})
    evidence = OrderRiskEvidence(0, 0, Decimal("0"), Decimal("10"), Decimal("20"))
    with pytest.raises(ExecutionClientError, match="blocked by deterministic policy"):
        client.create_order(
            client_id="cid-1", intent=valid_intent(), risk_evidence=evidence, now=NOW,
        )
    assert calls == []
