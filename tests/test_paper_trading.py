from decimal import Decimal
import pytest

from wallex_agent.paper_trading import PaperBroker, PaperTradingError


def broker(tmp_path, **overrides):
    config = dict(initial_cash="1000", fee_bps="10", slippage_bps="20",
                  max_order_notional="500", max_daily_loss_percent="5")
    config.update(overrides)
    return PaperBroker(tmp_path / "paper.sqlite3", **config)


def test_buy_sell_apply_costs_and_virtual_balances(tmp_path):
    account = broker(tmp_path)
    bought = account.execute_market_order(event_id="e1", timestamp="2026-10-23T10:00:00Z",
        symbol="btc_usdt", side="buy", quantity="1", reference_price="100")
    assert bought["mode"] == "paper"
    assert Decimal(bought["fill_price"]) == Decimal("100.20")
    assert Decimal(bought["fee"]) == Decimal("0.10020")
    assert bought["order_submission_attempted"] is False
    sold = account.execute_market_order(event_id="e2", timestamp="2026-10-23T10:01:00Z",
        symbol="BTC_USDT", side="sell", quantity="1", reference_price="110")
    assert Decimal(sold["fill_price"]) == Decimal("109.78")
    assert Decimal(sold["cash_after"]) < Decimal("1010")
    assert account.snapshot()["positions"] == {}


def test_duplicate_event_is_idempotent_after_restart(tmp_path):
    first = broker(tmp_path)
    original = first.execute_market_order(event_id="same", timestamp="2026-10-23T10:00:00Z",
        symbol="BTC_USDT", side="buy", quantity="1", reference_price="100")
    reopened = broker(tmp_path)
    repeated = reopened.execute_market_order(event_id="same", timestamp="2026-10-23T10:00:00Z",
        symbol="BTC_USDT", side="buy", quantity="1", reference_price="100")
    assert repeated == original
    assert Decimal(reopened.snapshot()["positions"]["BTC_USDT"]["units"]) == Decimal("1")


@pytest.mark.parametrize("kwargs", [
    {"side": "buy", "quantity": "1", "reference_price": "501", "message": "notional"},
    {"side": "buy", "quantity": "100", "reference_price": "10", "message": "cash"},
    {"side": "sell", "quantity": "1", "reference_price": "10", "message": "position"},
    {"side": "buy", "quantity": "-1", "reference_price": "10", "message": "positive"},
])
def test_rejects_orders_that_break_guards(tmp_path, kwargs):
    account = broker(tmp_path)
    with pytest.raises(PaperTradingError):
        account.execute_market_order(event_id="x", timestamp="2026-10-23T10:00:00Z",
            symbol="BTC_USDT", **{k: kwargs[k] for k in ("side", "quantity", "reference_price")})


def test_rejects_invalid_configuration(tmp_path):
    with pytest.raises(PaperTradingError):
        broker(tmp_path, max_daily_loss_percent="100")
