"""Standalone read-only CoinGecko MCP server using Streamable HTTP."""

from __future__ import annotations

import logging
import os
import sys
from typing import Any

from mcp.server import MCPServer

from .client import CoinGeckoClient, CoinGeckoError

logger = logging.getLogger("coingecko_mcp.server")


def configure_logging() -> None:
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s")
    )
    root = logging.getLogger()
    if not root.handlers:
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def create_server(client: CoinGeckoClient | None = None) -> MCPServer:
    server = MCPServer("coingecko-readonly-mcp")
    api = client or CoinGeckoClient()

    @server.tool()
    def coingecko_search_coins(query: str) -> dict[str, Any]:
        """Search CoinGecko for coins by name or symbol; returns candidate IDs."""
        try:
            return api.search_coins(query)
        except CoinGeckoError:
            logger.warning("CoinGecko search request failed")
            raise

    @server.tool()
    def coingecko_get_price(
        ids: str, vs_currencies: str = "usd"
    ) -> dict[str, Any]:
        """Get spot prices and 24-hour changes for comma-separated CoinGecko IDs."""
        try:
            return api.get_price(ids, vs_currencies)
        except CoinGeckoError:
            logger.warning("CoinGecko price request failed")
            raise

    @server.tool()
    def coingecko_get_markets(
        vs_currency: str = "usd", per_page: int = 10, page: int = 1
    ) -> dict[str, Any]:
        """Get market-cap-ranked coin market data; maximum 50 results per call."""
        try:
            return api.get_markets(vs_currency, per_page, page)
        except CoinGeckoError:
            logger.warning("CoinGecko markets request failed")
            raise

    return server


def main() -> int:
    configure_logging()
    server = create_server()
    host = os.getenv("COINGECKO_MCP_HOST", "127.0.0.1")
    port_text = os.getenv("COINGECKO_MCP_PORT", "8001")
    path = os.getenv("COINGECKO_MCP_PATH", "/mcp")

    try:
        port = int(port_text)
        if not 1 <= port <= 65535:
            raise ValueError
        if not path.startswith("/") or "?" in path or "#" in path:
            raise ValueError
    except ValueError:
        logger.error("Invalid MCP port or path configuration")
        return 2

    logger.info("Starting CoinGecko MCP on %s:%d%s", host, port, path)
    try:
        server.run(
            transport="streamable-http",
            host=host,
            port=port,
            streamable_http_path=path,
        )
    except Exception:
        logger.exception("CoinGecko MCP server stopped")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
