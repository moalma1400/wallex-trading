"""Test suite for the standalone Wallex MCP server."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from wallex_mcp import (
    DEFAULT_ALLOWLIST,
    EndpointNotAllowedError,
    EndpointAllowlist,
    EndpointAllowlistEntry,
    MarketsResponseModel,
    ResponseTooLargeError,
    SYNTHETIC_SECRET,
    WallexAPIError,
    WallexClient,
    WallexClientError,
    decimal_value,
    redact_for_log,
)
from wallex_mcp.config import (
    DEFAULT_BACKOFF_SECONDS,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_RESPONSE_BYTES,
    DEFAULT_TIMEOUT_SECONDS,
    WALLEX_OFFICIAL_HOST,
    MARKETS_PATH,
)
from wallex_mcp.server import create_server
from wallex_mcp.schemas import FairPriceModel, MarketMetadataModel
from wallex_mcp.redaction import assert_no_secret

FIXTURES = Path(__file__).resolve().parent / "fixtures"
STANDALONE_MARKETS = json.loads(
    (FIXTURES / "standalone_markets_response.json").read_text(encoding="utf-8")
)