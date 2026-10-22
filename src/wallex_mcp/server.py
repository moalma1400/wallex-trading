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
    EndpointAllowlist,
)
from .redaction import redact_for_log
from .schemas import MarketsResponseModel
from .wallex_client import WallexClient, WallexClientError

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

    return server


def main(argv: Optional[list[str]] = None) -> int:
    """Entry point for ``python -m wallex_mcp.server``."""
    _configure_logging()
    server = create_server()
    try:
        server.run(transport="stdio")
    except Exception as exc:  # pragma: no cover - defensive
        logger.error("MCP server terminated: %s", redact_for_log(str(exc)))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())