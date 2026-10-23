"""Bounded, read-only CoinGecko API client."""

from __future__ import annotations

import json
import os
import re
from typing import Any, Optional

import httpx


DEFAULT_BASE_URL = "https://api.coingecko.com/api/v3"
PRO_BASE_URL = "https://pro-api.coingecko.com/api/v3"
MAX_RESPONSE_BYTES = 1_000_000
DEFAULT_TIMEOUT_SECONDS = 10.0

_ALLOWED_BASE_URLS = {DEFAULT_BASE_URL, PRO_BASE_URL}
_ID_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,100}$")
_CURRENCY_RE = re.compile(r"^[a-zA-Z]{2,10}$")


class CoinGeckoError(Exception):
    """Base exception for CoinGecko MCP failures."""


class CoinGeckoInputError(CoinGeckoError):
    """Raised when user input is invalid."""


class CoinGeckoResponseError(CoinGeckoError):
    """Raised when an upstream response is invalid or too large."""


# Secret environment-variable names per plan. Values are never logged,
# included in error messages, or exposed via repr.
DEMO_API_KEY_ENV = "COINGECKO_DEMO_API_KEY"
PRO_API_KEY_ENV = "COINGECKO_PRO_API_KEY"
LEGACY_API_KEY_ENV = "COINGECKO_API_KEY"


class CoinGeckoClient:
    """Client restricted to documented, read-only endpoints.

    The Demo plan uses base URL ``https://api.coingecko.com/api/v3`` and the
    ``x-cg-demo-api-key`` header (header auth is recommended over query-string
    keys). The key is read from ``COINGECKO_DEMO_API_KEY`` unless explicitly
    passed; the legacy ``COINGECKO_API_KEY`` name remains a fallback.
    """

    def __init__(
        self,
        *,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes: int = MAX_RESPONSE_BYTES,
        transport: Optional[httpx.BaseTransport] = None,
    ) -> None:
        configured_url = (
            base_url or os.getenv("COINGECKO_API_BASE_URL") or DEFAULT_BASE_URL
        ).rstrip("/")

        if configured_url not in _ALLOWED_BASE_URLS:
            raise ValueError(
                "COINGECKO_API_BASE_URL must be the official CoinGecko Demo "
                "or Pro API base URL"
            )
        if timeout_seconds <= 0:
            raise ValueError("timeout_seconds must be positive")
        if max_response_bytes <= 0:
            raise ValueError("max_response_bytes must be positive")

        self.base_url = configured_url
        if api_key is not None:
            resolved_key = api_key
        elif configured_url == PRO_BASE_URL:
            resolved_key = os.getenv(PRO_API_KEY_ENV) or os.getenv(
                LEGACY_API_KEY_ENV
            )
        else:
            resolved_key = os.getenv(DEMO_API_KEY_ENV) or os.getenv(
                LEGACY_API_KEY_ENV
            )
        self.api_key = (resolved_key or "").strip() or None
        self.timeout_seconds = timeout_seconds
        self.max_response_bytes = max_response_bytes
        self.transport = transport

    @property
    def api_key_configured(self) -> bool:
        """Whether a key is set; never reveals the key itself."""
        return self.api_key is not None

    def __repr__(self) -> str:
        return (
            f"CoinGeckoClient(base_url={self.base_url!r}, "
            f"api_key_configured={self.api_key_configured}, "
            f"timeout_seconds={self.timeout_seconds!r})"
        )

    @staticmethod
    def _validate_ids(ids: str) -> list[str]:
        values = [value.strip() for value in ids.split(",")]
        if not values or len(values) > 50:
            raise CoinGeckoInputError("Provide between 1 and 50 coin IDs")
        if any(not _ID_RE.fullmatch(value) for value in values):
            raise CoinGeckoInputError("Coin IDs contain invalid characters")
        return values

    @staticmethod
    def _validate_currencies(currencies: str) -> list[str]:
        values = [value.strip().lower() for value in currencies.split(",")]
        if not values or len(values) > 20:
            raise CoinGeckoInputError(
                "Provide between 1 and 20 quote currencies"
            )
        if any(not _CURRENCY_RE.fullmatch(value) for value in values):
            raise CoinGeckoInputError("Quote currencies must be currency codes")
        return values

    def _get(self, path: str, params: dict[str, Any]) -> Any:
        # Paths are internal constants, never user-supplied URLs.
        if path not in {"/ping", "/search", "/simple/price", "/coins/markets"}:
            raise CoinGeckoError("Endpoint is not allowlisted")

        headers = {"Accept": "application/json"}
        if self.api_key:
            key_header = (
                "x-cg-pro-api-key"
                if self.base_url == PRO_BASE_URL
                else "x-cg-demo-api-key"
            )
            headers[key_header] = self.api_key

        try:
            with httpx.Client(
                timeout=self.timeout_seconds,
                transport=self.transport,
                follow_redirects=False,
            ) as client:
                with client.stream(
                    "GET",
                    f"{self.base_url}{path}",
                    params=params,
                    headers=headers,
                ) as response:
                    if response.status_code == 429:
                        # Do not expose upstream bodies, headers, or credentials.
                        raise CoinGeckoError(
                            "CoinGecko returned HTTP 429 (rate limited)"
                        )
                    if response.status_code >= 400:
                        raise CoinGeckoError(
                            f"CoinGecko returned HTTP {response.status_code}"
                        )

                    body = bytearray()
                    for chunk in response.iter_bytes(chunk_size=16_384):
                        if len(body) + len(chunk) > self.max_response_bytes:
                            raise CoinGeckoResponseError(
                                "CoinGecko response exceeds size limit"
                            )
                        body.extend(chunk)
                    content = bytes(body)
        except (CoinGeckoError, CoinGeckoResponseError):
            raise
        except httpx.TimeoutException as exc:
            raise CoinGeckoError("CoinGecko request timed out") from exc
        except httpx.HTTPError as exc:
            raise CoinGeckoError("CoinGecko request failed") from exc

        try:
            payload = json.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise CoinGeckoResponseError(
                "CoinGecko response was not valid UTF-8 JSON"
            ) from exc

        if not isinstance(payload, (dict, list)):
            raise CoinGeckoResponseError("Unexpected CoinGecko response type")
        return payload

    def ping(self) -> dict[str, Any]:
        """Check API server status via the documented GET /ping endpoint."""
        payload = self._get("/ping", {})
        if not isinstance(payload, dict) or not isinstance(
            payload.get("gecko_says"), str
        ):
            raise CoinGeckoResponseError("Ping response has no status message")
        return {
            "provider": "coingecko",
            "base_url": self.base_url,
            "api_key_configured": self.api_key_configured,
            "status_message_present": True,
        }

    def search_coins(self, query: str) -> dict[str, Any]:
        query = query.strip()
        if not query or len(query) > 100:
            raise CoinGeckoInputError(
                "Search query must contain 1 to 100 characters"
            )

        payload = self._get("/search", {"query": query})
        coins = payload.get("coins") if isinstance(payload, dict) else None
        if not isinstance(coins, list):
            raise CoinGeckoResponseError("Search response has no coins list")

        return {
            "query": query,
            "coins": coins[:25],
            "count": min(len(coins), 25),
        }

    def get_price(
        self, ids: str, vs_currencies: str = "usd"
    ) -> dict[str, Any]:
        coin_ids = self._validate_ids(ids)
        currencies = self._validate_currencies(vs_currencies)
        payload = self._get(
            "/simple/price",
            {
                "ids": ",".join(coin_ids),
                "vs_currencies": ",".join(currencies),
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            },
        )
        if not isinstance(payload, dict):
            raise CoinGeckoResponseError("Price response must be an object")
        return payload

    def get_markets(
        self,
        vs_currency: str = "usd",
        per_page: int = 10,
        page: int = 1,
    ) -> dict[str, Any]:
        currency = vs_currency.strip().lower()
        if not _CURRENCY_RE.fullmatch(currency):
            raise CoinGeckoInputError("Invalid quote currency")
        if not 1 <= per_page <= 50:
            raise CoinGeckoInputError("per_page must be between 1 and 50")
        if not 1 <= page <= 100:
            raise CoinGeckoInputError("page must be between 1 and 100")

        payload = self._get(
            "/coins/markets",
            {
                "vs_currency": currency,
                "order": "market_cap_desc",
                "per_page": per_page,
                "page": page,
                "sparkline": "false",
                "price_change_percentage": "24h",
            },
        )
        if not isinstance(payload, list):
            raise CoinGeckoResponseError("Markets response must be a list")

        return {
            "vs_currency": currency,
            "page": page,
            "count": len(payload),
            "markets": payload,
        }
