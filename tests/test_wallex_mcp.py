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


class FakeTransport:
    """Minimal stand-in for an httpx.Client that returns canned responses."""

    def __init__(self, responses, status_codes=None):
        self._responses = list(responses)
        self._status_codes = list(status_codes) if status_codes else None
        self.calls = []
        self._index = 0

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def request(self, method, url, headers=None, **kwargs):
        self.calls.append({"method": method, "url": url, "headers": headers})
        if self._index >= len(self._responses):
            raise AssertionError("FakeTransport ran out of canned responses")
        body = self._responses[self._index]
        status = 200
        if self._status_codes and self._index < len(self._status_codes):
            status = self._status_codes[self._index]
        self._index += 1
        response = MagicMock()
        response.status_code = status
        response.content = body if isinstance(body, bytes) else body.encode("utf-8")
        return response


def make_client(transport, api_key=None, allowlist=None):
    return WallexClient(
        allowlist=allowlist or DEFAULT_ALLOWLIST,
        timeout_seconds=DEFAULT_TIMEOUT_SECONDS,
        max_response_bytes=DEFAULT_MAX_RESPONSE_BYTES,
        max_retries=DEFAULT_MAX_RETRIES,
        backoff_seconds=DEFAULT_BACKOFF_SECONDS,
        api_key=api_key,
        transport=transport,
    )


def markets_bytes(payload=None):
    payload = payload if payload is not None else STANDALONE_MARKETS
    return json.dumps(payload).encode("utf-8")


def success_envelope(payload=None):
    payload = payload if payload is not None else STANDALONE_MARKETS
    return {"markets": payload["markets"], "message": "ok", "success": True}


class TestEndpointAllowlist:
    def test_default_allowlist_contains_only_markets(self):
        assert DEFAULT_ALLOWLIST.is_allowed("GET", WALLEX_OFFICIAL_HOST, MARKETS_PATH)
        assert not DEFAULT_ALLOWLIST.is_allowed(
            "GET", WALLEX_OFFICIAL_HOST, "/hector/web/v1/depth"
        )
        assert not DEFAULT_ALLOWLIST.is_allowed("GET", "evil.example", MARKETS_PATH)
        assert not DEFAULT_ALLOWLIST.is_allowed("POST", WALLEX_OFFICIAL_HOST, MARKETS_PATH)

    def test_default_markets_does_not_require_key(self):
        assert DEFAULT_ALLOWLIST.requires_key("GET", WALLEX_OFFICIAL_HOST, MARKETS_PATH) is False

    def test_non_get_methods_are_rejected_at_construction(self):
        with pytest.raises(ValueError):
            EndpointAllowlist(
                entries=(
                    EndpointAllowlistEntry(
                        method="POST",
                        host=WALLEX_OFFICIAL_HOST,
                        path=MARKETS_PATH,
                    ),
                )
            )

    def test_immutable_allowlist(self):
        allowlist = EndpointAllowlist.default()
        with pytest.raises(Exception):
            allowlist.entries = ()


class TestConfigConstants:
    def test_safe_operational_bounds(self):
        assert DEFAULT_TIMEOUT_SECONDS == 10.0
        assert DEFAULT_MAX_RESPONSE_BYTES == 5 * 1024 * 1024
        assert DEFAULT_MAX_RETRIES == 2
        assert DEFAULT_BACKOFF_SECONDS == 0.5

    def test_official_host_and_path(self):
        assert WALLEX_OFFICIAL_HOST == "api.wallex.ir"
        assert MARKETS_PATH == "/hector/web/v1/markets"