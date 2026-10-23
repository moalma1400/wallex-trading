"""Offline tests for the standalone Wallex MCP server.

All HTTP is served by an injected fake transport. The stdio protocol smoke
test only initializes the MCP session and lists tools; it never calls the
Wallex-backed tool and therefore performs no network requests.
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
from pathlib import Path
import subprocess
import sys
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from wallex_mcp import (
    DEFAULT_ALLOWLIST,
    EndpointAllowlist,
    EndpointAllowlistEntry,
    EndpointNotAllowedError,
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
    MARKETS_PATH,
    WALLEX_OFFICIAL_HOST,
)
from wallex_mcp.redaction import assert_no_secret
from wallex_mcp.schemas import FairPriceModel, MarketMetadataModel
from wallex_mcp.server import create_server

FIXTURES = Path(__file__).resolve().parent / "fixtures"
MARKETS_FIXTURE = json.loads(
    (FIXTURES / "standalone_markets_response.json").read_text(encoding="utf-8")
)


class FakeTransport:
    """Small httpx-compatible transport; it never opens a socket."""

    def __init__(self, responses=(), status_codes=None):
        self.responses = list(responses)
        self.status_codes = list(status_codes or [])
        self.calls = []
        self.index = 0

    def Client(self, timeout=None):
        self.timeout = timeout
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def request(self, method, url, headers=None, **kwargs):
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {})})
        if self.index >= len(self.responses):
            raise AssertionError("FakeTransport ran out of canned responses")
        item = self.responses[self.index]
        status = self.status_codes[self.index] if self.index < len(self.status_codes) else 200
        self.index += 1
        if isinstance(item, BaseException):
            raise item
        response = MagicMock()
        response.status_code = status
        response.content = item if isinstance(item, bytes) else str(item).encode("utf-8")
        return response


def client_for(transport, *, api_key=None, allowlist=None, retries=0, max_bytes=None):
    return WallexClient(
        allowlist=allowlist or DEFAULT_ALLOWLIST,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes=max_bytes or DEFAULT_MAX_RESPONSE_BYTES,
        max_retries=retries,
        backoff_seconds=0,
        api_key=api_key,
        transport=transport,
    )


def encoded(payload):
    return json.dumps(payload).encode("utf-8")


class TestAllowlistAndConfiguration:
    def test_only_documented_public_markets_endpoint_is_allowed(self):
        assert DEFAULT_ALLOWLIST.is_allowed("GET", WALLEX_OFFICIAL_HOST, MARKETS_PATH)
        assert not DEFAULT_ALLOWLIST.is_allowed("GET", WALLEX_OFFICIAL_HOST, "/hector/web/v1/depth")
        assert not DEFAULT_ALLOWLIST.is_allowed("GET", "evil.example", MARKETS_PATH)
        assert not DEFAULT_ALLOWLIST.is_allowed("POST", WALLEX_OFFICIAL_HOST, MARKETS_PATH)

    def test_public_markets_endpoint_does_not_require_api_key(self):
        assert not DEFAULT_ALLOWLIST.requires_key("GET", WALLEX_OFFICIAL_HOST, MARKETS_PATH)

    def test_allowlist_rejects_non_get_and_is_immutable(self):
        with pytest.raises(ValueError):
            EndpointAllowlist(entries=(EndpointAllowlistEntry("POST", WALLEX_OFFICIAL_HOST, MARKETS_PATH),))
        allowlist = EndpointAllowlist.default()
        with pytest.raises((AttributeError, TypeError)):
            allowlist.entries = ()

    def test_operational_bounds_and_documented_path(self):
        assert DEFAULT_TIMEOUT_SECONDS == 10.0
        assert DEFAULT_MAX_RESPONSE_BYTES == 5 * 1024 * 1024
        assert DEFAULT_MAX_RETRIES == 2
        assert DEFAULT_BACKOFF_SECONDS == 0.5
        assert WALLEX_OFFICIAL_HOST == "api.wallex.ir"
        assert MARKETS_PATH == "/hector/web/v1/markets"


class TestSchemasAndClient:
    def test_fixture_normalizes_and_preserves_decimal_strings(self):
        result = MarketsResponseModel.model_validate(MARKETS_FIXTURE)
        assert result.success is True
        assert len(result.markets) == 3
        assert result.markets[0].symbol == "USDTTMN"
        assert decimal_value(result.markets[0].price) == decimal_value("271622")
        assert result.markets[0].fair_price.ask == "271608.14"

    def test_invalid_schema_numeric_and_malformed_json_fail_closed(self):
        with pytest.raises(ValidationError):
            MarketMetadataModel.model_validate({"symbol": "BTC"})
        with pytest.raises(ValidationError):
            FairPriceModel(ask="NaN", bid="1")
        transport = FakeTransport([b"{not-json"])
        with pytest.raises(WallexClientError, match="valid UTF-8 JSON"):
            client_for(transport).get_markets()
        bad = json.loads(json.dumps(MARKETS_FIXTURE))
        bad["markets"][0]["price"] = "Infinity"
        with pytest.raises(ValidationError):
            MarketsResponseModel.model_validate(bad)

    def test_http_error_is_rejected_without_retry(self):
        transport = FakeTransport([encoded(MARKETS_FIXTURE)], status_codes=[503])
        with pytest.raises(WallexAPIError, match="HTTP 503"):
            client_for(transport, retries=2).get_markets()
        assert len(transport.calls) == 1

    def test_unsuccessful_response_envelope_is_rejected(self):
        payload = json.loads(json.dumps(MARKETS_FIXTURE))
        payload["success"] = False
        transport = FakeTransport([encoded(payload)])
        with pytest.raises(WallexAPIError, match="success=false"):
            client_for(transport).get_markets()

    def test_transient_transport_error_retries_then_succeeds(self):
        transport = FakeTransport([TimeoutError("synthetic timeout"), encoded(MARKETS_FIXTURE)])
        result = client_for(transport, retries=1).get_markets()
        assert result.success is True
        assert len(transport.calls) == 2

    def test_response_size_limit_is_enforced(self):
        transport = FakeTransport([encoded(MARKETS_FIXTURE)])
        with pytest.raises(ResponseTooLargeError):
            client_for(transport, max_bytes=8).get_markets()

    def test_allowlist_rejection_prevents_transport_call(self):
        transport = FakeTransport([encoded(MARKETS_FIXTURE)])
        client = client_for(transport)
        with pytest.raises(EndpointNotAllowedError):
            client._request("GET", WALLEX_OFFICIAL_HOST, "/hector/web/v1/depth")
        assert transport.calls == []

    def test_public_call_never_sends_configured_api_key(self):
        transport = FakeTransport([encoded(MARKETS_FIXTURE)])
        client_for(transport, api_key=SYNTHETIC_SECRET).get_markets()
        assert len(transport.calls) == 1
        assert "x-api-key" not in {k.lower() for k in transport.calls[0]["headers"]}
        assert transport.calls[0]["url"] == f"https://{WALLEX_OFFICIAL_HOST}{MARKETS_PATH}"

    def test_synthetic_secret_is_not_in_redacted_logs_or_errors(self, caplog):
        caplog.set_level(logging.DEBUG)
        text = redact_for_log(f"x-api-key: {SYNTHETIC_SECRET}")
        assert_no_secret(text, SYNTHETIC_SECRET)
        transport = FakeTransport([
            TimeoutError(f"failed with api_key={SYNTHETIC_SECRET}"),
            encoded(MARKETS_FIXTURE),
        ])
        result = client_for(transport, api_key=SYNTHETIC_SECRET, retries=1).get_markets()
        assert result.success is True
        assert len(transport.calls) == 2
        assert_no_secret(caplog.text, SYNTHETIC_SECRET)

    def test_adapter_keeps_standalone_source_compatible(self):
        from mcp_adapter import DataSource, MarketMeta
        assert DataSource.MCP_STANDALONE.name == "MCP_STANDALONE"
        assert DataSource.MCP_SMART98.name == "MCP_SMART98"
        assert MarketMeta.__dataclass_fields__["source"].default is DataSource.MCP_SMART98


def test_server_registers_only_read_only_markets_tool():
    # Inspect the SDK server's registered tool list without starting HTTP.
    server = create_server()
    async def list_tools():
        return await server.list_tools()
    tools = asyncio.run(list_tools())
    names = {tool.name for tool in tools}
    assert names == {"wallex_get_markets"}
    assert not any(any(word in name.lower() for word in ("order", "cancel", "withdraw", "transfer", "deposit")) for name in names)


def test_stdio_protocol_initializes_and_lists_tools_without_network():
    # Start the actual module as a child process. The test only initializes
    # the MCP session and lists tools; it deliberately does not call a tool.
    from mcp.client.session import ClientSession
    from mcp.client.stdio import StdioServerParameters, stdio_client

    async def smoke():
        params = StdioServerParameters(
            command=sys.executable,
            args=["-m", "wallex_mcp.server"],
            env={**os.environ, "PYTHONPATH": os.pathsep.join(["src", "."])},
        )
        async with stdio_client(params) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()
                return {tool.name for tool in result.tools}

    names = asyncio.run(smoke())
    assert names == {"wallex_get_markets"}


def test_default_allowlist_excludes_unverified_private_endpoints():
    from wallex_mcp.config import (
        BALANCES_PATH,
        DEFAULT_ALLOWLIST,
        MARKETS_PATH,
        OPEN_ORDERS_PATH,
        WALLEX_OFFICIAL_HOST,
    )

    assert DEFAULT_ALLOWLIST.is_allowed(
        "GET", WALLEX_OFFICIAL_HOST, MARKETS_PATH
    )
    assert not DEFAULT_ALLOWLIST.is_allowed(
        "GET", WALLEX_OFFICIAL_HOST, BALANCES_PATH
    )
    assert not DEFAULT_ALLOWLIST.is_allowed(
        "GET", WALLEX_OFFICIAL_HOST, OPEN_ORDERS_PATH
    )
    assert len(DEFAULT_ALLOWLIST.entries) == 1
