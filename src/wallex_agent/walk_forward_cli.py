"""CLI for chronological, offline walk-forward evaluation."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .backtest import BacktestError
from .data_quality import audit_file
from .walk_forward import run_walk_forward


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wallex-walk-forward", description="Offline walk-forward research; never submits orders.")
    parser.add_argument("--input", required=True, help="Chronological candle JSONL")
    parser.add_argument("--initial-cash", required=True)
    parser.add_argument("--folds", type=int, required=True)
    parser.add_argument("--train-size", type=int, required=True, help="Candles per training block")
    parser.add_argument("--test-size", type=int, required=True, help="Candles per held-out test block")
    parser.add_argument("--lookbacks", default="3,5,10")
    parser.add_argument("--entry-thresholds-bps", default="10,20,30")
    parser.add_argument("--exit-thresholds-bps", default="0,5")
    parser.add_argument("--fee-bps-per-side", required=True)
    parser.add_argument("--slippage-bps-per-side", required=True)
    parser.add_argument("--spread-bps-per-side", default="0")
    parser.add_argument("--audit-input-data", action="store_true")
    parser.add_argument("--expected-symbol")
    parser.add_argument("--expected-interval-seconds", type=int)
    parser.add_argument("--allow-review-data", action="store_true")
    parser.add_argument("--output")
    args = parser.parse_args(argv)
    try:
        if args.allow_review_data and not args.audit_input_data:
            raise BacktestError("--allow-review-data requires --audit-input-data")
        audit = None
        if args.audit_input_data:
            audit = audit_file(args.input, expected_symbol=args.expected_symbol,
                               expected_interval_seconds=args.expected_interval_seconds)
            if audit["status"] == "INVALID":
                raise BacktestError("input data audit status is INVALID; walk-forward blocked")
            if audit["status"] == "REVIEW" and not args.allow_review_data:
                raise BacktestError("input data audit status is REVIEW; inspect gaps and pass --allow-review-data only if justified")
        rows = []
        for line_no, line in enumerate(Path(args.input).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise BacktestError(f"invalid JSON on line {line_no}") from exc
            if not isinstance(row, dict):
                raise BacktestError(f"line {line_no} must be a JSON object")
            rows.append(row)
        report = run_walk_forward(rows, initial_cash=args.initial_cash, folds=args.folds,
            train_size=args.train_size, test_size=args.test_size,
            lookbacks=[int(x.strip()) for x in args.lookbacks.split(",") if x.strip()],
            entry_thresholds_bps=[x.strip() for x in args.entry_thresholds_bps.split(",") if x.strip()],
            exit_thresholds_bps=[x.strip() for x in args.exit_thresholds_bps.split(",") if x.strip()],
            fee_bps_per_side=args.fee_bps_per_side, slippage_bps_per_side=args.slippage_bps_per_side,
            spread_bps_per_side=args.spread_bps_per_side)
        if audit is not None:
            report["input_data_audit"] = {"status": audit["status"], "input_rows_valid": audit["input_rows_valid"],
                "potential_gaps": audit["potential_gaps"], "error_count": audit["error_count"],
                "warning_count": audit["warning_count"]}
        encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            target = Path(args.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0
    except (OSError, ValueError, BacktestError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
