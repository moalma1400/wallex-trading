"""Chronological walk-forward evaluation for the existing offline baseline."""
from __future__ import annotations

from decimal import Decimal
from typing import Any, Iterable, Mapping, Sequence

from .backtest import (
    BacktestConfig, BacktestError, load_candles, partition_walk_forward,
    run_momentum_backtest,
)


def _grid(values: Sequence[Any], name: str) -> list[Decimal]:
    if not values:
        raise BacktestError(f"{name} grid must not be empty")
    parsed = []
    for value in values:
        try:
            item = Decimal(str(value))
        except Exception as exc:
            raise BacktestError(f"invalid {name} grid value") from exc
        if not item.is_finite() or item < 0 or item > Decimal("10000"):
            raise BacktestError(f"{name} grid values must be finite and between 0 and 10000")
        parsed.append(item)
    return sorted(set(parsed))


def run_walk_forward(
    rows: Iterable[Mapping[str, Any]],
    *,
    initial_cash: Any,
    folds: int,
    train_size: int,
    test_size: int,
    lookbacks: Sequence[int],
    entry_thresholds_bps: Sequence[Any],
    exit_thresholds_bps: Sequence[Any],
    fee_bps_per_side: Any,
    slippage_bps_per_side: Any,
    spread_bps_per_side: Any = "0",
) -> dict[str, Any]:
    """Choose params on each train block and evaluate once on its later test block.

    Every train/test block is disjoint. Each test is a fresh isolated simulation;
    no training equity, position, or parameter-selection result is carried as an
    executable account state into the next fold.
    """
    candles = load_candles(rows)
    if any(isinstance(x, bool) or not isinstance(x, int) or x < 1 for x in lookbacks):
        raise BacktestError("lookbacks must be positive integers")
    lookback_grid = sorted(set(lookbacks))
    entries = _grid(entry_thresholds_bps, "entry threshold")
    exits = _grid(exit_thresholds_bps, "exit threshold")
    if len(exits) * len(entries) * len(lookback_grid) > 1000:
        raise BacktestError("parameter grid is too large (maximum 1000 combinations)")
    partitions = partition_walk_forward(len(candles), folds, train_size, test_size)
    if min(train_size, test_size) < max(lookback_grid) + 2:
        raise BacktestError("train_size and test_size must each be at least max(lookbacks) + 2")
    try:
        initial = Decimal(str(initial_cash))
    except Exception as exc:
        raise BacktestError("initial_cash must be a finite positive decimal") from exc
    if not initial.is_finite() or initial <= 0:
        raise BacktestError("initial_cash must be a finite positive decimal")
    # Validate fixed costs once using the same configuration contract as backtest.
    base = dict(initial_cash=initial, fee_bps_per_side=fee_bps_per_side,
                slippage_bps_per_side=slippage_bps_per_side, spread_bps_per_side=spread_bps_per_side)
    fold_reports = []
    for fold_index, part in enumerate(partitions, start=1):
        train_rows = candles[part.train_start:part.train_end]
        test_rows = candles[part.test_start:part.test_end]
        candidates = []
        for lookback in lookback_grid:
            for entry in entries:
                for exit_value in exits:
                    config = BacktestConfig(lookback_bars=lookback, entry_return_bps=entry,
                                            exit_return_bps=exit_value, **base)
                    report = run_momentum_backtest(train_rows, config)
                    candidates.append((report, config))
        # Selection uses training results only; drawdown breaks equal-return ties.
        candidates.sort(key=lambda pair: (
            -Decimal(pair[0]["net_return_percent_marked"]),
            Decimal(pair[0]["max_drawdown_percent"]),
            pair[1].lookback_bars, pair[1].entry_return_bps, pair[1].exit_return_bps,
        ))
        train_best, selected = candidates[0]
        test_config = BacktestConfig(lookback_bars=selected.lookback_bars,
            entry_return_bps=selected.entry_return_bps, exit_return_bps=selected.exit_return_bps, **base)
        test_report = run_momentum_backtest(test_rows, test_config)
        fold_reports.append({
            "fold": fold_index,
            "train_indices": [part.train_start, part.train_end],
            "test_indices": [part.test_start, part.test_end],
            "selected_parameters": {
                "lookback_bars": selected.lookback_bars,
                "entry_return_bps": str(selected.entry_return_bps),
                "exit_return_bps": str(selected.exit_return_bps),
            },
            "training_selection_return_percent": train_best["net_return_percent_marked"],
            "training_selection_max_drawdown_percent": train_best["max_drawdown_percent"],
            "test": {
                "net_return_percent_marked": test_report["net_return_percent_marked"],
                "max_drawdown_percent": test_report["max_drawdown_percent"],
                "completed_round_trips": test_report["completed_round_trips"],
                "win_rate_percent_completed": test_report["win_rate_percent_completed"],
                "final_equity_marked": test_report["final_equity_marked"],
                "order_submission_attempted": False,
            },
        })
    returns = [Decimal(f["test"]["net_return_percent_marked"]) for f in fold_reports]
    mean_return = sum(returns, Decimal("0")) / Decimal(len(returns))
    return {
        "mode": "walk_forward_research",
        "strategy_id": "long-only-threshold-momentum-next-open-v1",
        "folds": fold_reports,
        "aggregate": {
            "fold_count": len(fold_reports),
            "mean_test_return_percent": str(mean_return.quantize(Decimal("0.0001"))),
            "positive_test_folds": sum(value > 0 for value in returns),
            "negative_test_folds": sum(value < 0 for value in returns),
            "zero_test_folds": sum(value == 0 for value in returns),
            "worst_test_return_percent": str(min(returns).quantize(Decimal("0.0001"))),
            "best_test_return_percent": str(max(returns).quantize(Decimal("0.0001"))),
        },
        "parameter_selection": "highest marked training return; ties broken by lower training max drawdown, then simpler numeric parameters",
        "partition_policy": "chronological disjoint train/test blocks; test blocks are not used for parameter selection",
        "caveats": [
            "research only; no live account or order endpoints",
            "test results are isolated simulations, not a continuous portfolio",
            "no guarantee of future returns; small grids and small samples can overfit",
            "results depend on supplied data quality and explicit cost assumptions",
            "no taxes, depth, queue priority, partial fills, or variable liquidity model",
        ],
        "order_submission_attempted": False,
    }
