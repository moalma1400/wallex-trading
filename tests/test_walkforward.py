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
    build_rolling_windows,
    split_observations,
    validate_walk_forward_config,
)

UTC = timezone.utc
BASE = datetime(2026, 1, 1, tzinfo=UTC)


def _day_points(count: int) -> list[datetime]:
    return [BASE + timedelta(days=i) for i in range(count)]


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


if __name__ == "__main__":
    unittest.main()
