"""Offline-only tests for Feature 008 policy and order client."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import json

import pytest

from wallex_mcp.execution_client import (
    ExecutionClientError,
    OrderOutcomeUnknown,
    WallexExecutionClient,
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
    )


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


class FakeTransport:
    def __init__(self, payload=None, *, raise_on_request=False, status_code=200):
        self.payload = payload or {"success": True, "result": {"clientOrderId": "cid-1"}}
        self.raise_on_request = raise_on_request
        self.status_code = status_code
        self.calls = []

    def Client(self, timeout=None):
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def request(self, method, url, headers=None, json=None):
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {}), "json": json})
        if self.raise_on_request:
            raise TimeoutError("synthetic timeout")
        response = MagicMock()
        response.status_code = self.status_code
        response.content = __import__("json").dumps(self.payload).encode("utf-8")
        return response


def test_post_is_not_retried_and_timeout_is_outcome_unknown():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    transport = FakeTransport(raise_on_request=True)
    client = WallexExecutionClient("SYNTHETIC-KEY", policy, transport=transport)
    with pytest.raises(OrderOutcomeUnknown, match="reconcile"):
        client.create_order(
            client_id="cid-1", symbol="ABCTMN", side="BUY",
            order_type="TEST-LIMIT", price="10", quantity="1", now=NOW,
        )
    assert len(transport.calls) == 1


def test_create_order_uses_fixed_path_and_does_not_leak_key():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    transport = FakeTransport()
    client = WallexExecutionClient("SYNTHETIC-KEY", policy, transport=transport)
    result = client.create_order(
        client_id="cid-1", symbol="ABCTMN", side="BUY",
        order_type="TEST-LIMIT", price="10", quantity="1", now=NOW,
    )
    assert result["success"] is True
    assert len(transport.calls) == 1
    assert transport.calls[0]["method"] == "POST"
    assert transport.calls[0]["url"] == "https://api.wallex.ir/v1/account/orders"
    assert transport.calls[0]["headers"]["x-api-key"] == "SYNTHETIC-KEY"


def test_client_id_path_injection_is_rejected_before_request():
    policy = LiveActivationPolicy.from_mapping(valid_policy_mapping())
    transport = FakeTransport()
    client = WallexExecutionClient("SYNTHETIC-KEY", policy, transport=transport)
    with pytest.raises(ExecutionClientError, match="client_id"):
        client.get_order("../other")
    assert transport.calls == []
