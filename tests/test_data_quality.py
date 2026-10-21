from __future__ import annotations

import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

from wallex_research.csv_io import CSVDataError, load_candles
from wallex_research.data_quality import audit_candles
from wallex_research.models import Candle, DataError


UTC = timezone.utc


def candle(minute: int, *, symbol: str = "SYNTHETIC_XYZ", close: str = "10") -> Candle:
    return Candle(
        symbol=symbol,
        timestamp=datetime(2026, 1, 1, 0, minute, tzinfo=UTC),
        open=Decimal("10"),
        high=Decimal("12"),
        low=Decimal("9"),
        close=Decimal(close),
        volume=Decimal("1.25"),
    )


class CandleModelTests(unittest.TestCase):
    def test_rejects_invalid_ohlc_and_negative_volume(self) -> None:
        with self.assertRaises(DataError):
            Candle("SYNTHETIC_XYZ", datetime.now(UTC), Decimal("10"), Decimal("9"), Decimal("8"), Decimal("9"), Decimal("1"))
        with self.assertRaises(DataError):
            Candle("SYNTHETIC_XYZ", datetime.now(UTC), Decimal("10"), Decimal("11"), Decimal("9"), Decimal("10"), Decimal("-1"))

    def test_rejects_naive_timestamp_and_binary_float(self) -> None:
        with self.assertRaises(DataError):
            Candle("SYNTHETIC_XYZ", datetime(2026, 1, 1), Decimal("10"), Decimal("11"), Decimal("9"), Decimal("10"), Decimal("1"))
        with self.assertRaises(DataError):
            Candle("SYNTHETIC_XYZ", datetime.now(UTC), 10.1, Decimal("11"), Decimal("9"), Decimal("10"), Decimal("1"))

    def test_normalizes_aware_non_utc_time(self) -> None:
        local = datetime.fromisoformat("2026-01-01T02:00:00+02:00")
        result = Candle("SYNTHETIC_XYZ", local, Decimal("10"), Decimal("11"), Decimal("9"), Decimal("10"), Decimal("1"))
        self.assertEqual(result.timestamp, datetime(2026, 1, 1, tzinfo=UTC))


class DataQualityTests(unittest.TestCase):
    def test_valid_fixture_preserves_decimal_values(self) -> None:
        path = Path(__file__).parent / "fixtures" / "synthetic_ohlcv.csv"
        rows = load_candles(path)
        report = audit_candles(rows, expected_interval=timedelta(minutes=1))
        self.assertTrue(report.is_valid, report.issues)
        self.assertEqual(rows[0].volume, Decimal("12.5"))
        self.assertEqual(rows[1].timestamp.tzinfo, UTC)

    def test_duplicates_non_monotonic_and_mixed_symbols_are_issues(self) -> None:
        rows = [candle(0), candle(0), candle(2, symbol="OTHER")]
        codes = {issue.code for issue in audit_candles(rows).issues}
        self.assertIn("DUPLICATE_TIMESTAMP", codes)
        self.assertIn("NON_MONOTONIC_TIMESTAMP", codes)
        self.assertIn("MIXED_SYMBOLS", codes)

    def test_interval_gaps_are_reported_but_not_filled(self) -> None:
        rows = [candle(0), candle(2)]
        report = audit_candles(rows, expected_interval=timedelta(minutes=1))
        self.assertFalse(report.is_valid)
        self.assertIn("INTERVAL_GAP", {issue.code for issue in report.issues})
        self.assertEqual(len(rows), 2)

    def test_missing_interval_leaves_cadence_unknown(self) -> None:
        report = audit_candles([candle(0), candle(5)])
        self.assertTrue(report.is_valid)
        self.assertFalse(any(issue.code == "INTERVAL_GAP" for issue in report.issues))

    def test_csv_rejects_naive_time_and_schema_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "bad.csv"
            path.write_text("symbol,timestamp,open,high,low,close,volume\nX,2026-01-01T00:00:00,10,11,9,10,1\n", encoding="utf-8")
            with self.assertRaises(CSVDataError):
                load_candles(path)
            path.write_text("symbol,timestamp,open,high,low,close\n", encoding="utf-8")
            with self.assertRaises(CSVDataError):
                load_candles(path)


if __name__ == "__main__":
    unittest.main()
