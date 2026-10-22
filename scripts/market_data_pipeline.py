#!/usr/bin/env python3
"""Local-only historical market data import, audit, and replay export."""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wallex_research.dataset_store import DatasetStore
from wallex_research.historical import DatasetContext, HistoricalDataError, utc_time
from wallex_research.historical_quality import AuditPolicy, audit_dataset, export_replay_csv, write_audit_reports


def _parse_scale(value: str) -> tuple[str, int]:
    try:
        name, raw = value.split("=", 1)
        places = int(raw)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError("use FIELD=NONNEGATIVE_INTEGER, e.g. price=8") from exc
    if not name or places < 0:
        raise argparse.ArgumentTypeError("field must be non-empty and decimal places nonnegative")
    return name, places


def parser_factory() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)

    importer = commands.add_parser("import-local", help="preserve and normalize one local CSV/JSON file")
    importer.add_argument("--file", required=True, type=Path)
    importer.add_argument("--root", required=True, type=Path)
    importer.add_argument("--record-type", required=True, choices=("candles", "market_metadata", "public_trades", "fair_price_snapshot", "order_book_snapshot", "order_book_side"))
    importer.add_argument("--source-id", required=True, help="caller assertion; use SYNTHETIC-FIXTURE for committed examples")
    importer.add_argument("--source-url", required=True, help="source reference; this program does not request it")
    importer.add_argument("--retrieval-method", required=True, help="for example local_synthetic_fixture or user_file_copy")
    importer.add_argument("--retrieved-at-utc", required=True, help="explicit source/retrieval time with timezone offset")
    importer.add_argument("--ingested-at-utc", required=True, help="explicit UTC local ingestion time with timezone offset")
    importer.add_argument("--captured-at-utc", help="required for depth files without an exchange event timestamp; capture time is not ingestion time")
    importer.add_argument("--symbol", help="required context when a source row does not establish one; candles always require it")
    importer.add_argument("--interval-seconds", type=int, help="required positive interval for candle imports")

    auditor = commands.add_parser("audit", help="create deterministic JSON/CSV/Markdown quality reports")
    auditor.add_argument("--root", required=True, type=Path)
    auditor.add_argument("--dataset-id", required=True)
    auditor.add_argument("--known-symbol", action="append", dest="known_symbols", help="repeat for each symbol from a caller-supplied metadata snapshot")
    auditor.add_argument("--expected-interval-seconds", type=int)
    auditor.add_argument("--expected-start", help="inclusive expected first candle timestamp, timezone-aware")
    auditor.add_argument("--expected-end", help="inclusive expected last candle timestamp, timezone-aware")
    auditor.add_argument("--as-of", help="explicit UTC evaluation time")
    auditor.add_argument("--max-age-seconds", type=int)
    auditor.add_argument("--max-decimal-places", action="append", type=_parse_scale, default=[], metavar="FIELD=PLACES")
    auditor.add_argument("--report-dir", type=Path, help="default: ROOT/reports")
    auditor.add_argument("--replay-export", type=Path, help="optional Feature 002 CSV path; blocked unless the explicit audit policy passes")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = parser_factory()
    args = parser.parse_args(argv)
    try:
        if args.command == "import-local":
            context = DatasetContext(
                record_type=args.record_type,
                source_id=args.source_id,
                source_url=args.source_url,
                retrieval_method=args.retrieval_method,
                retrieved_at_utc=utc_time(args.retrieved_at_utc, "retrieved_at_utc"),
                ingested_at_utc=utc_time(args.ingested_at_utc, "ingested_at_utc"),
                captured_at_utc=utc_time(args.captured_at_utc, "captured_at_utc") if args.captured_at_utc else None,
                symbol=args.symbol,
                interval_seconds=args.interval_seconds,
            )
            result = DatasetStore(args.root).import_local(args.file, context)
            print(json.dumps({
                "dataset_id": result.dataset_id,
                "created": result.created,
                "record_count": result.record_count,
                "raw_sha256": result.raw_sha256,
                "normalized_sha256": result.normalized_sha256,
                "manifest": str(result.manifest_path),
            }, sort_keys=True, indent=2))
            return 0

        scales: dict[str, int] = {}
        for name, value in args.max_decimal_places:
            if name in scales and scales[name] != value:
                raise HistoricalDataError(f"conflicting maximum decimal places for {name}")
            scales[name] = value
        policy = AuditPolicy(
            expected_interval_seconds=args.expected_interval_seconds,
            expected_start_utc=utc_time(args.expected_start, "expected_start") if args.expected_start else None,
            expected_end_utc=utc_time(args.expected_end, "expected_end") if args.expected_end else None,
            as_of_utc=utc_time(args.as_of, "as_of") if args.as_of else None,
            max_age_seconds=args.max_age_seconds,
            known_symbols=tuple(args.known_symbols) if args.known_symbols is not None else None,
            max_decimal_places=scales if args.max_decimal_places else None,
        )
        store = DatasetStore(args.root)
        report = audit_dataset(store, args.dataset_id, policy)
        output_dir = args.report_dir or (args.root / "reports")
        outputs = write_audit_reports(report, output_dir)
        result = {
            "report_id": report.report_id,
            "dataset_id": report.dataset_id,
            "replay_eligible": report.replay_eligible,
            "error_count": sum(issue.severity == "error" for issue in report.issues),
            "warning_count": sum(issue.severity == "warning" for issue in report.issues),
            "outputs": [str(path) for path in outputs],
        }
        if args.replay_export:
            exported, sidecar = export_replay_csv(store, report, args.replay_export)
            result["replay_export"] = {"csv": str(exported), "sidecar": str(sidecar)}
        print(json.dumps(result, sort_keys=True, indent=2))
        if report.has_errors:
            return 1
        if report.record_type == "candles" and not report.replay_eligible:
            return 1
        return 0
    except (HistoricalDataError, OSError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
