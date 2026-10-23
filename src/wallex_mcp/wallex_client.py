"""HTTP client restricted to explicitly allowlisted Wallex endpoints.

Every request is validated against the endpoint allowlist before the
request is attempted. Responses are bounded and validated before returning.
"""
from __future__ import annotations

import json
import logging
import time
from typing import Any, Optional

from .config import (
    BALANCES_PATH,
    DEFAULT_BACKOFF_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    MARKETS_PATH,
    OPEN_ORDERS_PATH,
    WALLEX_OFFICIAL_HOST,
    EndpointAllowlist,
)
from .redaction import redact_for_log
from .schemas import MarketsResponseModel

logger = logging.getLogger("wallex_mcp.client")


class WallexClientError(Exception):
    """Base error for the standalone Wallex HTTP client."""


class EndpointNotAllowedError(WallexClientError):
    """Raised when a request targets a host or path outside the allowlist."""


class ResponseTooLargeError(WallexClientError):
    """Raised when an upstream response exceeds the configured size limit."""


class WallexAPIError(WallexClientError):
    """Raised when the upstream service returns an error envelope."""


class WallexClient:
    """Minimal HTTP client for explicitly allowlisted, read-only Wallex APIs."""

    def __init__(
        self,
        allowlist: Optional[EndpointAllowlist] = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = DEFAULT_MAX_RESPONSE_BYTES,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_seconds: float = DEFAULT_BACKOFF_SECONDS,
        api_key: Optional[str] = None,
        transport: Optional[Any] = None,
    ) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")
        if max_retries < 0:
            raise ValueError("max_retries must be non-negative")
        if backoff_seconds < 0:
            raise ValueError("backoff_seconds must be non-negative")
        self._allowlist = allowlist or EndpointAllowlist.default()
        self._timeout_seconds = timeout_seconds
        self._max_response_bytes = max_response_bytes
        self._max_retries = max_retries
        self._backoff_seconds = backoff_seconds
        self._api_key = api_key
        self._transport = transport

    def get_markets(self) -> MarketsResponseModel:
        """Fetch and validate the public Spot markets list."""
        response = self._request("GET", WALLEX_OFFICIAL_HOST, MARKETS_PATH)
        model = MarketsResponseModel.model_validate(response)
        if not model.success:
            raise WallexAPIError("Upstream markets response reported success=false")
        return model

    def get_balances(self) -> dict[str, Any]:
        """Fetch main-account balances through the authenticated GET endpoint."""
        response = self._request("GET", WALLEX_OFFICIAL_HOST, BALANCES_PATH)
        result = response.get("result")
        if response.get("success") is not True or not isinstance(result, dict):
            raise WallexAPIError("Upstream balances response has an invalid success/result envelope")
        if not isinstance(result.get("balances"), dict):
            raise WallexAPIError("Upstream balances response is missing result.balances")
        return response

    def get_open_orders(self) -> dict[str, Any]:
        """Fetch active orders through the authenticated GET endpoint."""
        response = self._request("GET", WALLEX_OFFICIAL_HOST, OPEN_ORDERS_PATH)
        result = response.get("result")
        if response.get("success") is not True or not isinstance(result, dict):
            raise WallexAPIError("Upstream open-orders response has an invalid success/result envelope")
        # The documented API uses a symbol-keyed object of order arrays. Validate
        # that broad shape without assuming undocumented fields within each order.
        if any(not isinstance(orders, list) for orders in result.values()):
            raise WallexAPIError("Upstream open-orders result must contain arrays of orders")
        return response

    def _request(self, method: str, host: str, path: str) -> dict[str, Any]:
        if not self._allowlist.is_allowed(method, host, path):
            raise EndpointNotAllowedError(
                f"Request to {method} {host}{path} is not in the endpoint allowlist"
            )

        headers = {"Accept": "application/json"}
        if self._allowlist.requires_key(method, host, path):
            if not self._api_key:
                raise WallexClientError("Endpoint requires an API key but none was provided")
            headers["x-api-key"] = self._api_key

        last_error: Optional[BaseException] = None
        for attempt in range(self._max_retries + 1):
            try:
                raw = self._perform_request(method, host, path, headers)
                return self._decode(raw)
            except (WallexClientError, EndpointNotAllowedError, ResponseTooLargeError):
                raise
            except Exception as exc:
                last_error = exc
                if attempt >= self._max_retries:
                    raise WallexClientError(
                        f"Request to {method} {host}{path} failed after "
                        f"{self._max_retries + 1} attempts"
                    ) from exc
                logger.debug(
                    "Retrying %s %s after %s",
                    method,
                    redact_for_log(f"{host}{path}"),
                    redact_for_log(str(exc)),
                )
                if self._backoff_seconds:
                    time.sleep(self._backoff_seconds * (2**attempt))

        raise WallexClientError("Request failed without a recorded error") from last_error

    def _perform_request(self, method: str, host: str, path: str, headers: dict[str, str]) -> bytes:
        transport = self._transport
        if transport is None:
            try:
                import httpx  # type: ignore
            except ImportError as exc:  # pragma: no cover
                raise WallexClientError(
                    "No HTTP transport is available and httpx is not installed"
                ) from exc
            transport = httpx

        url = f"https://{host}{path}"
        with transport.Client(timeout=self._timeout_seconds) as client:  # type: ignore[attr-defined]
            response = client.request(method, url, headers=headers)

        if response.status_code >= 400:
            raise WallexAPIError(
                f"Upstream returned HTTP {response.status_code} for {method} {url}"
            )
        content = response.content
        if len(content) > self._max_response_bytes:
            raise ResponseTooLargeError(
                f"Upstream response of {len(content)} bytes exceeds the limit of "
                f"{self._max_response_bytes} bytes"
            )
        return content

    @staticmethod
    def _decode(raw: bytes) -> dict[str, Any]:
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise WallexClientError("Upstream response is not valid UTF-8 JSON") from exc
        if not isinstance(decoded, dict):
            raise WallexClientError("Upstream response must be a JSON object")
        return decoded
