from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from wallex_research.csv_io import load_candles
from wallex_research.dataset_store import DatasetStore
from wallex_research.historical import (
    DatasetContext,
    HistoricalDataError,
    MarketMetadataRecord,
    OrderBookSideSnapshotRecord,
    OrderBookSnapshotRecord,
    PublicTradeRecord,
    record_to_dict,
)
from wallex_research.historical_quality import AuditPolicy, audit_dataset, export_replay_csv, write_audit_reports
from wallex_research.models import SimulationConfig
from wallex_research.replay import run_replay


UTC = timezone.utc
FIXTURES = Path(__file__).parent / "fixtures"
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def ctx(kind: str = "candles", *, symbol: str | None = "SYNTHETIC_XYZ", interval: int | None = 60, captured: datetime | None = None, ingested: datetime = BASE + timedelta(minutes=3)) -> DatasetContext:
    return DatasetContext(
        record_type=kind,
        source_id="SYNTHETIC-FIXTURE",
        source_url="https://example.invalid/synthetic-fixture",
        retrieval_method="local_synthetic_fixture",
        retrieved_at_utc=BASE + timedelta(minutes=3),
        ingested_at_utc=ingested,
        captured_at_utc=captured,
        symbol=symbol,
        interval_seconds=interval,
    )


def clean_policy(**overrides) -> AuditPolicy:
    values = dict(
        expected_interval_seconds=60,
        expected_start_utc=BASE,
        expected_end_utc=BASE + timedelta(minutes=2),
        as_of_utc=BASE + timedelta(minutes=3),
        max_age_seconds=120,
        known_symbols=("SYNTHETIC_XYZ",),
        max_decimal_places={"price": 2, "quantity": 2},
    )
    values.update(overrides)
    return AuditPolicy(**values)


class HistoricalPipelineTests(unittest.TestCase):
    def test_local_csv_import_is_raw_preserving_idempotent_and_replay_compatible(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "store"
            source = FIXTURES / "synthetic_ohlcv.csv"
            raw = source.read_bytes()
            store = DatasetStore(root)
            first = store.import_local(source, ctx())
            second = store.import_local(source, ctx(ingested=BASE + timedelta(hours=1)))
            self.assertTrue(first.created)
            self.assertFalse(second.created)
            self.assertEqual(first.dataset_id, second.dataset_id)
            self.assertEqual(first.record_count, 3)
            self.assertEqual((root / "raw" / "sha256" / first.raw_sha256).read_bytes(), raw)
            self.assertEqual(hashlib.sha256(raw).hexdigest(), first.raw_sha256)
            self.assertEqual(len(store.read_records(first.dataset_id)), 3)

            report = audit_dataset(store, first.dataset_id, clean_policy())
            self.assertTrue(report.replay_eligible, report.issues)
            self.assertEqual(report.raw_sha256, first.raw_sha256)
            repeated_report = audit_dataset(store, first.dataset_id, clean_policy())
            self.assertEqual(report.report_id, repeated_report.report_id)
            outputs = write_audit_reports(report, Path(directory) / "reports")
            self.assertTrue(all(path.is_file() for path in outputs))
            summary = json.loads(outputs[0].read_text(encoding="utf-8"))
            self.assertEqual(summary["retrieval_method"], "local_synthetic_fixture")
            self.assertEqual(summary["captured_at_utc"], None)
            self.assertIn("ingested_at_utc", summary)

            replay_csv, sidecar = export_replay_csv(store, report, Path(directory) / "export" / "bars.csv")
            self.assertTrue(sidecar.is_file())
            original_export = replay_csv.read_bytes()
            export_replay_csv(store, report, replay_csv)  # exact rerun is idempotent
            self.assertEqual(replay_csv.read_bytes(), original_export)
            replay_csv.write_bytes(b"user data")
            with self.assertRaises(HistoricalDataError):
                export_replay_csv(store, report, replay_csv)
            self.assertEqual(replay_csv.read_bytes(), b"user data")
            replay_csv.write_bytes(original_export)
            candles = load_candles(replay_csv)
            self.assertEqual(len(candles), 3)
            result = run_replay(candles, [], SimulationConfig("1000", "SYNTHETIC_QUOTE", "0", "0", "1"), expected_interval=timedelta(seconds=60))
            self.assertEqual(result.symbol, "SYNTHETIC_XYZ")
            self.assertEqual(result.final_equity, Decimal("1000"))

    def test_strict_policy_blocks_missing_policy_stale_incomplete_and_unknown_symbol(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = DatasetStore(directory)
            imported = store.import_local(FIXTURES / "synthetic_ohlcv.csv", ctx())
            self.assertFalse(audit_dataset(store, imported.dataset_id, AuditPolicy()).replay_eligible)

            stale = audit_dataset(store, imported.dataset_id, clean_policy(as_of_utc=BASE + timedelta(minutes=10), max_age_seconds=60))
            self.assertIn("STALE_DATA", {issue.code for issue in stale.issues})
            self.assertFalse(stale.replay_eligible)

            incomplete = audit_dataset(store, imported.dataset_id, clean_policy(expected_end_utc=BASE + timedelta(minutes=3)))
            self.assertIn("INCOMPLETE_END", {issue.code for issue in incomplete.issues})
            self.assertFalse(incomplete.replay_eligible)

            unknown = audit_dataset(store, imported.dataset_id, clean_policy(known_symbols=("OTHER",)))
            self.assertIn("UNKNOWN_SYMBOL", {issue.code for issue in unknown.issues})
            self.assertFalse(unknown.replay_eligible)

    def test_duplicates_out_of_order_and_gaps_are_not_sorted_or_repaired(self) -> None:
        contents = (
            "symbol,timestamp,open,high,low,close,volume\n"
            "SYNTHETIC_XYZ,2026-01-01T00:00:00Z,10,11,9,10,1\n"
            "SYNTHETIC_XYZ,2026-01-01T00:02:00Z,10,11,9,10,1\n"
            "SYNTHETIC_XYZ,2026-01-01T00:02:00Z,10,11,9,10,1\n"
            "SYNTHETIC_XYZ,2026-01-01T00:01:00Z,10,11,9,10,1\n"
        )
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "out_of_order.csv"
            source.write_text(contents, encoding="utf-8")
            store = DatasetStore(Path(directory) / "store")
            imported = store.import_local(source, ctx())
            records = store.read_records(imported.dataset_id)
            self.assertEqual(len(records), 4)
            report = audit_dataset(store, imported.dataset_id, clean_policy())
            codes = {issue.code for issue in report.issues}
            self.assertIn("DUPLICATE_TIMESTAMP", codes)
            self.assertIn("NON_MONOTONIC_TIMESTAMP", codes)
            self.assertIn("INTERVAL_GAP", codes)
            self.assertFalse(report.replay_eligible)
            with self.assertRaises(HistoricalDataError):
                export_replay_csv(store, report, Path(directory) / "must-not-exist.csv")

    def test_csv_invalid_timestamp_decimal_and_ohlc_fail_at_import(self) -> None:
        bad_rows = (
            "symbol,timestamp,open,high,low,close,volume\nSYNTHETIC_XYZ,2026-01-01T00:00:00,10,11,9,10,1\n",
            "symbol,timestamp,open,high,low,close,volume\nSYNTHETIC_XYZ,2026-01-01T00:00:00Z,ten,11,9,10,1\n",
            "symbol,timestamp,open,high,low,close,volume\nSYNTHETIC_XYZ,2026-01-01T00:00:00Z,10,9,8,9,1\n",
        )
        with tempfile.TemporaryDirectory() as directory:
            store = DatasetStore(Path(directory) / "store")
            for index, content in enumerate(bad_rows):
                source = Path(directory) / f"bad{index}.csv"
                source.write_text(content, encoding="utf-8")
                with self.subTest(index=index), self.assertRaises(HistoricalDataError):
                    store.import_local(source, ctx())

    def test_import_identity_includes_parser_format_and_manifest_identity_is_verified(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "store"
            payload = (FIXTURES / "synthetic_markets.json").read_bytes()
            json_path = Path(directory) / "same.json"
            json_path.write_bytes(payload)
            context = ctx("market_metadata", symbol=None, interval=None)
            raw_sha = hashlib.sha256(payload).hexdigest()
            self.assertNotEqual(context.identity(raw_sha, ".json"), context.identity(raw_sha, ".jsonl"))
            store = DatasetStore(root)
            first = store.import_local(json_path, context)
            manifest = store.read_manifest(first.dataset_id)
            manifest["identity"]["input_format"] = ".jsonl"
            (store.dataset_dir(first.dataset_id) / "manifest.json").write_text(json.dumps(manifest), encoding="utf-8")
            with self.assertRaises(HistoricalDataError):
                store.read_manifest(first.dataset_id)

    def test_json_duplicate_keys_and_udf_array_length_mismatch_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = DatasetStore(Path(directory) / "store")
            duplicate = Path(directory) / "duplicate.json"
            duplicate.write_text('{"result":{"markets":[],"markets":[]}}', encoding="utf-8")
            with self.assertRaises(HistoricalDataError):
                store.import_local(duplicate, ctx("market_metadata", symbol=None, interval=None))
            mismatch = Path(directory) / "mismatch.json"
            mismatch.write_text('{"s":"ok","t":[1767225600],"o":[],"h":["11"],"l":["9"],"c":["10"],"v":["1"]}', encoding="utf-8")
            with self.assertRaises(HistoricalDataError):
                store.import_local(mismatch, ctx("candles"))

    def test_json_record_types_keep_decimal_and_time_provenance(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "store"
            store = DatasetStore(root)
            metadata = store.import_local(FIXTURES / "synthetic_markets.json", ctx("market_metadata", symbol=None, interval=None))
            metadata_record = store.read_records(metadata.dataset_id)[0]
            self.assertIsInstance(metadata_record, MarketMetadataRecord)
            self.assertEqual(metadata_record.price_precision, 2)

            trades = store.import_local(FIXTURES / "synthetic_public_trades.json", ctx("public_trades", symbol=None, interval=None))
            trade_record = store.read_records(trades.dataset_id)[0]
            self.assertIsInstance(trade_record, PublicTradeRecord)
            self.assertEqual(trade_record.price, Decimal("100.125"))

            fair = store.import_local(FIXTURES / "synthetic_fair_price.json", ctx("fair_price_snapshot", symbol=None, interval=None))
            fair_record = store.read_records(fair.dataset_id)[0]
            self.assertEqual(fair_record.prices["SYNTHETIC_XYZ"], Decimal("100.125"))
            self.assertNotIn("NOT_PRESENT", fair_record.prices)

            captured = BASE + timedelta(seconds=25)
            book = store.import_local(FIXTURES / "synthetic_depth.json", ctx("order_book_snapshot", captured=captured, symbol="SYNTHETIC_XYZ", interval=None))
            book_record = store.read_records(book.dataset_id)[0]
            self.assertIsInstance(book_record, OrderBookSnapshotRecord)
            self.assertEqual(book_record.captured_at_utc, captured)
            self.assertIsNone(book_record.source_timestamp_utc)

            side = store.import_local(FIXTURES / "synthetic_depth_side.json", ctx("order_book_side", captured=captured, symbol="SYNTHETIC_XYZ", interval=None))
            side_record = store.read_records(side.dataset_id)[0]
            self.assertIsInstance(side_record, OrderBookSideSnapshotRecord)
            self.assertEqual(side_record.side, "bid")
            self.assertNotEqual(side_record.captured_at_utc, side_record.provenance.ingested_at_utc)

    def test_udf_candles_normalize_to_feature_002_candles(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = DatasetStore(directory)
            imported = store.import_local(FIXTURES / "synthetic_udf_candles.json", ctx())
            records = store.read_records(imported.dataset_id)
            self.assertEqual(len(records), 3)
            self.assertEqual(records[0].timestamp_utc, BASE)
            self.assertEqual(records[0].to_replay_candle().open, Decimal("100"))

    def test_explicit_precision_policy_rejects_excess_scale(self) -> None:
        content = "symbol,timestamp,open,high,low,close,volume\nSYNTHETIC_XYZ,2026-01-01T00:00:00Z,10.123,11,9,10,1\nSYNTHETIC_XYZ,2026-01-01T00:01:00Z,10,11,9,10,1\n"
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "precision.csv"
            source.write_text(content, encoding="utf-8")
            store = DatasetStore(Path(directory) / "store")
            imported = store.import_local(source, ctx())
            policy = clean_policy(expected_end_utc=BASE + timedelta(minutes=1), max_decimal_places={"price": 2, "quantity": 2})
            report = audit_dataset(store, imported.dataset_id, policy)
            self.assertIn("PRECISION_EXCEEDS_POLICY", {issue.code for issue in report.issues})
            self.assertFalse(report.replay_eligible)

    def test_raw_and_normalized_tampering_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "store"
            store = DatasetStore(root)
            imported = store.import_local(FIXTURES / "synthetic_ohlcv.csv", ctx())
            manifest = store.read_manifest(imported.dataset_id)
            raw_path = root / manifest["raw_relative_path"]
            raw_path.write_bytes(raw_path.read_bytes() + b"\n")
            raw_report = audit_dataset(store, imported.dataset_id, clean_policy())
            self.assertIn("RAW_SHA256_MISMATCH", {issue.code for issue in raw_report.issues})

            normalized_path = root / "datasets" / imported.dataset_id / "records.jsonl"
            normalized_path.write_bytes(normalized_path.read_bytes() + b" ")
            normalized_report = audit_dataset(store, imported.dataset_id, clean_policy())
            self.assertIn("NORMALIZED_LOAD_FAILED", {issue.code for issue in normalized_report.issues})
            self.assertIn("NORMALIZED_SHA256_MISMATCH", {issue.code for issue in normalized_report.issues})

    def test_depth_context_requires_capture_timestamp(self) -> None:
        with self.assertRaises(HistoricalDataError):
            ctx("order_book_snapshot", captured=None, symbol="SYNTHETIC_XYZ", interval=None)

    def test_serialized_records_keep_schema_provenance_and_decimal_text(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = DatasetStore(directory)
            imported = store.import_local(FIXTURES / "synthetic_ohlcv.csv", ctx())
            raw = (store.dataset_dir(imported.dataset_id) / "records.jsonl").read_text(encoding="utf-8")
            record = json.loads(raw.splitlines()[0])
            self.assertEqual(record["schema_version"], "1.0")
            self.assertEqual(record["open"], "100")
            self.assertIn("retrieved_at_utc", record["provenance"])
            self.assertIn("ingested_at_utc", record["provenance"])
            self.assertEqual(record["provenance"]["raw_sha256"], imported.raw_sha256)


if __name__ == "__main__":
    unittest.main()
