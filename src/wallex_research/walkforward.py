#!/usr/bin/env python
"""Chronological walk-forward evaluation with explicit train/validation/test split.

Prevents future-data leakage by enforcing temporal boundaries.  The split is
deterministic for identical configuration and input.  No strategy backtesting,
profitability claim, or live-trading authorization is implied.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Sequence


UTC = timezone.utc


class WalkForwardError(ValueError):
    """Walk-forward configuration or split violates leakage-prevention rules."""


@dataclass(frozen=True, slots=True)
class TimeWindow:
    """A named temporal range for one phase of evaluation."""

    label: str  # "train" | "validation" | "test"
    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        for field, name in ((self.start, "start"), (self.end, "end")):
            if not isinstance(field, datetime):
                raise WalkForwardError(f"{name} must be a datetime")
            if field.tzinfo is None or field.utcoffset() is None:
                raise WalkForwardError(f"{name} must be timezone-aware")
        start_utc = self.start.astimezone(UTC)
        end_utc = self.end.astimezone(UTC)
        if end_utc <= start_utc:
            raise WalkForwardError(f"TimeWindow '{self.label}' end must be after start")
        object.__setattr__(self, "start", start_utc)
        object.__setattr__(self, "end", end_utc)

    def contains(self, timestamp: datetime) -> bool:
        """Check whether a UTC-aware timestamp falls within [start, end)."""
        ts = timestamp.astimezone(UTC)
        return self.start <= ts < self.end

    @property
    def duration(self) -> timedelta:
        return self.end - self.start


@dataclass(frozen=True, slots=True)
class WalkForwardConfig:
    """Configuration for one walk-forward cycle.

    Multiple cycles form a walk-forward chain.  Training always starts at the
    earliest available timestamp and expands forward; the train window's
    end advances by ``test_duration`` each cycle so that earlier cycles train
    on a subset of what later cycles see.
    """

    train_window: TimeWindow
    test_window: TimeWindow
    validation_window: TimeWindow | None = None
    min_train_observations: int = 10

    def __post_init__(self) -> None:
        if not isinstance(self.min_train_observations, int) or self.min_train_observations < 1:
            raise WalkForwardError("min_train_observations must be a positive integer")
        if self.train_window.end.astimezone(UTC) > self.test_window.start.astimezone(UTC):
            raise WalkForwardError("Train window must end before test window starts (no overlap)")
        if self.validation_window is not None:
            v_start = self.validation_window.start.astimezone(UTC)
            v_end = self.validation_window.end.astimezone(UTC)
            if v_start < self.train_window.start.astimezone(UTC):
                raise WalkForwardError("Validation window cannot start before train window")
            if v_end > self.test_window.start.astimezone(UTC):
                raise WalkForwardError("Validation window must end before test window starts")


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    """Result of one walk-forward evaluation cycle."""

    cycle_index: int
    config: WalkForwardConfig
    train_observations: int
    validation_observations: int | None
    test_observations: int
    errors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class WalkForwardResult:
    """Result of one walk-forward evaluation cycle."""

    cycle_index: int
    config: WalkForwardConfig
    train_observations: int
    validation_observations: int | None
    test_observations: int
    errors: tuple[str, ...]


def build_rolling_windows(
    first_candle_time: datetime,
    last_candle_time: datetime,
    *,
    train_duration: timedelta,
    test_duration: timedelta,
    validation_duration: timedelta | None = None,
    min_train_observations: int = 10,
) -> list[WalkForwardConfig]:
    """Build walk-forward cycles using an expanding training window.

    Each cycle slides forward by ``test_duration``.  The training window
    **always starts at** ``first_candle_time`` and its end advances by
    ``test_duration`` each cycle.  The validation window, when configured,
    occupies the last ``validation_duration`` of the training window.
    """
    first = first_candle_time.astimezone(UTC)
    last = last_candle_time.astimezone(UTC)
    if last <= first:
        raise WalkForwardError("Candle time range start must precede end")

    cycles: list[WalkForwardConfig] = []
    offset = timedelta(0)
    cycle_index = 0
    max_attempts = 10000  # safety guard

    while True:
        train_start = first
        train_end = first + train_duration + offset

        test_start = train_end
        test_end = test_start + test_duration

        if test_end > last:
            break

        train = TimeWindow("train", train_start, train_end)
        test = TimeWindow("test", test_start, test_end)
        val: TimeWindow | None = None
        if validation_duration is not None and validation_duration > timedelta(0):
            val_start = train_end - validation_duration
            if val_start < train_start:
                val_start = train_start
            if val_start < train_end:
                val = TimeWindow("validation", val_start, train_end)

        config = WalkForwardConfig(
            train_window=train,
            test_window=test,
            validation_window=val,
            min_train_observations=min_train_observations,
        )
        cycles.append(config)
        cycle_index += 1
        offset += test_duration

        if cycle_index >= max_attempts:
            raise WalkForwardError("Infinite loop guard triggered")

    if not cycles:
        raise WalkForwardError("Time range too short for any walk-forward cycle")

    return cycles


def split_observations(
    timestamps: Sequence[datetime],
    config: WalkForwardConfig,
) -> tuple[list[datetime], list[datetime], list[datetime]]:
    """Partition timestamps into train/validation/test.

    Returns (train, validation, test) lists.  Timestamps outside all
    windows are discarded without error.
    """
    train: list[datetime] = []
    validation: list[datetime] = []
    test: list[datetime] = []

    for ts in timestamps:
        aware_ts = ts.astimezone(UTC)
        if config.test_window.contains(aware_ts):
            test.append(aware_ts)
        elif config.validation_window is not None and config.validation_window.contains(aware_ts):
            validation.append(aware_ts)
        elif config.train_window.contains(aware_ts):
            train.append(aware_ts)

    return train, validation, test


def validate_walk_forward_config(
    cycles: list[WalkForwardConfig],
    all_timestamps: Sequence[datetime],
    *,
    strict_test_size: int | None = None,
) -> list[str]:
    """Validate walk-forward configuration against available timestamps.

    Returns a list of error messages (empty = no errors).
    """
    errors: list[str] = []
    sorted_times = sorted(ts.astimezone(UTC) for ts in all_timestamps)
    if not sorted_times:
        return ["No timestamps available for walk-forward validation"]

    for idx, cycle in enumerate(cycles):
        label = f"Cycle {idx}"
        train_times = [ts for ts in sorted_times if cycle.train_window.contains(ts)]
        if len(train_times) < cycle.min_train_observations:
            errors.append(
                f"{label}: train window has {len(train_times)} observations, "
                f"need at least {cycle.min_train_observations}"
            )

        test_times = [ts for ts in sorted_times if cycle.test_window.contains(ts)]
        if not test_times:
            errors.append(f"{label}: test window has zero observations")
        if strict_test_size is not None and len(test_times) < strict_test_size:
            errors.append(
                f"{label}: test window has {len(test_times)} observations, "
                f"need at least {strict_test_size}"
            )

    return errors
