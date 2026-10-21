#!/usr/bin/env python3
"""Audit a local OHLCV CSV file without network access or automatic data repair."""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wallex_research.csv_io import CSVDataError, load_candles  # noqa: E402
from wallex_research.data_quality import audit_candles  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv_file", type=Path, help="local CSV with symbol,timestamp,open,high,low,close,volume columns")
    parser.add_argument("--interval-seconds", type=int, help="explicit expected timestamp interval; cadence is not inferred")
    args = parser.parse_args()
    expected = timedelta(seconds=args.interval_seconds) if args.interval_seconds is not None else None
    try:
        candles = load_candles(args.csv_file)
        report = audit_candles(candles, expected_interval=expected)
    except (CSVDataError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print(f"Rows checked: {report.rows_checked}")
    print(f"Cadence checked: {'yes' if report.cadence_checked else 'no (unknown)'}")
    for issue in report.issues:
        row = f" row={issue.row}" if issue.row is not None else ""
        print(f"{issue.severity.upper()} {issue.code}{row}: {issue.message}")
    if report.is_valid:
        print("Result: structurally valid; provenance, completeness, and exchange compatibility are not verified")
        return 0
    print("Result: invalid; no rows were sorted, repaired, imputed, or removed")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
