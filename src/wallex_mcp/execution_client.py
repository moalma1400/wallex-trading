"""Fixed-contract order client for Feature 008.

This module is not registered as an MCP tool by Feature 007. It is intended
for a separately reviewed execution service. POST is never retried; a timeout
means the order outcome is unknown and must be reconciled by client_id.
"""
from __future__ import annotations

import json
import re
from typing import Any, Optional

from .config import WALLEX_OFFICIAL_HOST
from .execution_policy import ExecutionPolicyError, LiveActivationPolicy


CREATE_ORDER_PATH = "/v1/account/orders"
ORDER_DETAIL_PATH_PREFIX = "/v1/account/orders/"
_CLIENT_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9]{2,40}$")


class ExecutionClientError(RuntimeError):
    """Base error for fixed-contract order operations."""


class OrderOutcomeUnknown(ExecutionClientError):
    """POST may have reached Wallex; reconcile by client ID before any retry."""


class WallexExecutionClient:
    """Only documented create-order and order-detail routes; no arbitrary HTTP."""

    def __init__(
        self,
        api_key: str,
        policy: LiveActivationPolicy,
        *,
        timeout_seconds: float = 10.0,
        transport: Optional[Any] = None,
    ) -> None:
        if not api_key or not api_key.strip():
            raise ExecutionClientError("API key is required")
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        self._api_key = api_key
        self._policy = policy
        self._timeout_seconds = timeout_seconds
        self._transport = transport

    def create_order(
        self,
        *,
        client_id: str,
        symbol: str,
        side: str,
        order_type: str,
        price: str,
        quantity: str,
        now=None,
    ) -> dict[str, Any]:
        """Submit one order only after the policy's live window is active.

        Risk validation must be completed by the caller before this method.
        No automatic retry is performed. A transport exception is ambiguous.
        """
        self._policy.assert_live_window(now)
        self._validate_identifier(client_id, _CLIENT_ID_PATTERN, "client_id")
        self._validate_identifier(symbol, _SYMBOL_PATTERN, "symbol")
        if side not in {"BUY", "SELL"}:
            raise ExecutionClientError("side must be BUY or SELL")
        if order_type not in self._policy.allowed_order_types:
            raise ExecutionClientError("order type is not allowlisted by the reviewed policy")
        payload = {
            "client_id": client_id,
            "price": str(price),
            "quantity": str(quantity),
            "side": side,
            "symbol": symbol,
            "type": order_type,
        }
        try:
            response = self._request("POST", CREATE_ORDER_PATH, payload=payload)
        except Exception as exc:
            if isinstance(exc, ExecutionClientError):
                raise
            raise OrderOutcomeUnknown(
                f"Order outcome unknown for client_id={client_id}; reconcile via order detail"
            ) from None
        if response.get("success") is not True or not isinstance(response.get("result"), dict):
            raise ExecutionClientError("Wallex create-order response envelope is invalid; reconcile before retry")
        return response

    def get_order(self, client_id: str) -> dict[str, Any]:
        """Read order details using the documented client-ID path."""
        self._policy.assert_live_window()
        self._validate_identifier(client_id, _CLIENT_ID_PATTERN, "client_id")
        response = self._request("GET", ORDER_DETAIL_PATH_PREFIX + client_id)
        if response.get("success") is not True or not isinstance(response.get("result"), dict):
            raise ExecutionClientError("Wallex order-detail response envelope is invalid")
        return response

    @staticmethod
    def _validate_identifier(value: str, pattern: re.Pattern[str], field: str) -> None:
        if not isinstance(value, str) or not pattern.fullmatch(value):
            raise ExecutionClientError(f"{field} has an invalid format")

    def _request(self, method: str, path: str, *, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        transport = self._transport
        if transport is None:
            try:
                import httpx
            except ImportError as exc:  # pragma: no cover
                raise ExecutionClientError("httpx is not installed") from exc
            transport = httpx
        headers = {"Accept": "application/json", "x-api-key": self._api_key}
        if payload is not None:
            headers["Content-Type"] = "application/json"
        url = f"https://{WALLEX_OFFICIAL_HOST}{path}"
        with transport.Client(timeout=self._timeout_seconds) as client:
            response = client.request(method, url, headers=headers, json=payload)
        if response.status_code >= 400:
            raise ExecutionClientError(f"Wallex returned HTTP {response.status_code} for {method} {path}")
        try:
            decoded = json.loads(response.content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ExecutionClientError("Wallex response is not valid UTF-8 JSON") from exc
        if not isinstance(decoded, dict):
            raise ExecutionClientError("Wallex response must be a JSON object")
        return decoded
