#!/usr/bin/env python
"""Tests for chronological walk-forward splits and leakage prevention.

These tests use synthetic timestamps only and never touch the network or
any exchange, strategy, or account input.  They assert boundaries, explicit
splits, determinism, and fail-closed validation of under-supplied windows.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timedelta, timezone

from wallex_research.walkforward import (
    TimeWindow,
    WalkForwardConfig,
    WalkForwardError,
    WalkForwardResult,
    _ensure_aware,
    build_rolling_windows,
    split_observations,
    validate_walk_forward_config,
)

UTC = timezone.utc
AWARE = datetime(2026, 1, 1, tzinfo=UTC)
BASE = AWARE


def _day_points(count: int) -> list[datetime]:
    return [BASE + timedelta(days=i) for i in range(count)]


def _tz_points(count: int, offset_hours: int = 3) -> list[datetime]:
    """Daily points in a fixed non-UTC timezone; same UTC instants as _day_points."""
    tz = timezone(timedelta(hours=offset_hours))
    first = datetime(2026, 1, 1, 3, tzinfo=tz)  # == 2026-01-01T00:00Z
    return [first + timedelta(days=i) for i in range(count)]


# ---------------------------------------------------------------------------
#  _ensure_aware
# ---------------------------------------------------------------------------

class EnsureAwareTests(unittest.TestCase):
    def test_accepts_utc(self) -> None:
        self.assertEqual(_ensure_aware(BASE), BASE)

    def test_accepts_non_utc_offset(self) -> None:
        off = datetime(2026, 1, 1, 3, tzinfo=timezone(timedelta(hours=3)))
        result = _ensure_aware(off)
        self.assertEqual(result, BASE)

    def test_rejects_naive(self) -> None:
        with self.assertRaises(WalkForwardError):
            _ensure_aware(datetime(2026, 1, 1))

    def test_rejects_non_datetime(self) -> None:
        with self.assertRaises(WalkForwardError):
            _ensure_aware("2026-01-01")  # type: ignore[arg-type]

    def test_rejects_bool(self) -> None:
        with self.assertRaises(WalkForwardError):
            _ensure_aware(True)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
#  TimeWindow
# ---------------------------------------------------------------------------

class TimeWindowTests(unittest.TestCase):
    def test_requires_aware_utc_boundaries(self) -> None:
        with self.assertRaises(WalkForwardError):
            TimeWindow("train", datetime(2026, 1, 1), datetime(2026, 1, 2, tzinfo=UTC))
        with self.assertRaises(WalkForwardError):
            TimeWindow("train", BASE, datetime(2026, 1, 2))

    def test_end_must_follow_start(self) -> None:
        with self.assertRaises(WalkForwardError):
            TimeWindow("test", BASE + timedelta(days=2), BASE + timedelta(days=1))

    def test_contains_is_half_open(self) -> None:
        w = TimeWindow("test", BASE, BASE + timedelta(days=1))
        self.assertTrue(w.contains(BASE))
        self.assertTrue(w.contains(BASE + timedelta(hours=23)))
        self.assertFalse(w.contains(BASE + timedelta(days=1)))

    def test_normalizes_to_utc(self) -> None:
        off = datetime.fromisoformat("2026-01-01T03:30:00+03:30")
        w = TimeWindow("train", off, off + timedelta(hours=1))
        self.assertEqual(w.start, datetime(2026, 1, 1, tzinfo=UTC))

    def test_contains_rejects_naive(self) -> None:
        w = TimeWindow("train", BASE, BASE + timedelta(days=1))
        with self.assertRaises(WalkForwardError):
            w.contains(datetime(2026, 1, 1))

    def test_contains_handles_offsets(self) -> None:
        w = TimeWindow("train", BASE, BASE + timedelta(days=2))
        off = _tz_points(1)[0]
        self.assertTrue(w.contains(off))  # same UTC instant


# ---------------------------------------------------------------------------
#  WalkForwardConfig
# ---------------------------------------------------------------------------

class WalkForwardConfigTests(unittest.TestCase):
    def test_train_after_test_is_rejected(self) -> None:
        with self.assertRaises(WalkForwardError):
            WalkForwardConfig(
                train_window=TimeWindow("train", BASE + timedelta(days=2), BASE + timedelta(days=3)),
                test_window=TimeWindow("test", BASE, BASE + timedelta(days=1)),
            )

    def test_validation_overflow_is_rejected(self) -> None:
        with self.assertRaises(WalkForwardError):
            WalkForwardConfig(
                train_window=TimeWindow("train", BASE, BASE + timedelta(days=1)),
                test_window=TimeWindow("test", BASE + timedelta(days=2), BASE + timedelta(days=3)),
                validation_window=TimeWindow("val", BASE + timedelta(hours=12), BASE + timedelta(days=5)),
            )

    def test_adjacent_windows_accepted(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=6)),
            test_window=TimeWindow("test", BASE + timedelta(days=6), BASE + timedelta(days=8)),
            validation_window=TimeWindow("val", BASE + timedelta(days=5), BASE + timedelta(days=6)),
        )
        self.assertEqual(c.min_train_observations, 10)

    def test_rejects_naive_train_boundary(self) -> None:
        with self.assertRaises(WalkForwardError):
            WalkForwardConfig(
                train_window=TimeWindow("train", datetime(2026, 1, 1), BASE + timedelta(days=1)),
                test_window=TimeWindow("test", BASE + timedelta(days=2), BASE + timedelta(days=3)),
            )


# ---------------------------------------------------------------------------
#  build_rolling_windows
# ---------------------------------------------------------------------------

class BuildRollingWindowsTests(unittest.TestCase):
    def test_expanding_cycles_without_overlap(self) -> None:
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=30),
            train_duration=timedelta(days=10), test_duration=timedelta(days=5),
        )
        self.assertGreater(len(cycles), 1)
        for c in cycles:
            self.assertLessEqual(c.train_window.end, c.test_window.start)
        self.assertGreater(cycles[1].train_window.end, cycles[0].train_window.end)

    def test_validation_window(self) -> None:
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=30),
            train_duration=timedelta(days=10), test_duration=timedelta(days=5),
            validation_duration=timedelta(days=1),
        )
        self.assertIsNotNone(cycles[0].validation_window)

    def test_too_short_range(self) -> None:
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                BASE, BASE + timedelta(days=10),
                train_duration=timedelta(days=10), test_duration=timedelta(days=5),
            )

    def test_rejects_naive_first_candle(self) -> None:
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                datetime(2026, 1, 1), BASE + timedelta(days=30),
                train_duration=timedelta(days=5), test_duration=timedelta(days=2),
            )

    def test_rejects_naive_last_candle(self) -> None:
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                BASE, datetime(2026, 1, 31),
                train_duration=timedelta(days=5), test_duration=timedelta(days=2),
            )

    def test_rejects_zero_train_duration(self) -> None:
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                BASE, BASE + timedelta(days=30),
                train_duration=timedelta(0), test_duration=timedelta(days=5),
            )

    def test_rejects_negative_train_duration(self) -> None:
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                BASE, BASE + timedelta(days=30),
                train_duration=timedelta(days=-1), test_duration=timedelta(days=5),
            )

    def test_rejects_zero_test_duration(self) -> None:
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                BASE, BASE + timedelta(days=30),
                train_duration=timedelta(days=5), test_duration=timedelta(0),
            )

    def test_rejects_negative_validation_duration(self) -> None:
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                BASE, BASE + timedelta(days=30),
                train_duration=timedelta(days=5), test_duration=timedelta(days=2),
                validation_duration=timedelta(days=-1),
            )

    def test_zero_validation_no_window(self) -> None:
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=30),
            train_duration=timedelta(days=10), test_duration=timedelta(days=5),
            validation_duration=timedelta(0),
        )
        self.assertIsNone(cycles[0].validation_window)

    def test_accepts_non_utc_timezone(self) -> None:
        tz = timezone(timedelta(hours=5, minutes=30))
        first = datetime(2026, 1, 1, 5, 30, tzinfo=tz)
        last = datetime(2026, 1, 15, 5, 30, tzinfo=tz)
        cycles = build_rolling_windows(
            first, last,
            train_duration=timedelta(days=5), test_duration=timedelta(days=3),
        )
        self.assertGreater(len(cycles), 1)

    def test_validation_duration_equals_train(self) -> None:
        """Validation duration == train duration: valid, but falls back to full train window."""
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=30),
            train_duration=timedelta(days=10), test_duration=timedelta(days=5),
            validation_duration=timedelta(days=10),
        )
        # validation window should span the whole train window
        v = cycles[0].validation_window
        self.assertIsNotNone(v)
        self.assertEqual(v.start, cycles[0].train_window.start)
        self.assertEqual(v.end, cycles[0].train_window.end)

    def test_validation_duration_greater_than_train(self) -> None:
        """Validation duration > train duration: clipped to full train window."""
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=30),
            train_duration=timedelta(days=7), test_duration=timedelta(days=5),
            validation_duration=timedelta(days=14),
        )
        v = cycles[0].validation_window
        self.assertIsNotNone(v)
        self.assertEqual(v.start, cycles[0].train_window.start)
        self.assertEqual(v.end, cycles[0].train_window.end)


# ---------------------------------------------------------------------------
#  split_observations
# ---------------------------------------------------------------------------

class SplitObservationsTests(unittest.TestCase):
    def test_split_exact_and_deterministic(self) -> None:
        config = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            min_train_observations=1,
        )
        points = _day_points(14)
        tr, va, te = split_observations(points, config)
        self.assertEqual(len(tr), 10)
        self.assertEqual(len(te), 2)
        self.assertEqual(len(va), 0)
        self.assertEqual(split_observations(points, config), split_observations(points, config))

    def test_out_of_window_discarded(self) -> None:
        config = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=5)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            min_train_observations=1,
        )
        tr, va, te = split_observations(_day_points(14), config)
        self.assertEqual(len(tr), 5)
        self.assertEqual(len(te), 2)
        self.assertEqual(len(va), 0)

    def test_validation_excluded_from_train(self) -> None:
        config = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            validation_window=TimeWindow("val", BASE + timedelta(days=8), BASE + timedelta(days=10)),
            min_train_observations=1,
        )
        points = _day_points(14)  # days 0..13
        tr, va, te = split_observations(points, config)
        self.assertEqual(len(tr), 8)   # days 0-7
        self.assertEqual(len(va), 2)   # days 8-9
        self.assertEqual(len(te), 2)   # days 10-11

    def test_rejects_naive_timestamps(self) -> None:
        config = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=5)),
            test_window=TimeWindow("test", BASE + timedelta(days=5), BASE + timedelta(days=7)),
            min_train_observations=1,
        )
        naive_points = [datetime(2026, 1, d) for d in range(1, 8)]
        with self.assertRaises(WalkForwardError):
            split_observations(naive_points, config)

    def test_handles_offset_timestamps(self) -> None:
        config = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=5)),
            test_window=TimeWindow("test", BASE + timedelta(days=5), BASE + timedelta(days=7)),
            min_train_observations=1,
        )
        points = _tz_points(10, offset_hours=3)
        tr, va, te = split_observations(points, config)
        self.assertEqual(len(tr), 5)
        self.assertEqual(len(te), 2)

    def test_no_overlap_across_partitions(self) -> None:
        """A timestamp must never appear in more than one partition."""
        config = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            validation_window=TimeWindow("val", BASE + timedelta(days=7), BASE + timedelta(days=10)),
            min_train_observations=1,
        )
        points = _day_points(14)
        tr, va, te = split_observations(points, config)
        all_assigned = set(tr) | set(va) | set(te)
        self.assertEqual(len(tr) + len(va) + len(te), len(all_assigned))


# ---------------------------------------------------------------------------
#  validate_walk_forward_config
# ---------------------------------------------------------------------------

class ValidateWalkForwardConfigTests(unittest.TestCase):
    def test_valid_no_errors(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            min_train_observations=5,
        )
        self.assertEqual(validate_walk_forward_config([c], _day_points(14)), [])

    def test_insufficient_train(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=2)),
            test_window=TimeWindow("test", BASE + timedelta(days=3), BASE + timedelta(days=4)),
            min_train_observations=10,
        )
        self.assertTrue(any("train window" in e for e in validate_walk_forward_config([c], _day_points(14))))

    def test_empty_test_window(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=2)),
            test_window=TimeWindow("test", BASE + timedelta(days=20), BASE + timedelta(days=25)),
            min_train_observations=1,
        )
        self.assertTrue(any("zero observations" in e for e in validate_walk_forward_config([c], _day_points(14))))

    def test_strict_test_size_enforced(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            min_train_observations=1,
        )
        self.assertTrue(any("test window has" in e for e in validate_walk_forward_config([c], _day_points(14), strict_test_size=5)))

    def test_empty_cycles_produces_error(self) -> None:
        """Empty cycle list must not pass validation silently."""
        errors = validate_walk_forward_config([], _day_points(14))
        self.assertTrue(errors)
        self.assertTrue(any("No walk-forward cycles" in e for e in errors))

    def test_empty_timestamps_produces_error(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            min_train_observations=1,
        )
        errors = validate_walk_forward_config([c], [])
        self.assertTrue(errors)
        self.assertTrue(any("No timestamps" in e for e in errors))

    def test_validation_excluded_from_effective_train_count(self) -> None:
        """Effective training count must exclude validation observations."""
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            validation_window=TimeWindow("val", BASE + timedelta(days=7), BASE + timedelta(days=10)),
            min_train_observations=9,  # 10 raw - 3 validation = 7 effective → fails
        )
        errors = validate_walk_forward_config([c], _day_points(14))
        self.assertTrue(any("effective" in e and "assigned to validation" in e for e in errors))

    def test_insufficient_effective_train_without_val_note_when_no_val(self) -> None:
        """No 'assigned to validation' note when validation partition is absent."""
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=2)),
            test_window=TimeWindow("test", BASE + timedelta(days=3), BASE + timedelta(days=4)),
            min_train_observations=10,
        )
        errors = validate_walk_forward_config([c], _day_points(14))
        self.assertTrue(any("train window" in e for e in errors))
        self.assertFalse(any("assigned to validation" in e for e in errors))

    def test_rejects_naive_timestamps(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=5)),
            test_window=TimeWindow("test", BASE + timedelta(days=5), BASE + timedelta(days=7)),
            min_train_observations=1,
        )
        naive_points = [datetime(2026, 1, d) for d in range(1, 8)]
        with self.assertRaises(WalkForwardError):
            validate_walk_forward_config([c], naive_points)

    def test_handles_offset_timestamps(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=5)),
            test_window=TimeWindow("test", BASE + timedelta(days=5), BASE + timedelta(days=7)),
            min_train_observations=1,
        )
        points = _tz_points(10, offset_hours=3)
        errors = validate_walk_forward_config([c], points)
        self.assertEqual(errors, [])

    def test_strict_test_size_rejects_zero(self) -> None:
        """strict_test_size=0 must be rejected, not silently accepted."""
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            min_train_observations=1,
        )
        points = _day_points(14)
        errors = validate_walk_forward_config([c], points, strict_test_size=0)
        self.assertTrue(any("strict_test_size" in e for e in errors),
                        f"Expected strict_test_size error, got: {errors}")

    def test_strict_test_size_rejects_negative(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            min_train_observations=1,
        )
        errors = validate_walk_forward_config([c], _day_points(14), strict_test_size=-3)
        self.assertTrue(any("strict_test_size" in e for e in errors))

    def test_strict_test_size_rejects_bool(self) -> None:
        c = WalkForwardConfig(
            train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
            test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
            min_train_observations=1,
        )
        errors = validate_walk_forward_config([c], _day_points(14), strict_test_size=True)  # type: ignore[arg-type]
        self.assertTrue(any("strict_test_size" in e for e in errors))

    def test_min_train_observations_rejects_bool(self) -> None:
        with self.assertRaises(WalkForwardError):
            WalkForwardConfig(
                train_window=TimeWindow("train", BASE, BASE + timedelta(days=10)),
                test_window=TimeWindow("test", BASE + timedelta(days=10), BASE + timedelta(days=12)),
                min_train_observations=True,  # type: ignore[arg-type]
            )
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                BASE, BASE + timedelta(days=30),
                train_duration=timedelta(days=10), test_duration=timedelta(days=5),
                min_train_observations=True,  # type: ignore[arg-type]
            )


# ---------------------------------------------------------------------------
#  Integration tests  (build_rolling_windows → split_observations → validate)
# ---------------------------------------------------------------------------

class IntegrationTests(unittest.TestCase):
    def test_expanding_walk_forward_flow(self) -> None:
        """End-to-end: build cycles, split, validate — correct counts."""
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=40),
            train_duration=timedelta(days=10),
            test_duration=timedelta(days=5),
            validation_duration=timedelta(days=2),
            min_train_observations=3,
        )
        self.assertGreater(len(cycles), 1)

        points = _day_points(42)
        errors = validate_walk_forward_config(cycles, points)
        self.assertEqual(errors, [], f"Expected clean validation, got: {errors}")

        # spot-check first cycle
        tr, va, te = split_observations(points, cycles[0])
        self.assertEqual(len(tr), 8)   # days 0-7 (10 raw - 2 validation)
        self.assertEqual(len(va), 2)   # days 8-9
        self.assertEqual(len(te), 5)   # days 10-14

    def test_integration_insufficient_effective_train(self) -> None:
        """Validation partition reduces effective train below minimum."""
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=20),
            train_duration=timedelta(days=10),
            test_duration=timedelta(days=5),
            validation_duration=timedelta(days=9),  # only 1 day left for training
            min_train_observations=5,
        )
        points = _day_points(22)
        errors = validate_walk_forward_config(cycles, points)
        self.assertTrue(any("effective" in e for e in errors),
                        "Should flag insufficient effective training data")

    def test_integration_validation_duration_eq_train(self) -> None:
        """Validation == train duration reduces effective train to 0."""
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=20),
            train_duration=timedelta(days=7),
            test_duration=timedelta(days=5),
            validation_duration=timedelta(days=7),  # validation = train
            min_train_observations=1,
        )
        points = _day_points(22)
        errors = validate_walk_forward_config(cycles, points)
        # Effective train should be 0 because validation covers the whole train period
        self.assertTrue(any("effective" in e for e in errors),
                        "Should flag zero effective training data")

    def test_integration_validation_duration_greater_than_train(self) -> None:
        """Validation > train duration: fail closed with zero effective training."""
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=25),
            train_duration=timedelta(days=5),
            test_duration=timedelta(days=5),
            validation_duration=timedelta(days=20),
            min_train_observations=1,
        )
        points = _day_points(27)
        errors = validate_walk_forward_config(cycles, points)
        self.assertTrue(any("effective" in e for e in errors),
                        "Should flag zero effective training data")

    def test_integration_non_utc_offsets(self) -> None:
        """Timestamps in non-UTC timezones produce correct deterministic splits."""
        tz = timezone(timedelta(hours=5, minutes=30))
        first = datetime(2026, 1, 1, 5, 30, tzinfo=tz)
        last = datetime(2026, 1, 31, 5, 30, tzinfo=tz)
        cycles = build_rolling_windows(
            first, last,
            train_duration=timedelta(days=10),
            test_duration=timedelta(days=5),
            validation_duration=timedelta(days=2),
            min_train_observations=2,
        )
        points = [first + timedelta(days=i) for i in range(31)]
        errors = validate_walk_forward_config(cycles, points)
        self.assertEqual(errors, [])

        # First cycle split
        tr, va, te = split_observations(points, cycles[0])
        self.assertEqual(len(tr), 8)  # 10 raw - 2 validation suffix
        self.assertEqual(len(va), 2)
        self.assertEqual(len(te), 5)

    def test_integration_naive_timestamps_rejected(self) -> None:
        with self.assertRaises(WalkForwardError):
            build_rolling_windows(
                datetime(2026, 1, 1), BASE + timedelta(days=30),
                train_duration=timedelta(days=5), test_duration=timedelta(days=2),
            )

    def test_integration_no_overlap(self) -> None:
        """Across all cycles, no timestamp is assigned to both train and test."""
        cycles = build_rolling_windows(
            BASE, BASE + timedelta(days=40),
            train_duration=timedelta(days=10),
            test_duration=timedelta(days=5),
            min_train_observations=1,
        )
        points = _day_points(42)
        for cycle in cycles:
            tr, va, te = split_observations(points, cycle)
            self.assertEqual(set(tr) & set(te), set())
            if va:
                self.assertEqual(set(tr) & set(va), set())
                self.assertEqual(set(te) & set(va), set())


if __name__ == "__main__":
    unittest.main()