"""Offline tests: all HTTP requests use httpx.MockTransport."""

import json

import httpx
import pytest

from coingecko_mcp.client import (
    DEFAULT_BASE_URL,
    PRO_BASE_URL,
    CoinGeckoClient,
    CoinGeckoError,
    CoinGeckoInputError,
    CoinGeckoResponseError,
)
from coingecko_mcp.server import create_server


def response(payload, status=200):
    return httpx.Response(
        status,
        json=payload,
        request=httpx.Request("GET", "https://api.coingecko.com/api/v3/test"),
    )


def make_client(handler, **kwargs):
    transport = httpx.MockTransport(handler)
    return CoinGeckoClient(transport=transport, **kwargs)


def test_search_uses_fixed_official_endpoint_and_returns_coin_candidates():
    def handler(request):
        assert request.url.host == "api.coingecko.com"
        assert request.url.path == "/api/v3/search"
        assert request.url.params["query"] == "bitcoin"
        return response({"coins": [{"id": "bitcoin", "symbol": "btc"}]})

    result = make_client(handler).search_coins("bitcoin")
    assert result["coins"][0]["id"] == "bitcoin"
    assert result["count"] == 1


def test_price_sends_demo_key_in_header_not_query_string():
    secret = "synthetic-test-secret"

    def handler(request):
        assert request.url.path == "/api/v3/simple/price"
        assert request.headers["x-cg-demo-api-key"] == secret
        assert "synthetic-test-secret" not in str(request.url)
        assert request.url.params["ids"] == "bitcoin,ethereum"
        return response({"bitcoin": {"usd": 100}})

    result = make_client(handler, api_key=secret).get_price(
        "bitcoin,ethereum", "usd,eur"
    )
    assert result["bitcoin"]["usd"] == 100


def test_pro_key_uses_pro_header():
    def handler(request):
        assert request.url.host == "pro-api.coingecko.com"
        assert request.headers["x-cg-pro-api-key"] == "test-pro-key"
        return response({"bitcoin": {"usd": 100}})

    result = make_client(
        handler, base_url=PRO_BASE_URL, api_key="test-pro-key"
    ).get_price("bitcoin")
    assert "bitcoin" in result


def test_markets_endpoint_has_bounded_page_size():
    def handler(request):
        assert request.url.path == "/api/v3/coins/markets"
        assert request.url.params["per_page"] == "2"
        return response([{"id": "bitcoin"}, {"id": "ethereum"}])

    result = make_client(handler).get_markets(per_page=2)
    assert result["count"] == 2


@pytest.mark.parametrize("ids", ["", "bitcoin,,ethereum", "../secret", "x" * 101])
def test_invalid_coin_ids_rejected_before_network(ids):
    client = make_client(lambda request: pytest.fail("network must not be called"))
    with pytest.raises(CoinGeckoInputError):
        client.get_price(ids)


@pytest.mark.parametrize("per_page", [0, 51, -1])
def test_invalid_market_page_size_rejected(per_page):
    client = make_client(lambda request: pytest.fail("network must not be called"))
    with pytest.raises(CoinGeckoInputError):
        client.get_markets(per_page=per_page)


def test_unofficial_base_url_is_rejected():
    with pytest.raises(ValueError):
        CoinGeckoClient(base_url="https://attacker.example/api")


def test_http_errors_are_sanitized():
    client = make_client(lambda request: response({"private": "details"}, status=429))
    with pytest.raises(CoinGeckoError, match="HTTP 429") as exc:
        client.get_price("bitcoin")
    assert "private" not in str(exc.value)


def test_oversized_response_rejected():
    body = b'{"coins":[]}' + b" " * 100
    def handler(request):
        return httpx.Response(
            200,
            content=body,
            request=request,
            headers={"content-type": "application/json"},
        )

    client = make_client(handler, max_response_bytes=32)
    with pytest.raises(CoinGeckoResponseError, match="size limit"):
        client.search_coins("bitcoin")


def test_invalid_json_rejected():
    def handler(request):
        return httpx.Response(
            200,
            content=b"{not-json",
            request=request,
            headers={"content-type": "application/json"},
        )

    with pytest.raises(CoinGeckoResponseError, match="valid UTF-8 JSON"):
        make_client(handler).search_coins("bitcoin")


def test_server_registers_three_read_only_tools():
    import asyncio

    server = create_server(
        make_client(lambda request: response({}))
    )

    async def list_tools():
        return await server.list_tools()

    names = {tool.name for tool in asyncio.run(list_tools())}
    assert names == {
        "coingecko_search_coins",
        "coingecko_get_price",
        "coingecko_get_markets",
    }


def test_demo_key_read_from_coingecko_demo_api_key_env(monkeypatch):
    monkeypatch.setenv("COINGECKO_DEMO_API_KEY", "synthetic-demo-key")
    monkeypatch.delenv("COINGECKO_API_KEY", raising=False)

    def handler(request):
        assert request.headers["x-cg-demo-api-key"] == "synthetic-demo-key"
        assert "synthetic-demo-key" not in str(request.url)
        return response({"bitcoin": {"usd": 100}})

    client = make_client(handler)
    assert client.api_key_configured is True
    assert client.get_price("bitcoin")["bitcoin"]["usd"] == 100


def test_demo_env_takes_precedence_over_legacy_env(monkeypatch):
    monkeypatch.setenv("COINGECKO_DEMO_API_KEY", "demo-value")
    monkeypatch.setenv("COINGECKO_API_KEY", "legacy-value")
    client = CoinGeckoClient(transport=httpx.MockTransport(lambda r: response({})))
    assert client.api_key == "demo-value"


def test_repr_and_errors_never_leak_key(monkeypatch):
    secret = "synthetic-demo-key-never-print"
    monkeypatch.setenv("COINGECKO_DEMO_API_KEY", secret)
    client = make_client(lambda request: response({"e": secret}, status=500))
    assert secret not in repr(client)
    assert "api_key_configured=True" in repr(client)
    with pytest.raises(CoinGeckoError) as exc:
        client.get_price("bitcoin")
    assert secret not in str(exc.value)


def test_blank_env_key_means_no_auth_header(monkeypatch):
    monkeypatch.setenv("COINGECKO_DEMO_API_KEY", "   ")
    monkeypatch.delenv("COINGECKO_API_KEY", raising=False)

    def handler(request):
        assert "x-cg-demo-api-key" not in request.headers
        return response({"coins": []})

    client = make_client(handler)
    assert client.api_key_configured is False
    assert client.search_coins("btc")["count"] == 0


def test_ping_uses_documented_endpoint_and_validates_payload():
    def handler(request):
        assert request.url.path == "/api/v3/ping"
        return response({"gecko_says": "(V3) To the Moon!"})

    result = make_client(handler).ping()
    assert result["provider"] == "coingecko"
    assert result["status_message_present"] is True

    with pytest.raises(CoinGeckoResponseError, match="status message"):
        make_client(lambda request: response({"unexpected": 1})).ping()


def test_timeout_is_reported_without_details():
    def handler(request):
        raise httpx.ConnectTimeout("synthetic timeout", request=request)

    with pytest.raises(CoinGeckoError, match="timed out"):
        make_client(handler).get_price("bitcoin")


def test_rate_limit_is_named_and_body_not_exposed():
    client = make_client(lambda request: response({"private": "details"}, status=429))
    with pytest.raises(CoinGeckoError, match=r"HTTP 429 \(rate limited\)") as exc:
        client.get_price("bitcoin")
    assert "private" not in str(exc.value)
