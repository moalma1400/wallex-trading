"""Test suite for the standalone Wallex MCP server.

All tests are fully offline: no real Wallex network traffic is performed.
HTTP is mocked through an injectable transport hook on WallexClient, and
the protocol-level tests run the actual MCP SDK server and client over
in-memory stdio pipes.
"""

from __future__ import annotations

import asyncio
import io
import json
import logging
import os
import re
import sys
from contextlib import asynccontextmanager
from decimal import Decimal
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client
from mcp.server import MCPServer
from mcp.server.stdio import stdio_server
from mcp import types

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