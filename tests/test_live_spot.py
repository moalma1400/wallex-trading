"""Offline tests for the opt-in standalone live Spot client.

All HTTP is served by a fake transport. No test connects to Wallex or needs a
real API key; live trading is disabled unless an operator configures it.
"""
from __future__ import annotations

import json
from decimal import Decimal
from unittest.mock import MagicMock

import pytest

from wallex_mcp.live_spot import (
    LIVE_ACK_VALUE,
    LiveSpotClient,
    LiveSpotConfig,
    LiveSpotConfigurationError,
    LiveSpotError,
    OrderOutcomeUnknown,
)


class FakeTransport:
    def __init__(self, responses=(), statuses=None):
        self.responses = list(responses)
        self.statuses = list(statuses or [])
        self.calls = []

    def Client(self, timeout=None):
        self.timeout = timeout
        return self

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def request(self, method, url, headers=None, json=None, **kwargs):
        self.calls.append({
            "method": method, "url": url, "headers": dict(headers or {}), "json": json
        })
        if not self.responses:
            raise AssertionError("no fake response configured")
        item = self.responses.pop(0)
        status = self.statuses.pop(0) if self.statuses else 200
        if isinstance(item, BaseException):
            raise item
        response = MagicMock()
        response.status_code = status
        response.content = json_module_dumps(item)
        return response


def json_module_dumps(payload):
    return __import__("json").dumps(payload).encode("utf-8")


def config(**overrides):
    values = dict(
        api_key="synthetic-not-a-real-key",
        allowed_symbols=frozenset({"BTCUSDT"}),
        quote_asset="USDT",
        max_order_notional=Decimal("100"),
        fee_buffer_bps=100,
    )
    values.update(overrides)
    return LiveSpotConfig(**values)


def market(**overrides):
    value = {
        "symbol": "BTCUSDT",
        "base_asset": "BTC",
        "quote_asset": "USDT",
        "is_spot": True,
        "amount_precision": 4,
        "price_precision": 2,
    }
    value.update(overrides)
    return value


def balances(*, usdt="1000", btc="1", locked_usdt="0", locked_btc="0"):
    return {
        "success": True,
        "result": {
            "balances": {
                "USDT": {"value": usdt, "locked": locked_usdt},
                "BTC": {"value": btc, "locked": locked_btc},
            }
        },
    }


def test_live_trading_disabled_by_default():
    assert LiveSpotConfig.from_env({}) is None


def test_live_trading_requires_ack_key_allowlist_quote_and_cap():
    with pytest.raises(LiveSpotConfigurationError, match="ACK"):
        LiveSpotConfig.from_env({
            "WALLEX_ENABLE_LIVE_TRADING": "1",
            "WALLEX_API_KEY": "synthetic",
            "WALLEX_LIVE_ALLOWED_SYMBOLS": "BTCUSDT",
            "WALLEX_LIVE_QUOTE_ASSET": "USDT",
            "WALLEX_LIVE_MAX_ORDER_NOTIONAL": "100",
        })


def test_live_configuration_is_explicit_and_repr_hides_key():
    loaded = LiveSpotConfig.from_env({
        "WALLEX_ENABLE_LIVE_TRADING": "1",
        "WALLEX_LIVE_TRADING_ACK": LIVE_ACK_VALUE,
        "WALLEX_API_KEY": "secret-test-value",
        "WALLEX_LIVE_ALLOWED_SYMBOLS": "btcusdt",
        "WALLEX_LIVE_QUOTE_ASSET": "usdt",
        "WALLEX_LIVE_MAX_ORDER_NOTIONAL": "100",
    })
    assert loaded is not None
    assert loaded.allowed_symbols == frozenset({"BTCUSDT"})
    assert "secret-test-value" not in repr(loaded)


def test_buy_submits_once_after_local_preflight():
    transport = FakeTransport([{
        "success": True,
        "result": {"clientOrderId": "contest-001", "status": "NEW", "symbol": "BTCUSDT"},
    }], statuses=[201])
    client = LiveSpotClient(config(), transport=transport)
    result = client.place_limit_order(
        symbol="BTCUSDT", side="BUY", quantity="0.1", price="100",
        market=market(), balances_response=balances(), client_id="contest-001",
    )
    assert result["success"] is True
    assert len(transport.calls) == 1
    assert transport.calls[0]["method"] == "POST"
    assert transport.calls[0]["url"] == "https://api.wallex.ir/v1/account/orders"
    assert transport.calls[0]["headers"]["x-api-key"] == "synthetic-not-a-real-key"
    assert transport.calls[0]["json"]["type"] == "LIMIT"
    assert transport.calls[0]["json"]["client_id"] == "contest-001"


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"symbol": "ETHUSDT"}, "not in WALLEX_LIVE_ALLOWED_SYMBOLS"),
        ({"side": "HOLD"}, "side must be BUY or SELL"),
        ({"market": {"is_spot": False}}, "not explicitly marked is_spot=true"),
        ({"market": {"quote_asset": "TMN"}}, "quote asset"),
        ({"quantity": "0.00001"}, "exceeds market precision"),
        ({"price": "100.001"}, "exceeds market precision"),
        ({"quantity": "2"}, "exceeds WALLEX_LIVE_MAX_ORDER_NOTIONAL"),
    ],
)
def test_preflight_rejects_invalid_order_without_network(kwargs, message):
    transport = FakeTransport([])
    client = LiveSpotClient(config(), transport=transport)
    args = dict(
        symbol="BTCUSDT", side="BUY", quantity="0.1", price="100",
        market=market(), balances_response=balances(), client_id="contest-001",
    )
    if "market" in kwargs:
        market_changes = dict(kwargs.pop("market"))
        args["market"] = market(**market_changes)
    args.update(kwargs)
    with pytest.raises(LiveSpotError, match=message):
        client.place_limit_order(**args)
    assert transport.calls == []


def test_insufficient_quote_balance_or_locked_balance_blocks_buy():
    client = LiveSpotClient(config(), transport=FakeTransport([]))
    with pytest.raises(LiveSpotError, match="insufficient available quote"):
        client.place_limit_order(
            symbol="BTCUSDT", side="BUY", quantity="0.1", price="100",
            market=market(), balances_response=balances(usdt="5"), client_id="contest-001",
        )
    assert client._transport.calls == []


def test_sell_requires_available_base_balance():
    client = LiveSpotClient(config(), transport=FakeTransport([]))
    with pytest.raises(LiveSpotError, match="insufficient available base"):
        client.place_limit_order(
            symbol="BTCUSDT", side="SELL", quantity="2", price="10",
            market=market(), balances_response=balances(btc="1", locked_btc="0.5"),
            client_id="contest-001",
        )
    assert client._transport.calls == []


def test_timeout_after_post_is_unknown_and_never_retried():
    transport = FakeTransport([TimeoutError("synthetic timeout")])
    client = LiveSpotClient(config(), transport=transport)
    with pytest.raises(OrderOutcomeUnknown, match="reconcile before any retry"):
        client.place_limit_order(
            symbol="BTCUSDT", side="BUY", quantity="0.1", price="100",
            market=market(), balances_response=balances(), client_id="contest-001",
        )
    assert len(transport.calls) == 1


def test_invalid_post_response_is_unknown():
    transport = FakeTransport([{"message": "missing result"}], statuses=[201])
    client = LiveSpotClient(config(), transport=transport)
    with pytest.raises(OrderOutcomeUnknown, match="reconcile before any retry"):
        client.place_limit_order(
            symbol="BTCUSDT", side="BUY", quantity="0.1", price="100",
            market=market(), balances_response=balances(), client_id="contest-001",
        )
    assert len(transport.calls) == 1


def test_order_lookup_uses_encoded_client_id_and_requires_success_envelope():
    transport = FakeTransport([{
        "success": True, "result": {"clientOrderId": "contest-001", "status": "NEW"}
    }])
    result = LiveSpotClient(config(), transport=transport).get_order("contest-001")
    assert result["success"] is True
    assert transport.calls[0]["method"] == "GET"
    assert transport.calls[0]["url"] == "https://api.wallex.ir/v1/account/orders/contest-001"


def test_zero_balances_are_valid_but_never_fund_orders():
    client = LiveSpotClient(config(), transport=FakeTransport([]))
    with pytest.raises(LiveSpotError, match="insufficient available quote"):
        client.place_limit_order(
            symbol="BTCUSDT", side="BUY", quantity="0.1", price="100",
            market=market(), balances_response=balances(usdt="0", btc="0"),
            client_id="contest-001",
        )
