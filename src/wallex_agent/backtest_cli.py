"""CLI for offline historical candle JSONL backtests."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Sequence
from .backtest import BacktestConfig, BacktestError, run_momentum_backtest, load_candles
from .data_quality import audit_file


def _write_json(path_value: str | None, report: dict) -> None:
    encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
    if path_value:
        path = Path(path_value)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


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
    parser.add_argument("--audit-input-data", action="store_true",
                        help="Audit the full input (and recorder sidecar manifest if present) before backtesting")
    parser.add_argument("--allow-review-data", action="store_true",
                        help="Explicitly allow a REVIEW audit after inspecting the audit report; INVALID is never allowed")
    parser.add_argument("--expected-symbol", help="Expected symbol when auditing")
    parser.add_argument("--expected-interval-seconds", type=int, help="Expected candle interval when auditing")
    parser.add_argument("--audit-output", help="Optional separate JSON audit report path")
    args = parser.parse_args(argv)
    try:
        if args.allow_review_data and not args.audit_input_data:
            raise BacktestError("--allow-review-data requires --audit-input-data")
        if args.audit_output and not args.audit_input_data:
            raise BacktestError("--audit-output requires --audit-input-data")

        audit_report = None
        if args.audit_input_data:
            audit_report = audit_file(
                args.input,
                expected_symbol=args.expected_symbol,
                expected_interval_seconds=args.expected_interval_seconds,
            )
            if args.audit_output:
                _write_json(args.audit_output, audit_report)
            if audit_report["status"] == "INVALID":
                raise BacktestError("input data audit status is INVALID; backtest blocked")
            if audit_report["status"] == "REVIEW" and not args.allow_review_data:
                raise BacktestError("input data audit status is REVIEW; inspect the audit report, then pass --allow-review-data only if gaps are understood")

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
        if audit_report is not None:
            report["input_data_audit"] = {
                "status": audit_report["status"],
                "input_rows_valid": audit_report["input_rows_valid"],
                "invalid_records": audit_report["invalid_records"],
                "potential_gaps": audit_report["potential_gaps"],
                "error_count": audit_report["error_count"],
                "warning_count": audit_report["warning_count"],
                "audit_output": args.audit_output,
            }
        _write_json(args.output, report)
        return 0
    except (OSError, BacktestError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
