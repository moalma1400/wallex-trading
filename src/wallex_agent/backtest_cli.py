"""CLI for offline historical candle JSONL backtests."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Sequence
from .backtest import BacktestConfig, BacktestError, run_momentum_backtest, load_candles

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wallex-backtest", description="Offline long-only research baseline; never submits orders.")
    parser.add_argument("--input", required=True, help="JSONL file with timestamp, open, high, low, close, volume per line")
    parser.add_argument("--initial-cash", required=True)
    parser.add_argument("--lookback-bars", type=int, default=3)
    parser.add_argument("--entry-return-bps", type=str, default="20")
    parser.add_argument("--exit-return-bps", type=str, default="0")
    parser.add_argument("--fee-bps-per-side", required=True)
    parser.add_argument("--slippage-bps-per-side", required=True)
    parser.add_argument("--spread-bps-per-side", default="0")
    parser.add_argument("--output", help="Optional JSON report path; defaults to stdout")
    args = parser.parse_args(argv)
    try:
        path = Path(args.input)
        rows = []
        for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise BacktestError(f"invalid JSON on line {line_number}") from exc
            if not isinstance(row, dict):
                raise BacktestError(f"line {line_number} must contain a JSON object")
            rows.append(row)
        candles = load_candles(rows)
        config = BacktestConfig(args.initial_cash, args.lookback_bars, args.entry_return_bps,
            args.exit_return_bps, args.fee_bps_per_side, args.slippage_bps_per_side, args.spread_bps_per_side)
        report = run_momentum_backtest(candles, config)
        encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            Path(args.output).write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0
    except (OSError, BacktestError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
