"""Command-line audit of local candle datasets."""
from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path
from typing import Sequence
from .data_quality import audit_file

def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="wallex-data-audit", description="Audit local OHLCV JSONL; never connects to Wallex or trades.")
    parser.add_argument("--input", required=True, help="Candle JSONL file to audit")
    parser.add_argument("--symbol", help="Expected exact symbol")
    parser.add_argument("--interval-seconds", type=int, help="Expected candle interval")
    parser.add_argument("--manifest", help="Optional recorder manifest path (auto-detected by default)")
    parser.add_argument("--as-of", help="Optional audit time (ISO-8601, timezone-aware); requires --max-staleness-seconds")
    parser.add_argument("--max-staleness-seconds", type=int, help="Flag data older than this at --as-of as stale")
    parser.add_argument("--output", help="Optional JSON report path; defaults to stdout")
    args = parser.parse_args(argv)
    try:
        report = audit_file(args.input, expected_symbol=args.symbol,
                            expected_interval_seconds=args.interval_seconds,
                            manifest_path=args.manifest,
                            as_of=args.as_of,
                            max_staleness_seconds=args.max_staleness_seconds)
        encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            path = Path(args.output)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0 if report["status"] == "OK" else 1
    except (OSError, ValueError) as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
