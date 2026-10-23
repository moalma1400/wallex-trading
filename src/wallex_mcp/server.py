"""Standalone Wallex MCP server.

This is a repository-owned Model Context Protocol server. It speaks MCP
over stdio: protocol messages on stdout, diagnostics on stderr. It exposes
one verified public tool, ``wallex_get_markets``, backed by the officially
documented endpoint ``GET https://api.wallex.ir/hector/web/v1/markets``.

Run with::

    python -m wallex_mcp.server

The server is intentionally minimal. It accesses only explicitly
allowlisted Wallex endpoints and fails closed on any unexpected schema,
error, or unverified capability.
"""

from __future__ import annotations

import logging
import os
import sys
from typing import Any, Optional

from mcp.server import MCPServer
from mcp.server.stdio import stdio_server

from .config import (
    DEFAULT_ALLOWLIST,
    DEFAULT_BACKOFF_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    BALANCES_PATH,
    OPEN_ORDERS_PATH,
    WALLEX_OFFICIAL_HOST,
    EndpointAllowlist,
)
from .redaction import redact_for_log
from .schemas import MarketsResponseModel
from .wallex_client import WallexClient, WallexClientError
from .live_spot import (
    LiveSpotClient,
    LiveSpotConfig,
    LiveSpotError,
    OrderOutcomeUnknown,
)

logger = logging.getLogger("wallex_mcp.server")


def _configure_logging() -> None:
    """Send all diagnostics to stderr so stdout stays a clean protocol stream."""
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    # Never let library noise reach stdout.
    for noisy in ("httpx", "httpcore", "mcp.server"):
        logging.getLogger(noisy).setLevel(logging.WARNING)


def _build_client(
    api_key: Optional[str] = None,
    allowlist: Optional[EndpointAllowlist] = None,
) -> WallexClient:
    return WallexClient(
        allowlist=allowlist or DEFAULT_ALLOWLIST,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes=DEFAULT_MAX_RESPONSE_BYTES,
        max_retries=DEFAULT_MAX_RETRIES,
        backoff_seconds=DEFAULT_BACKOFF_SECONDS,
        api_key=api_key,
    )


def create_server(
    api_key: Optional[str] = None,
    allowlist: Optional[EndpointAllowlist] = None,
    live_config: Optional[LiveSpotConfig] = None,
) -> MCPServer:
    """Construct the MCP server with its registered tools.

    ``api_key`` is optional and is only consumed for endpoints whose
    allowlist entry marks ``requires_key=True``. The default allowlist
    contains only the public markets endpoint, which does not require a
    key, so the default server makes no authenticated requests.
    """
    server = MCPServer("wallex-standalone-mcp")
    client = _build_client(api_key=api_key, allowlist=allowlist)

    @server.tool()
    def wallex_get_markets() -> dict[str, Any]:
        """Return the verified public Spot market metadata list from Wallex.

        This tool calls the officially documented public endpoint
        ``GET https://api.wallex.ir/hector/web/v1/markets`` and returns a
        normalized, Decimal-safe market list. No API key is required or
        sent for this public endpoint.

        Returns:
            A dict with ``markets`` (non-empty list), ``message`` and
            ``success`` fields. Each market entry preserves the official
            field names exactly.
        """
        logger.info("wallex_get_markets invoked")
        try:
            response = client.get_markets()
        except WallexClientError as exc:
            logger.error("wallex_get_markets failed: %s", redact_for_log(str(exc)))
            raise
        logger.info(
            "wallex_get_markets returned %d markets", len(response.markets)
        )
        return response.model_dump(mode="json")

    account_reads_enabled = bool(
        api_key
        and (allowlist or DEFAULT_ALLOWLIST).is_allowed("GET", WALLEX_OFFICIAL_HOST, BALANCES_PATH)
        and (allowlist or DEFAULT_ALLOWLIST).is_allowed("GET", WALLEX_OFFICIAL_HOST, OPEN_ORDERS_PATH)
    )
    if account_reads_enabled:
        @server.tool()
        def wallex_get_balances() -> dict[str, Any]:
            """Read main-account balances; explicit read-only mode only."""
            logger.info("wallex_get_balances invoked")
            try:
                result = client.get_balances()
            except WallexClientError as exc:
                logger.error("wallex_get_balances failed: %s", redact_for_log(str(exc)))
                raise
            logger.info("wallex_get_balances completed")
            return result

        @server.tool()
        def wallex_get_open_orders() -> dict[str, Any]:
            """Read active orders; explicit read-only mode only."""
            logger.info("wallex_get_open_orders invoked")
            try:
                result = client.get_open_orders()
            except WallexClientError as exc:
                logger.error("wallex_get_open_orders failed: %s", redact_for_log(str(exc)))
                raise
            logger.info("wallex_get_open_orders completed")
            return result
    else:
        logger.info("Authenticated account tools disabled; public-only mode")

    if live_config is not None:
        if not api_key or api_key != live_config.api_key:
            raise ValueError("Live Spot tools require the same explicitly configured API key")
        live_client = LiveSpotClient(live_config)

        @server.tool()
        def wallex_live_place_limit_order(
            symbol: str, side: str, quantity: str, price: str, client_id: str = ""
        ) -> dict[str, Any]:
            """Place one real Spot LIMIT order after live market/balance preflight.

            Only available when WALLEX_ENABLE_LIVE_TRADING=1 and the explicit
            operator acknowledgment and hard limits are configured. The call
            submits at most once. If outcome is ambiguous, reconcile by client_id;
            never retry the POST.
            """
            try:
                raw_markets = client._request("GET", WALLEX_OFFICIAL_HOST, "/hector/web/v1/markets")
                if raw_markets.get("success") is not True:
                    raise LiveSpotError("Public markets response did not report success=true")
                markets = raw_markets.get("markets")
                if not isinstance(markets, list):
                    result = raw_markets.get("result")
                    markets = result.get("markets") if isinstance(result, dict) else None
                if not isinstance(markets, list):
                    raise LiveSpotError("Public markets response has no markets array")
                market = next(
                    (item for item in markets if isinstance(item, dict) and item.get("symbol") == symbol.strip().upper()),
                    None,
                )
                if market is None:
                    raise LiveSpotError("Requested symbol was not found in current public market metadata")
                balances = client.get_balances()
                result = live_client.place_limit_order(
                    symbol=symbol, side=side, quantity=quantity, price=price,
                    market=market, balances_response=balances,
                    client_id=client_id or None,
                )
                logger.info("Live Spot order submitted; client_id=%s", result.get("result", {}).get("clientOrderId", client_id or "generated"))
                return result
            except OrderOutcomeUnknown:
                logger.error("Live Spot order outcome is unknown; do not resubmit without reconciliation")
                raise
            except (LiveSpotError, WallexClientError) as exc:
                logger.warning("Live Spot order blocked/failed: %s", redact_for_log(str(exc)))
                raise

        @server.tool()
        def wallex_live_get_order(client_id: str) -> dict[str, Any]:
            """Read one Spot order by client ID; use to reconcile ambiguous submissions."""
            try:
                return live_client.get_order(client_id)
            except LiveSpotError as exc:
                logger.warning("Live Spot order lookup failed: %s", redact_for_log(str(exc)))
                raise

    return server


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for the module command."""
    _configure_logging()
    api_key = os.environ.get("WALLEX_API_KEY")
    readonly_enabled = os.environ.get("WALLEX_ENABLE_ACCOUNT_READONLY", "").strip() == "1"
    live_config = LiveSpotConfig.from_env()
    if (readonly_enabled or live_config is not None) and api_key:
        server = create_server(
            api_key=api_key,
            allowlist=EndpointAllowlist.authenticated_readonly(),
            live_config=live_config,
        )
    else:
        if readonly_enabled and not api_key:
            logger.warning("Account read-only mode requested without WALLEX_API_KEY; public-only mode")
        server = create_server()
    try:
        server.run(transport="stdio")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("MCP server terminated: %s", redact_for_log(str(exc)))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())