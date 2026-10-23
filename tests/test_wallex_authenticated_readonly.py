"""Offline tests for opt-in authenticated, read-only Wallex account tools."""
from __future__ import annotations

import asyncio
import json
from unittest.mock import MagicMock

import pytest

from wallex_mcp.config import (
    BALANCES_PATH,
    DEFAULT_ALLOWLIST,
    OPEN_ORDERS_PATH,
    WALLEX_OFFICIAL_HOST,
    EndpointAllowlist,
)
from wallex_mcp.server import create_server
from wallex_mcp.wallex_client import WallexAPIError, WallexClient, WallexClientError


class FakeTransport:
    def __init__(self, payload, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.calls = []

    def Client(self, timeout=None):
        self.timeout = timeout
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def request(self, method, url, headers=None, **kwargs):
        self.calls.append({"method": method, "url": url, "headers": dict(headers or {})})
        response = MagicMock()
        response.status_code = self.status_code
        response.content = json.dumps(self.payload).encode()
        return response


def test_default_server_is_public_only():
    server = create_server(api_key="synthetic-not-a-real-key")
    names = {tool.name for tool in asyncio.run(server.list_tools())}
    assert names == {"wallex_get_markets"}


def test_account_tools_require_key_and_explicit_authenticated_allowlist():
    no_key_server = create_server(allowlist=EndpointAllowlist.authenticated_readonly())
    no_key_names = {tool.name for tool in asyncio.run(no_key_server.list_tools())}
    assert no_key_names == {"wallex_get_markets"}

    enabled_server = create_server(
        api_key="synthetic-not-a-real-key",
        allowlist=EndpointAllowlist.authenticated_readonly(),
    )
    enabled_names = {tool.name for tool in asyncio.run(enabled_server.list_tools())}
    assert enabled_names == {
        "wallex_get_markets",
        "wallex_get_balances",
        "wallex_get_open_orders",
    }


@pytest.mark.parametrize(
    ("path", "payload", "method_name"),
    [
        (
            BALANCES_PATH,
            {"success": True, "message": "ok", "result": {"balances": {"USDT": {"value": "2.5"}}}},
            "get_balances",
        ),
        (
            OPEN_ORDERS_PATH,
            {"success": True, "message": "ok", "result": {"USDTTMN": []}},
            "get_open_orders",
        ),
    ],
)
def test_authenticated_gets_send_api_key_only_to_allowlisted_private_paths(path, payload, method_name):
    transport = FakeTransport(payload)
    client = WallexClient(
        allowlist=EndpointAllowlist.authenticated_readonly(),
        api_key="synthetic-not-a-real-key",
        transport=transport,
        max_retries=0,
        backoff_seconds=0,
    )
    result = getattr(client, method_name)()
    assert result["success"] is True
    assert len(transport.calls) == 1
    call = transport.calls[0]
    assert call["url"] == f"https://{WALLEX_OFFICIAL_HOST}{path}"
    assert call["headers"].get("x-api-key") == "synthetic-not-a-real-key"


def test_private_endpoint_fails_closed_without_key_before_network():
    transport = FakeTransport({"success": True, "result": {"balances": {}}})
    client = WallexClient(
        allowlist=EndpointAllowlist.authenticated_readonly(),
        transport=transport,
        max_retries=0,
    )
    with pytest.raises(WallexClientError, match="requires an API key"):
        client.get_balances()
    assert transport.calls == []


def test_account_response_envelope_must_be_valid():
    transport = FakeTransport({"success": False, "result": {"balances": {}}})
    client = WallexClient(
        allowlist=EndpointAllowlist.authenticated_readonly(),
        api_key="synthetic-not-a-real-key",
        transport=transport,
        max_retries=0,
    )
    with pytest.raises(WallexAPIError):
        client.get_balances()
