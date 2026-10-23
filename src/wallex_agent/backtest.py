"""Offline, long-only baseline backtest with next-bar execution and explicit costs.

This is a research harness, not an investment recommendation or live order path.
Signals use only closes available at bar t and are executed at bar t+1 open.
"""
from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Iterable, Mapping

class BacktestError(ValueError):
    """Malformed input or invalid backtest configuration."""

def _d(value: Any, name: str) -> Decimal:
    if isinstance(value, bool):
        raise BacktestError(f"{name} must be a finite decimal")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise BacktestError(f"{name} must be a finite decimal") from exc
    if not result.is_finite():
        raise BacktestError(f"{name} must be a finite decimal")
    return result

def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise BacktestError("timestamp must be an ISO-8601 string")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise BacktestError("timestamp must be valid ISO-8601") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise BacktestError("naive timestamps are not accepted")
    return parsed

@dataclass(frozen=True, slots=True)
class Candle:
    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal

    @classmethod
    def from_mapping(cls, row: Mapping[str, Any]) -> "Candle":
        stamp = _timestamp(row.get("timestamp"))
        values = {name: _d(row.get(name), name) for name in ("open", "high", "low", "close", "volume")}
        if min(values["open"], values["high"], values["low"], values["close"]) <= 0:
            raise BacktestError("OHLC prices must be positive")
        if values["volume"] < 0:
            raise BacktestError("volume cannot be negative")
        if values["high"] < max(values["open"], values["close"], values["low"]):
            raise BacktestError("high is inconsistent with OHLC values")
        if values["low"] > min(values["open"], values["close"], values["high"]):
            raise BacktestError("low is inconsistent with OHLC values")
        return cls(stamp.isoformat(), values["open"], values["high"], values["low"], values["close"], values["volume"])

@dataclass(frozen=True, slots=True)
class BacktestConfig:
    initial_cash: Decimal
    lookback_bars: int
    entry_return_bps: Decimal
    exit_return_bps: Decimal
    fee_bps_per_side: Decimal
    slippage_bps_per_side: Decimal
    spread_bps_per_side: Decimal = Decimal("0")

    def __post_init__(self) -> None:
        cash = _d(self.initial_cash, "initial_cash")
        if cash <= 0:
            raise BacktestError("initial_cash must be positive")
        object.__setattr__(self, "initial_cash", cash)
        if isinstance(self.lookback_bars, bool) or not isinstance(self.lookback_bars, int) or self.lookback_bars < 1:
            raise BacktestError("lookback_bars must be a positive integer")
        for name in ("entry_return_bps", "exit_return_bps", "fee_bps_per_side", "slippage_bps_per_side", "spread_bps_per_side"):
            value = _d(getattr(self, name), name)
            if name.endswith("bps") or "bps_" in name:
                if value < 0 or value > Decimal("10000"):
                    raise BacktestError(f"{name} must be between 0 and 10000")
            object.__setattr__(self, name, value)

    @property
    def cost_rate_per_side(self) -> Decimal:
        return (self.fee_bps_per_side + self.slippage_bps_per_side + self.spread_bps_per_side) / Decimal("10000")

def load_candles(rows: Iterable[Mapping[str, Any]]) -> list[Candle]:
    candles = [Candle.from_mapping(row) for row in rows]
    if len(candles) < 2:
        raise BacktestError("at least two candles are required")
    stamps = [_timestamp(c.timestamp) for c in candles]
    if any(stamps[i] >= stamps[i + 1] for i in range(len(stamps) - 1)):
        raise BacktestError("candles must have unique, strictly increasing timestamps")
    return candles

def run_momentum_backtest(rows: Iterable[Mapping[str, Any]] | list[Candle], config: BacktestConfig) -> dict[str, Any]:
    """Long-only threshold baseline. Close[t] signal is filled at Open[t+1]."""
    candles = rows if isinstance(rows, list) and (not rows or isinstance(rows[0], Candle)) else load_candles(rows)  # type: ignore[arg-type]
    if len(candles) < config.lookback_bars + 2:
        raise BacktestError("need at least lookback_bars + 2 candles for next-bar execution")
    cash = config.initial_cash
    units = Decimal("0")
    entry_equity: Decimal | None = None
    trades: list[dict[str, str]] = []
    equity_curve: list[dict[str, str]] = []
    peak = config.initial_cash
    max_drawdown = Decimal("0")
    cost_rate = config.cost_rate_per_side
    for i, candle in enumerate(candles):
        # Signal formed at the previous close; it can only execute at this bar's open.
        if i > config.lookback_bars:
            signal_start = candles[i - 1 - config.lookback_bars].close
            signal_end = candles[i - 1].close
            signal_bps = (signal_end - signal_start) / signal_start * Decimal("10000")
            if units == 0 and signal_bps >= config.entry_return_bps:
                units = cash / (candle.open * (Decimal("1") + cost_rate))
                cash = Decimal("0")
                entry_equity = units * candle.open
                trades.append({"entry_timestamp": candle.timestamp, "entry_price": str(candle.open),
                               "signal_return_bps": str(signal_bps.quantize(Decimal("0.01")))})
            elif units > 0 and signal_bps <= config.exit_return_bps:
                proceeds = units * candle.open * (Decimal("1") - cost_rate)
                cash = proceeds
                if trades and "exit_timestamp" not in trades[-1]:
                    trades[-1].update({"exit_timestamp": candle.timestamp, "exit_price": str(candle.open),
                                       "trade_pnl": str((proceeds - (entry_equity or config.initial_cash)).quantize(Decimal("0.00000001")))})
                units = Decimal("0")
                entry_equity = None
        equity = cash + units * candle.close
        peak = max(peak, equity)
        drawdown = (peak - equity) / peak if peak else Decimal("0")
        max_drawdown = max(max_drawdown, drawdown)
        equity_curve.append({"timestamp": candle.timestamp, "equity": str(equity.quantize(Decimal("0.00000001"))),
                             "close": str(candle.close)})
    final_equity = cash + units * candles[-1].close
    if units > 0:
        # Mark open inventory to market; do not pretend a final liquidation occurred.
        trades.append({"status": "OPEN_AT_END", "mark_price": str(candles[-1].close),
                       "marked_value": str((units * candles[-1].close).quantize(Decimal("0.00000001")))})
    net_return = (final_equity / config.initial_cash - Decimal("1")) * Decimal("100")
    completed = [t for t in trades if "trade_pnl" in t]
    wins = sum(1 for t in completed if Decimal(t["trade_pnl"]) > 0)
    return {
        "mode": "historical_backtest",
        "strategy_id": "long-only-threshold-momentum-next-open-v1",
        "bars": len(candles),
        "lookback_bars": config.lookback_bars,
        "initial_cash": str(config.initial_cash),
        "final_equity_marked": str(final_equity.quantize(Decimal("0.00000001"))),
        "net_return_percent_marked": str(net_return.quantize(Decimal("0.0001"))),
        "max_drawdown_percent": str((max_drawdown * 100).quantize(Decimal("0.0001"))),
        "completed_round_trips": len(completed),
        "win_rate_percent_completed": str((Decimal(wins) / len(completed) * 100).quantize(Decimal("0.01"))) if completed else None,
        "cost_model_per_side_bps": str((cost_rate * Decimal("10000")).quantize(Decimal("0.01"))),
        "trades": trades,
        "equity_curve": equity_curve,
        "caveats": ["research baseline only", "no intrabar execution", "no depth/queue modelling",
                    "no tax or exchange-specific fee-tier lookup", "open inventory is marked, not liquidated",
                    "results depend on supplied data and explicit cost assumptions"],
        "order_submission_attempted": False,
    }

@dataclass(frozen=True, slots=True)
class WalkForwardFold:
    train_start: int
    train_end: int
    test_start: int
    test_end: int

def partition_walk_forward(total_bars: int, folds: int, train_size: int, test_size: int) -> list[WalkForwardFold]:
    """Make chronological, fully disjoint train/test blocks; leftover bars are unused."""
    for name, value in (("total_bars", total_bars), ("folds", folds), ("train_size", train_size), ("test_size", test_size)):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise BacktestError(f"{name} must be a positive integer")
    required = folds * (train_size + test_size)
    if required > total_bars:
        raise BacktestError(f"insufficient bars: need {required}, got {total_bars}")
    result = []
    cursor = 0
    for _ in range(folds):
        train_start, train_end = cursor, cursor + train_size
        test_start, test_end = train_end, train_end + test_size
        result.append(WalkForwardFold(train_start, train_end, test_start, test_end))
        cursor = test_end
    return result
