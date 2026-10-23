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



def test_rejects_reuse_of_event_id_for_different_order(tmp_path):
    account = broker(tmp_path)
    account.execute_market_order(event_id="stable-id", timestamp="2026-10-23T10:00:00Z",
        symbol="BTC_USDT", side="buy", quantity="1", reference_price="100")
    with pytest.raises(PaperTradingError, match="event_id already exists"):
        account.execute_market_order(event_id="stable-id", timestamp="2026-10-23T10:00:00Z",
            symbol="BTC_USDT", side="buy", quantity="2", reference_price="100")


def test_daily_loss_guard_keeps_new_mark_and_blocks_retries(tmp_path):
    account = broker(tmp_path)
    account.execute_market_order(event_id="buy", timestamp="2026-10-23T10:00:00Z",
        symbol="BTC_USDT", side="buy", quantity="1", reference_price="100")
    with pytest.raises(PaperTradingError, match="max daily loss"):
        account.execute_market_order(event_id="blocked", timestamp="2026-10-23T10:05:00Z",
            symbol="BTC_USDT", side="buy", quantity="0.1", reference_price="40")
    # The market mark from the rejected order is committed, so retrying at the
    # same price cannot evade the risk check by rolling the price back.
    assert account.snapshot()["positions"]["BTC_USDT"]["last_price"] == "40"
    with pytest.raises(PaperTradingError, match="max daily loss"):
        account.execute_market_order(event_id="blocked-retry", timestamp="2026-10-23T10:06:00Z",
            symbol="BTC_USDT", side="buy", quantity="0.1", reference_price="40")


def test_rejects_timestamp_without_timezone(tmp_path):
    account = broker(tmp_path)
    with pytest.raises(PaperTradingError, match="timezone-aware"):
        account.execute_market_order(event_id="no-tz", timestamp="2026-10-23T10:00:00",
            symbol="BTC_USDT", side="buy", quantity="1", reference_price="100")


def test_paper_cli_processes_jsonl_and_persists_ledger(tmp_path, capsys):
    import json
    from wallex_agent.paper_trading_cli import main

    source = tmp_path / "events.jsonl"
    source.write_text(json.dumps({
        "event_id": "cli-1", "timestamp": "2026-10-23T10:00:00Z",
        "symbol": "BTC_USDT", "side": "buy", "quantity": "1", "reference_price": "100",
    }) + "\n", encoding="utf-8")
    db = tmp_path / "cli.sqlite3"
    code = main(["--input", str(source), "--db", str(db), "--initial-cash", "1000",
                 "--max-order-notional", "500"])
    assert code == 0
    report = json.loads(capsys.readouterr().out)
    assert report["events_processed"] == 1
    assert report["live_trading_enabled"] is False
    assert report["account"]["positions"]["BTC_USDT"]["units"] == "1"


def test_first_price_mark_of_new_day_cannot_hide_loss(tmp_path):
    account = broker(tmp_path)
    account.execute_market_order(event_id="day-one-buy", timestamp="2026-10-23T10:00:00Z",
        symbol="BTC_USDT", side="buy", quantity="1", reference_price="100")
    with pytest.raises(PaperTradingError, match="max daily loss"):
        account.execute_market_order(event_id="day-two", timestamp="2026-10-24T10:00:00Z",
            symbol="BTC_USDT", side="buy", quantity="0.1", reference_price="40")
    assert account.snapshot()["positions"]["BTC_USDT"]["last_price"] == "40"



def test_rejects_buy_that_exceeds_virtual_cash_even_below_notional_cap(tmp_path):
    account = broker(tmp_path, initial_cash="100")
    with pytest.raises(PaperTradingError, match="insufficient virtual cash"):
        account.execute_market_order(event_id="too-expensive", timestamp="2026-10-23T10:00:00Z",
            symbol="BTC_USDT", side="buy", quantity="11", reference_price="10")


def test_existing_ledger_rejects_changed_simulation_settings(tmp_path):
    broker(tmp_path)
    with pytest.raises(PaperTradingError, match="configuration mismatch"):
        broker(tmp_path, fee_bps="11")


def test_daily_loss_guard_still_allows_risk_reducing_sell(tmp_path):
    account = broker(tmp_path)
    account.execute_market_order(event_id="buy-before-loss", timestamp="2026-10-23T10:00:00Z",
        symbol="BTC_USDT", side="buy", quantity="1", reference_price="100")
    account.mark_price(timestamp="2026-10-23T10:05:00Z", symbol="BTC_USDT", price="40")
    sold = account.execute_market_order(event_id="risk-reducing-sell", timestamp="2026-10-23T10:06:00Z",
        symbol="BTC_USDT", side="sell", quantity="1", reference_price="40")
    assert sold["side"] == "sell"
    assert account.snapshot()["positions"] == {}


def test_candle_strategy_generates_next_open_paper_fills(tmp_path):
    from wallex_agent.paper_candle_strategy import run_paper_candle_strategy

    prices = [100, 101, 102, 103, 101, 99, 98]
    rows = []
    for hour, price in enumerate(prices):
        rows.append({
            "timestamp": f"2026-10-23T{hour:02d}:00:00Z",
            "open": str(price), "high": str(price + 1), "low": str(price - 1),
            "close": str(price), "volume": "10", "symbol": "BTC_USDT",
        })
    account = PaperBroker(tmp_path / "strategy.sqlite3", initial_cash="1000",
        fee_bps="0", slippage_bps="0", max_order_notional="1000",
        max_daily_loss_percent="20")
    report = run_paper_candle_strategy(account, rows, symbol="BTC_USDT",
        lookback_bars=2, entry_return_bps="50", exit_return_bps="0")
    assert [fill["side"] for fill in report["fills"]] == ["buy", "sell"]
    assert report["order_submission_attempted"] is False
    assert report["account"]["positions"] == {}
