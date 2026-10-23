"""Mediated execution adapter for Feature 008.

This module never connects to Wallex or handles API keys. It invokes only
explicitly verified tools through an injected MCP/Smart98 tool caller. Because
the real Smart98/Wallex order-tool contract is not yet verified, no live
tool names or invocation client are configured in this repository.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Callable, Mapping

from .execution_policy import (
    ExecutionPolicyError,
    LiveActivationPolicy,
    OrderIntent,
    validate_order_intent,
)


_TOOL_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_CLIENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")


class ExecutionClientError(RuntimeError):
    """Base error for mediated execution operations."""


class OrderOutcomeUnknown(ExecutionClientError):
    """The mediated order call may have succeeded; reconcile before resubmitting."""


@dataclass(frozen=True)
class VerifiedExecutionToolContract:
    """Contract record required before the adapter can call any tool."""

    place_order_tool: str
    get_order_tool: str
    source_url: str
    version: str
    verified: bool

    def __post_init__(self) -> None:
        if self.verified is not True:
            raise ExecutionClientError("execution tool contract must be explicitly verified")
        if not isinstance(self.source_url, str) or not self.source_url.startswith("https://"):
            raise ExecutionClientError("execution tool contract requires an HTTPS source URL")
        if not isinstance(self.version, str) or not self.version.strip():
            raise ExecutionClientError("execution tool contract version is required")
        for field, name in (
            ("place_order_tool", self.place_order_tool),
            ("get_order_tool", self.get_order_tool),
        ):
            if not isinstance(name, str) or not _TOOL_NAME.fullmatch(name):
                raise ExecutionClientError(f"{field} is missing or invalid")


@dataclass(frozen=True)
class OrderRiskEvidence:
    """Risk observations supplied by a verified, non-model-controlled adapter."""

    open_orders_count: int
    orders_in_window: int
    daily_loss_tmn: Decimal
    spread_basis_points: Decimal
    total_cost_basis_points: Decimal


class MediatedExecutionClient:
    """Policy-check intents and delegate through a verified MCP tool contract.

    The injected callable belongs to the verified Smart98/MCP integration.
    No HTTP, URL, headers, API key, or direct Wallex fallback exists here.
    """

    def __init__(
        self,
        policy: LiveActivationPolicy,
        contract: VerifiedExecutionToolContract,
        invoke_tool: Callable[[str, Mapping[str, Any]], Any],
        disabled_pairs: set[str] | frozenset[str],
    ) -> None:
        if not callable(invoke_tool):
            raise ExecutionClientError("a verified MCP tool invoker is required")
        self._policy = policy
        self._contract = contract
        self._invoke_tool = invoke_tool
        self._disabled_pairs = frozenset(disabled_pairs)

    @staticmethod
    def _validate_client_id(client_id: str) -> None:
        if not isinstance(client_id, str) or not _CLIENT_ID.fullmatch(client_id):
            raise ExecutionClientError("client_id has an invalid format")

    def create_order(
        self,
        *,
        client_id: str,
        intent: OrderIntent,
        risk_evidence: OrderRiskEvidence,
        now=None,
    ) -> dict[str, Any]:
        """Validate policy/risk locally, then delegate once; never auto-retry."""
        self._validate_client_id(client_id)
        try:
            notional = validate_order_intent(
                intent,
                self._policy,
                self._disabled_pairs,
                open_orders_count=risk_evidence.open_orders_count,
                orders_in_window=risk_evidence.orders_in_window,
                daily_loss_tmn=risk_evidence.daily_loss_tmn,
                spread_basis_points=risk_evidence.spread_basis_points,
                total_cost_basis_points=risk_evidence.total_cost_basis_points,
                now=now,
            )
        except ExecutionPolicyError as exc:
            raise ExecutionClientError(f"order blocked by deterministic policy: {exc}") from exc

        payload = {
            "client_id": client_id,
            "symbol": intent.symbol,
            "side": intent.side,
            "type": intent.order_type,
            "price": format(Decimal(str(intent.price)), "f"),
            "quantity": format(Decimal(str(intent.quantity)), "f"),
            "validated_notional_tmn": format(notional, "f"),
            "policy_activation_record_id": self._policy.activation_record_id,
            "execution_contract_version": self._contract.version,
        }
        try:
            result = self._invoke_tool(self._contract.place_order_tool, payload)
        except Exception:
            raise OrderOutcomeUnknown(
                f"Order outcome unknown for client_id={client_id}; reconcile via the verified order-detail tool"
            ) from None
        if not isinstance(result, dict) or result.get("success") is not True or not isinstance(result.get("result"), dict):
            raise OrderOutcomeUnknown(
                f"Order outcome unknown for client_id={client_id}; reconcile via the verified order-detail tool"
            )
        return result

    def get_order(self, client_id: str) -> dict[str, Any]:
        """Reconcile an order by client ID; allowed after cutoff for recovery."""
        self._validate_client_id(client_id)
        try:
            result = self._invoke_tool(self._contract.get_order_tool, {"client_id": client_id})
        except Exception:
            raise ExecutionClientError("Order reconciliation failed; do not submit a replacement order") from None
        if not isinstance(result, dict) or result.get("success") is not True or not isinstance(result.get("result"), dict):
            raise ExecutionClientError("Order reconciliation response is invalid; do not submit a replacement order")
        return result
