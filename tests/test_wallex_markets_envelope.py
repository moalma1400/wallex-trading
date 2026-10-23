"""Regression tests for the official nested Wallex markets response envelope."""

from wallex_mcp.wallex_client import WallexClient


def _market():
    return {
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "price": "65000.10",
        "is_spot": True,
        "is_otc": False,
        "is_margin": False,
        "is_tmn_based": False,
        "is_usdt_based": True,
        "amount_precision": 8,
        "price_precision": 2,
        "flags": [],
        "volume_24h": "12.5",
        "change_24h": "1.2",
        "created_at": "2025-01-01T00:00:00Z",
        # Additive API metadata should not break consumers of the fields above.
        "fa_base_asset": "بیت‌کوین",
        "categories": ["spot"],
        "change_7D": "4.1",
    }


def _client_with_response(payload):
    client = WallexClient(max_retries=0, backoff_seconds=0)
    client._request = lambda method, host, path: payload
    return client


def test_get_markets_normalizes_nested_result_envelope():
    client = _client_with_response({
        "success": True,
        "message": "ok",
        "result": {"markets": [_market()]},
    })

    response = client.get_markets()

    assert response.success is True
    assert len(response.markets) == 1
    assert response.markets[0].symbol == "BTCUSDT"
    assert response.markets[0].price == "65000.10"


def test_get_markets_accepts_legacy_flat_envelope():
    client = _client_with_response({
        "success": True,
        "message": "ok",
        "markets": [_market()],
    })

    response = client.get_markets()

    assert response.markets[0].symbol == "BTCUSDT"


def test_get_markets_rejects_unsuccessful_envelope():
    client = _client_with_response({
        "success": False,
        "message": "failure",
        "result": {"markets": [_market()]},
    })

    try:
        client.get_markets()
    except Exception as exc:
        assert "success=false" in str(exc)
    else:
        raise AssertionError("Expected unsuccessful Wallex response to be rejected")
