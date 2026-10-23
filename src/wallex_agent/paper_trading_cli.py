"""Offline JSONL driver for the SQLite paper broker."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Sequence

from .paper_trading import PaperBroker, PaperTradingError


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wallex-paper",
        description="Run explicit simulated orders from local JSONL; never connects to Wallex.",
    )
    parser.add_argument("--input", required=True, help="JSONL file of simulated order events")
    parser.add_argument("--db", default="var/wallex-agent/paper.sqlite3", help="SQLite virtual ledger")
    parser.add_argument("--initial-cash", required=True, help="Used only when initializing a new ledger")
    parser.add_argument("--fee-bps", default="0", help="Illustrative fee assumption per side")
    parser.add_argument("--slippage-bps", default="0", help="Illustrative adverse slippage per side")
    parser.add_argument("--max-order-notional", required=True)
    parser.add_argument("--max-daily-loss-percent", default="5")
    parser.add_argument("--output", help="Optional JSON report path; defaults to stdout")
    args = parser.parse_args(argv)
    try:
        broker = PaperBroker(
            args.db, initial_cash=args.initial_cash, fee_bps=args.fee_bps,
            slippage_bps=args.slippage_bps, max_order_notional=args.max_order_notional,
            max_daily_loss_percent=args.max_daily_loss_percent,
        )
        results = []
        for line_no, line in enumerate(Path(args.input).read_text(encoding="utf-8").splitlines(), 1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as exc:
                raise PaperTradingError(f"invalid JSON on line {line_no}") from exc
            if not isinstance(event, dict):
                raise PaperTradingError(f"line {line_no} must be a JSON object")
            try:
                results.append(broker.execute_market_order(
                    event_id=event["event_id"], timestamp=event["timestamp"], symbol=event["symbol"],
                    side=event["side"], quantity=event["quantity"], reference_price=event["reference_price"],
                ))
            except KeyError as exc:
                raise PaperTradingError(f"line {line_no} is missing required field {exc.args[0]}") from exc
        report = {"mode": "paper", "events_processed": len(results), "fills": results,
                  "account": broker.snapshot(), "live_trading_enabled": False,
                  "order_submission_attempted": False}
        encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\\n"
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
