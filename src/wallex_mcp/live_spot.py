"""Opt-in live Spot order client for the repository-owned MCP server.

This module is independent of Smart98. It talks only to fixed official Wallex
paths, requires explicit operator environment gates and never retries a write.
"""
from __future__ import annotations

import json
import os
import re
import uuid
from dataclasses import dataclass, field
from decimal import Decimal, InvalidOperation
from typing import Any, Mapping, Optional
from urllib.parse import quote

WALLEX_HOST = "api.wallex.ir"
ORDER_CREATE_PATH = "/v1/account/orders"
ORDER_DETAIL_PATH = "/v1/account/orders/{client_id}"
LIVE_ACK_VALUE = "I_UNDERSTAND_REAL_ORDERS"

_SYMBOL = re.compile(r"^[A-Z0-9]{2,32}$")
_CLIENT_ID = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
_DECIMAL = re.compile(r"^[0-9]+(?:\.[0-9]+)?$")


class LiveSpotError(RuntimeError):
    """Base error for opt-in live Spot execution."""


class LiveSpotConfigurationError(LiveSpotError):
    """Required live-trading configuration is absent or invalid."""


class OrderOutcomeUnknown(LiveSpotError):
    """A write might have reached Wallex; reconcile using client_id before retrying."""


class LiveSpotAPIError(LiveSpotError):
    """Wallex definitively returned a non-success HTTP response."""


def _positive_decimal(value: Any, field_name: str) -> Decimal:
    if not isinstance(value, (str, int, Decimal)) or isinstance(value, bool):
        raise LiveSpotError(f"{field_name} must be supplied as a decimal string")
    text = str(value)
    if not _DECIMAL.fullmatch(text):
        raise LiveSpotError(f"{field_name} must be a plain positive decimal")
    try:
        result = Decimal(text)
    except InvalidOperation as exc:
        raise LiveSpotError(f"{field_name} must be a valid decimal") from exc
    if not result.is_finite() or result <= 0:
        raise LiveSpotError(f"{field_name} must be greater than zero")
    return result


@dataclass(frozen=True)
class LiveSpotConfig:
    """Explicit live-trading gates and hard operator-set limits."""

    api_key: str = field(repr=False)
    allowed_symbols: frozenset[str]
    quote_asset: str
    max_order_notional: Decimal
    fee_buffer_bps: int = 100
    timeout_seconds: float = 8.0
    max_response_bytes: int = 1024 * 1024

    def __post_init__(self) -> None:
        if not self.api_key.strip():
            raise LiveSpotConfigurationError("WALLEX_API_KEY is required for live trading")
        symbols = frozenset(item.strip().upper() for item in self.allowed_symbols)
        if not symbols or any(not _SYMBOL.fullmatch(item) for item in symbols):
            raise LiveSpotConfigurationError("WALLEX_LIVE_ALLOWED_SYMBOLS must contain valid symbols")
        object.__setattr__(self, "allowed_symbols", symbols)
        quote_asset = self.quote_asset.strip().upper()
        if not _SYMBOL.fullmatch(quote_asset):
            raise LiveSpotConfigurationError("WALLEX_LIVE_QUOTE_ASSET must be a valid asset symbol")
        object.__setattr__(self, "quote_asset", quote_asset)
        amount = _positive_decimal(str(self.max_order_notional), "WALLEX_LIVE_MAX_ORDER_NOTIONAL")
        object.__setattr__(self, "max_order_notional", amount)
        if isinstance(self.fee_buffer_bps, bool) or not isinstance(self.fee_buffer_bps, int) or not 0 <= self.fee_buffer_bps <= 5000:
            raise LiveSpotConfigurationError("fee_buffer_bps must be an integer between 0 and 5000")
        if self.timeout_seconds <= 0 or self.max_response_bytes <= 0:
            raise LiveSpotConfigurationError("HTTP timeout and response limit must be positive")

    @classmethod
    def from_env(cls, environ: Optional[Mapping[str, str]] = None) -> Optional["LiveSpotConfig"]:
        """Return None by default; fail loudly if opt-in is incomplete."""
        env = os.environ if environ is None else environ
        if env.get("WALLEX_ENABLE_LIVE_TRADING", "").strip() != "1":
            return None
        if env.get("WALLEX_LIVE_TRADING_ACK", "").strip() != LIVE_ACK_VALUE:
            raise LiveSpotConfigurationError(
                "Live trading requires WALLEX_LIVE_TRADING_ACK=I_UNDERSTAND_REAL_ORDERS"
            )
        api_key = env.get("WALLEX_API_KEY", "").strip()
        symbols = frozenset(
            part.strip().upper()
            for part in env.get("WALLEX_LIVE_ALLOWED_SYMBOLS", "").split(",")
            if part.strip()
        )
        quote_asset = env.get("WALLEX_LIVE_QUOTE_ASSET", "").strip().upper()
        cap_raw = env.get("WALLEX_LIVE_MAX_ORDER_NOTIONAL", "").strip()
        if not api_key:
            raise LiveSpotConfigurationError("WALLEX_API_KEY is required when live trading is enabled")
        if not symbols:
            raise LiveSpotConfigurationError("WALLEX_LIVE_ALLOWED_SYMBOLS must be explicitly configured")
        if not quote_asset:
            raise LiveSpotConfigurationError("WALLEX_LIVE_QUOTE_ASSET must be explicitly configured")
        if not cap_raw:
            raise LiveSpotConfigurationError("WALLEX_LIVE_MAX_ORDER_NOTIONAL must be explicitly configured")
        fee_buffer_raw = env.get("WALLEX_LIVE_FEE_BUFFER_BPS", "100").strip()
        try:
            fee_buffer = int(fee_buffer_raw)
        except ValueError as exc:
            raise LiveSpotConfigurationError("WALLEX_LIVE_FEE_BUFFER_BPS must be an integer") from exc
        return cls(
            api_key=api_key,
            allowed_symbols=symbols,
            quote_asset=quote_asset,
            max_order_notional=_positive_decimal(cap_raw, "WALLEX_LIVE_MAX_ORDER_NOTIONAL"),
            fee_buffer_bps=fee_buffer,
        )


class LiveSpotClient:
    """Direct, fixed-host API client used only behind opt-in MCP tools.

    The POST path is attempted exactly once. A timeout, transport exception,
    server-side error, or malformed response becomes OrderOutcomeUnknown and
    must be reconciled using the same client_id before any replacement order.
    """

    def __init__(self, config: LiveSpotConfig, *, transport: Any = None) -> None:
        self._config = config
        self._transport = transport

    @staticmethod
    def _validate_client_id(client_id: str) -> str:
        if not isinstance(client_id, str) or not _CLIENT_ID.fullmatch(client_id):
            raise LiveSpotError("client_id must contain 1-64 letters, digits, underscores or hyphens")
        return client_id

    @staticmethod
    def _free_balance(balances_response: Mapping[str, Any], asset: str) -> Decimal:
        result = balances_response.get("result")
        balances = result.get("balances") if isinstance(result, Mapping) else None
        if balances_response.get("success") is not True or not isinstance(balances, Mapping):
            raise LiveSpotError("Balance response is not a verified success/result/balances envelope")
        item = balances.get(asset)
        if not isinstance(item, Mapping):
            return Decimal("0")
        try:
            total = _positive_decimal(str(item.get("value", "0")), f"{asset} balance")
        except LiveSpotError:
            # A zero balance is valid; negative, non-finite or malformed values are not.
            raw = str(item.get("value", "0"))
            if raw == "0":
                total = Decimal("0")
            else:
                raise
        locked_raw = str(item.get("locked", "0"))
        if not _DECIMAL.fullmatch(locked_raw) and locked_raw != "0":
            raise LiveSpotError(f"{asset} locked balance is malformed")
        locked = Decimal(locked_raw)
        if not locked.is_finite() or locked < 0 or locked > total:
            raise LiveSpotError(f"{asset} balance/locked amounts are inconsistent")
        return total - locked

    def _request(self, method: str, path: str, *, body: Optional[Mapping[str, Any]] = None,
                 client_id: Optional[str] = None) -> dict[str, Any]:
        if path != ORDER_CREATE_PATH and not (
            path.startswith("/v1/account/orders/") and path.count("/") == 4
        ):
            raise LiveSpotError("Blocked path: endpoint is not in the fixed live Spot allowlist")
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "x-api-key": self._config.api_key,
        }
        transport = self._transport
        if transport is None:
            try:
                import httpx
            except ImportError as exc:  # pragma: no cover
                raise LiveSpotError("httpx is unavailable") from exc
            transport = httpx

        # Never retry. For POST, any transport ambiguity is a possible accepted order.
        try:
            with transport.Client(timeout=self._config.timeout_seconds) as session:
                response = session.request(method, f"https://{WALLEX_HOST}{path}",
                                           headers=headers, json=body)
        except Exception:
            if method == "POST":
                safe_id = client_id or "not-generated"
                raise OrderOutcomeUnknown(
                    f"Order outcome unknown for client_id={safe_id}; reconcile before any retry"
                ) from None
            raise LiveSpotError("Wallex read request failed; no retry was attempted") from None

        status = int(response.status_code)
        if method == "POST" and status >= 500:
            raise OrderOutcomeUnknown(
                f"Order outcome unknown for client_id={client_id}; HTTP {status}; reconcile before any retry"
            )
        if status >= 400:
            raise LiveSpotAPIError(f"Wallex returned HTTP {status} for {method} request")
        raw = response.content
        if len(raw) > self._config.max_response_bytes:
            if method == "POST":
                raise OrderOutcomeUnknown(
                    f"Order outcome unknown for client_id={client_id}; response exceeded size limit"
                )
            raise LiveSpotError("Wallex response exceeded the configured size limit")
        try:
            decoded = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            if method == "POST":
                raise OrderOutcomeUnknown(
                    f"Order outcome unknown for client_id={client_id}; response was not valid JSON"
                ) from None
            raise LiveSpotError("Wallex response was not valid UTF-8 JSON") from None
        if not isinstance(decoded, dict):
            if method == "POST":
                raise OrderOutcomeUnknown(
                    f"Order outcome unknown for client_id={client_id}; response was not a JSON object"
                )
            raise LiveSpotError("Wallex response must be a JSON object")
        return decoded

    def get_order(self, client_id: str) -> dict[str, Any]:
        """Read order status by its client order ID for reconciliation."""
        client_id = self._validate_client_id(client_id)
        response = self._request("GET", ORDER_DETAIL_PATH.format(client_id=quote(client_id, safe="")))
        if response.get("success") is not True or not isinstance(response.get("result"), dict):
            raise LiveSpotError("Order detail response did not contain success=true and an object result")
        return response

    def place_limit_order(
        self, *, symbol: str, side: str, quantity: str, price: str,
        market: Mapping[str, Any], balances_response: Mapping[str, Any],
        client_id: Optional[str] = None,
    ) -> dict[str, Any]:
        """Validate one Spot LIMIT order, submit exactly once, and return its response."""
        symbol = symbol.strip().upper() if isinstance(symbol, str) else ""
        side = side.strip().upper() if isinstance(side, str) else ""
        if not _SYMBOL.fullmatch(symbol) or symbol not in self._config.allowed_symbols:
            raise LiveSpotError("symbol is invalid or not in WALLEX_LIVE_ALLOWED_SYMBOLS")
        if side not in {"BUY", "SELL"}:
            raise LiveSpotError("side must be BUY or SELL")
        if not isinstance(market, Mapping) or market.get("symbol") != symbol:
            raise LiveSpotError("current market metadata for the requested symbol is missing")
        if market.get("is_spot") is not True:
            raise LiveSpotError("symbol is not explicitly marked is_spot=true")
        base_asset = market.get("base_asset")
        quote_asset = market.get("quote_asset")
        if not isinstance(base_asset, str) or not isinstance(quote_asset, str):
            raise LiveSpotError("market metadata is missing base_asset or quote_asset")
        if quote_asset.upper() != self._config.quote_asset:
            raise LiveSpotError("market quote asset differs from the configured quote asset")
        amount_precision = market.get("amount_precision")
        price_precision = market.get("price_precision")
        for name, val in (("amount_precision", amount_precision), ("price_precision", price_precision)):
            if isinstance(val, bool) or not isinstance(val, int) or val < 0:
                raise LiveSpotError(f"market metadata has invalid {name}")

        qty = _positive_decimal(quantity, "quantity")
        limit_price = _positive_decimal(price, "price")
        if len(str(quantity).partition(".")[2]) > amount_precision:
            raise LiveSpotError(f"quantity exceeds market precision ({amount_precision})")
        if len(str(price).partition(".")[2]) > price_precision:
            raise LiveSpotError(f"price exceeds market precision ({price_precision})")
        notional = qty * limit_price
        if notional > self._config.max_order_notional:
            raise LiveSpotError("order notional exceeds WALLEX_LIVE_MAX_ORDER_NOTIONAL")

        free_quote = self._free_balance(balances_response, self._config.quote_asset)
        free_base = self._free_balance(balances_response, base_asset.upper())
        if side == "BUY":
            required_quote = notional * (Decimal("1") + Decimal(self._config.fee_buffer_bps) / Decimal("10000"))
            if required_quote > free_quote:
                raise LiveSpotError("insufficient available quote balance after configured fee buffer")
        elif qty > free_base:
            raise LiveSpotError("insufficient available base-asset balance")

        effective_client_id = self._validate_client_id(client_id) if client_id else f"wallex-{uuid.uuid4().hex}"
        body = {
            "client_id": effective_client_id,
            "symbol": symbol,
            "side": side,
            "type": "LIMIT",
            "quantity": format(qty, "f"),
            "price": format(limit_price, "f"),
        }
        response = self._request(
            "POST", ORDER_CREATE_PATH, body=body, client_id=effective_client_id
        )
        if response.get("success") is not True or not isinstance(response.get("result"), dict):
            raise OrderOutcomeUnknown(
                f"Order outcome unknown for client_id={effective_client_id}; reconcile before any retry"
            )
        order = response["result"]
        returned_id = order.get("clientOrderId")
        if returned_id is not None and str(returned_id) != effective_client_id:
            raise OrderOutcomeUnknown(
                f"Order response ID mismatch for client_id={effective_client_id}; reconcile before any retry"
            )
        return response
