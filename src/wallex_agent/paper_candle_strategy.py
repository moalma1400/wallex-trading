"""Offline candle-to-paper simulation; no network or exchange access."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable, Mapping

from .backtest import BacktestError, load_candles
from .paper_trading import PaperBroker, PaperTradingError


def run_paper_candle_strategy(
    broker: PaperBroker,
    rows: Iterable[Mapping[str, Any]],
    *,
    symbol: str,
    lookback_bars: int = 5,
    entry_return_bps: Any = "20",
    exit_return_bps: Any = "0",
) -> dict[str, Any]:
    """Replay a simple long-only momentum rule with next-open virtual fills.

    Signals use only closes available before the current candle; simulated execution
    occurs at the current candle's open. One symbol and one long position at a time.
    """
    symbol = symbol.strip().upper()
    if not symbol:
        raise PaperTradingError("symbol must be non-empty")
    if isinstance(lookback_bars, bool) or not isinstance(lookback_bars, int) or lookback_bars < 1:
        raise PaperTradingError("lookback_bars must be a positive integer")
    try:
        entry = Decimal(str(entry_return_bps))
        exit_value = Decimal(str(exit_return_bps))
    except Exception as exc:
        raise PaperTradingError("entry/exit thresholds must be finite decimals") from exc
    if not entry.is_finite() or not exit_value.is_finite():
        raise PaperTradingError("entry/exit thresholds must be finite decimals")
    raw_rows = list(rows)
    candles = load_candles(raw_rows)
    if len(candles) < lookback_bars + 2:
        raise BacktestError("need at least lookback_bars + 2 candles")
    if any(isinstance(row, Mapping) and row.get("symbol") and str(row["symbol"]).strip().upper() != symbol
           for row in raw_rows):
        raise PaperTradingError("input candles contain a symbol that differs from --symbol")

    fills: list[dict[str, Any]] = []
    rejections: list[dict[str, str]] = []
    signals: list[dict[str, str]] = []
    for index, candle in enumerate(candles):
        broker.mark_price(timestamp=candle.timestamp, symbol=symbol, price=candle.open)
        if index > lookback_bars:
            start = candles[index - 1 - lookback_bars].close
            end = candles[index - 1].close
            signal_bps = (end - start) / start * Decimal("10000")
            account = broker.snapshot()
            position = account["positions"].get(symbol)
            units = Decimal(position["units"]) if position else Decimal("0")
            side = None
            if units == 0 and signal_bps >= entry:
                side = "buy"
            elif units > 0 and signal_bps <= exit_value:
                side = "sell"
            signals.append({"timestamp": candle.timestamp, "signal_return_bps": str(signal_bps),
                            "action": side or "hold"})
            if side == "buy":
                cash = Decimal(account["cash"])
                fee_rate = broker.fee_bps / Decimal("10000")
                slippage_rate = broker.slippage_bps / Decimal("10000")
                total_cost_factor = (Decimal("1") + slippage_rate) * (Decimal("1") + fee_rate)
                quantity = min(
                    cash / (candle.open * total_cost_factor),
                    broker.max_order_notional / candle.open,
                )
            elif side == "sell":
                quantity = min(units, broker.max_order_notional / candle.open)
            else:
                quantity = Decimal("0")
            if side and quantity > 0:
                event_id = f"paper-candle-{symbol}-{candle.timestamp}-{side}"
                try:
                    fill = broker.execute_market_order(
                        event_id=event_id, timestamp=candle.timestamp, symbol=symbol,
                        side=side, quantity=quantity, reference_price=candle.open,
                    )
                    fills.append(fill)
                except PaperTradingError as exc:
                    rejections.append({"event_id": event_id, "reason": str(exc)})
        broker.mark_price(timestamp=candle.timestamp, symbol=symbol, price=candle.close)

    return {
        "mode": "paper_candle_simulation",
        "symbol": symbol,
        "bars": len(candles),
        "strategy": {"id": "long-only-threshold-momentum-next-open-v1",
                     "lookback_bars": lookback_bars, "entry_return_bps": str(entry),
                     "exit_return_bps": str(exit_value)},
        "signals": signals,
        "fills": fills,
        "rejections": rejections,
        "account": broker.snapshot(),
        "live_trading_enabled": False,
        "order_submission_attempted": False,
        "caveats": [
            "offline research simulation only; no exchange or network calls",
            "signals use prior closes and fills use the next candle open",
            "fee and slippage assumptions come from the PaperBroker configuration",
            "no intrabar execution, order-book depth, partial fills, or queue modelling",
            "not a profitability claim or a live-trading recommendation",
        ],
    }
