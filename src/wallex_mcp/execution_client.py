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

from .execution_policy import ExecutionPolicyError, LiveActivationPolicy


_TOOL_NAME = re.compile(r"^[A-Za-z][A-Za-z0-9_.-]{0,127}$")
_CLIENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SYMBOL = re.compile(r"^[A-Za-z0-9]{2,40}$")


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
    ) -> None:
        if not callable(invoke_tool):
            raise ExecutionClientError("a verified MCP tool invoker is required")
        self._policy = policy
        self._contract = contract
        self._invoke_tool = invoke_tool

    @staticmethod
    def _positive_decimal(value: Any, field: str) -> Decimal:
        if isinstance(value, bool) or value is None:
            raise ExecutionClientError(f"{field} must be a positive decimal")
        try:
            parsed = Decimal(str(value))
        except (InvalidOperation, ValueError, TypeError) as exc:
            raise ExecutionClientError(f"{field} must be a positive decimal") from exc
        if not parsed.is_finite() or parsed <= 0:
            raise ExecutionClientError(f"{field} must be a positive finite decimal")
        return parsed

    def create_order(
        self,
        *,
        client_id: str,
        symbol: str,
        side: str,
        order_type: str,
        price: Any,
        quantity: Any,
        now=None,
    ) -> dict[str, Any]:
        """Delegate one validated order intent; never automatically retry."""
        self._policy.assert_live_window(now)
        if not isinstance(client_id, str) or not _CLIENT_ID.fullmatch(client_id):
            raise ExecutionClientError("client_id has an invalid format")
        if not isinstance(symbol, str) or not _SYMBOL.fullmatch(symbol):
            raise ExecutionClientError("symbol has an invalid format")
        if side not in {"BUY", "SELL"}:
            raise ExecutionClientError("side must be BUY or SELL")
        if order_type not in self._policy.allowed_order_types:
            raise ExecutionClientError("order type is not allowlisted by the reviewed policy")
        price_value = self._positive_decimal(price, "price")
        quantity_value = self._positive_decimal(quantity, "quantity")
        payload = {
            "client_id": client_id,
            "symbol": symbol,
            "side": side,
            "type": order_type,
            "price": format(price_value, "f"),
            "quantity": format(quantity_value, "f"),
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
        if not isinstance(client_id, str) or not _CLIENT_ID.fullmatch(client_id):
            raise ExecutionClientError("client_id has an invalid format")
        try:
            result = self._invoke_tool(self._contract.get_order_tool, {"client_id": client_id})
        except Exception:
            raise ExecutionClientError("Order reconciliation failed; do not submit a replacement order") from None
        if not isinstance(result, dict) or result.get("success") is not True or not isinstance(result.get("result"), dict):
            raise ExecutionClientError("Order reconciliation response is invalid; do not submit a replacement order")
        return result
