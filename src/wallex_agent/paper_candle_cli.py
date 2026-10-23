"""CLI for offline candle-driven paper simulation."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .data_quality import audit_file
from .paper_candle_strategy import run_paper_candle_strategy
from .paper_trading import PaperBroker, PaperTradingError


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wallex-paper-candles",
        description="Run a long-only momentum strategy on local candles with a virtual ledger only.",
    )
    parser.add_argument("--input", required=True, help="Chronological OHLCV JSONL file")
    parser.add_argument("--symbol", required=True, help="Single symbol label for this dataset")
    parser.add_argument("--db", default="var/wallex-agent/paper-candles.sqlite3")
    parser.add_argument("--initial-cash", required=True, help="Used only for a new ledger")
    parser.add_argument("--fee-bps", default="0", help="Fee assumption per side; not inferred from Wallex")
    parser.add_argument("--slippage-bps", default="0", help="Adverse slippage assumption per side")
    parser.add_argument("--max-order-notional", required=True)
    parser.add_argument("--max-daily-loss-percent", default="5")
    parser.add_argument("--lookback-bars", type=int, default=5)
    parser.add_argument("--entry-return-bps", default="20")
    parser.add_argument("--exit-return-bps", default="0")
    parser.add_argument("--audit-input-data", action="store_true", help="Audit candle data before simulation")
    parser.add_argument("--expected-interval-seconds", type=int, help="Expected candle interval for audit")
    parser.add_argument("--allow-review-data", action="store_true", help="Proceed on REVIEW only after manually checking the audit report")
    parser.add_argument("--output", help="Optional JSON report path; defaults to stdout")
    args = parser.parse_args(argv)
    try:
        if args.allow_review_data and not args.audit_input_data:
            raise PaperTradingError("--allow-review-data requires --audit-input-data")
        audit = None
        if args.audit_input_data:
            audit = audit_file(args.input, expected_symbol=args.symbol,
                               expected_interval_seconds=args.expected_interval_seconds)
            if audit["status"] == "INVALID":
                raise PaperTradingError("input data audit status is INVALID; paper simulation blocked")
            if audit["status"] == "REVIEW" and not args.allow_review_data:
                raise PaperTradingError("input data audit status is REVIEW; inspect audit report and pass --allow-review-data only if justified")
        rows = []
        for line_no, line in enumerate(Path(args.input).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PaperTradingError(f"invalid JSON on line {line_no}") from exc
            if not isinstance(row, dict):
                raise PaperTradingError(f"line {line_no} must be a JSON object")
            rows.append(row)
        broker = PaperBroker(
            args.db, initial_cash=args.initial_cash, fee_bps=args.fee_bps,
            slippage_bps=args.slippage_bps, max_order_notional=args.max_order_notional,
            max_daily_loss_percent=args.max_daily_loss_percent,
        )
        report = run_paper_candle_strategy(
            broker, rows, symbol=args.symbol, lookback_bars=args.lookback_bars,
            entry_return_bps=args.entry_return_bps, exit_return_bps=args.exit_return_bps,
        )
        if audit is not None:
            report["input_data_audit"] = {
                "status": audit["status"], "input_rows_valid": audit["input_rows_valid"],
                "potential_gaps": audit["potential_gaps"], "error_count": audit["error_count"],
                "warning_count": audit["warning_count"], "review_override_used": args.allow_review_data,
            }
        encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            target = Path(args.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0
    except (OSError, ValueError, PaperTradingError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
