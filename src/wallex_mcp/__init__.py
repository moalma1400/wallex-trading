"""Standalone Wallex MCP server package.

This package implements a repository-owned Model Context Protocol server
for verified public, read-only Wallex Spot market data. It is an
independent alternative to Smart98 mediation (constitution v1.3.0,
Feature 007) and does not depend on Smart98 being running.
"""

from __future__ import annotations

from .config import (
    DEFAULT_ALLOWLIST,
    DEFAULT_BACKOFF_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    EndpointAllowlist,
    EndpointAllowlistEntry,
    WALLEX_OFFICIAL_HOST,
    MARKETS_PATH,
)
from .redaction import SYNTHETIC_SECRET, redact_for_log
from .live_spot import (
    LIVE_ACK_VALUE,
    LiveSpotClient,
    LiveSpotConfig,
    LiveSpotConfigurationError,
    LiveSpotError,
    LiveSpotAPIError,
    OrderOutcomeUnknown,
)
from .schemas import (
    FairPriceModel,
    MarketsResponseModel,
    MarketMetadataModel,
    decimal_value,
)
from .wallex_client import (
    EndpointNotAllowedError,
    ResponseTooLargeError,
    WallexClient,
    WallexClientError,
    WallexAPIError,
)

__all__ = [
    "DEFAULT_ALLOWLIST",
    "DEFAULT_BACKOFF_SECONDS",
    "DEFAULT_MAX_RETRIES",
    "DEFAULT_MAX_RESPONSE_BYTES",
    "DEFAULT_TIMEOUT_SECONDS",
    "EndpointAllowlist",
    "EndpointAllowlistEntry",
    "WALLEX_OFFICIAL_HOST",
    "MARKETS_PATH",
    "FairPriceModel",
    "MarketsResponseModel",
    "MarketMetadataModel",
    "decimal_value",
    "WallexClient",
    "WallexClientError",
    "WallexAPIError",
    "EndpointNotAllowedError",
    "ResponseTooLargeError",
    "redact_for_log",
    "SYNTHETIC_SECRET",
    "LIVE_ACK_VALUE",
    "LiveSpotClient",
    "LiveSpotConfig",
    "LiveSpotConfigurationError",
    "LiveSpotError",
    "LiveSpotAPIError",
    "OrderOutcomeUnknown",
]