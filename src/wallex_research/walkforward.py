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


def _ensure_aware(ts: datetime, name: str = "timestamp") -> datetime:
    """Validate timezone awareness and normalize to UTC.

    Raises WalkForwardError if *ts* is not timezone-aware or not a datetime.
    Returns a UTC-normalized datetime.
    """
    if not isinstance(ts, datetime):
        raise WalkForwardError(f"{name} must be a datetime, got {type(ts).__name__}")
    if ts.tzinfo is None or ts.utcoffset() is None:
        raise WalkForwardError(f"{name} must be timezone-aware")
    return ts.astimezone(UTC)


def _positive_int(value: object, name: str) -> int:
    """Validate an explicit positive integer, rejecting booleans explicitly."""
    if isinstance(value, bool) or not isinstance(value, int) or value < 1:
        raise WalkForwardError(f"{name} must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class TimeWindow:
    """A named temporal range for one phase of evaluation."""

    label: str
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
        ts = _ensure_aware(timestamp)
        return self.start <= ts < self.end


@dataclass(frozen=True, slots=True)
class WalkForwardConfig:
    """Configuration for one walk-forward cycle using expanding training window."""

    train_window: TimeWindow
    test_window: TimeWindow
    validation_window: TimeWindow | None = None
    min_train_observations: int = 10

    def __post_init__(self) -> None:
        _positive_int(self.min_train_observations, "min_train_observations")
        if self.train_window.end.astimezone(UTC) > self.test_window.start.astimezone(UTC):
            raise WalkForwardError("Train window must end before test window starts")
        if self.validation_window is not None:
            if self.validation_window.start.astimezone(UTC) < self.train_window.start.astimezone(UTC):
                raise WalkForwardError("Validation window cannot start before train window")
            if self.validation_window.end.astimezone(UTC) > self.test_window.start.astimezone(UTC):
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


def build_rolling_windows(
    first_candle_time: datetime,
    last_candle_time: datetime,
    *,
    train_duration: timedelta,
    test_duration: timedelta,
    validation_duration: timedelta | None = None,
    min_train_observations: int = 10,
) -> list[WalkForwardConfig]:
    first = _ensure_aware(first_candle_time, "first_candle_time")
    last = _ensure_aware(last_candle_time, "last_candle_time")

    if last <= first:
        raise WalkForwardError("Candle time range start must precede end")
    if not isinstance(train_duration, timedelta) or train_duration <= timedelta(0):
        raise WalkForwardError("train_duration must be a positive timedelta")
    if not isinstance(test_duration, timedelta) or test_duration <= timedelta(0):
        raise WalkForwardError("test_duration must be a positive timedelta")
    if validation_duration is not None and (
        not isinstance(validation_duration, timedelta) or validation_duration < timedelta(0)
    ):
        raise WalkForwardError("validation_duration must be a non-negative timedelta when provided")
    _positive_int(min_train_observations, "min_train_observations")

    cycles: list[WalkForwardConfig] = []
    offset = timedelta(0)
    max_attempts = 10000

    while True:
        train_end = first + train_duration + offset
        test_start = train_end
        test_end = test_start + test_duration

        if test_end > last:
            break

        train = TimeWindow("train", first, train_end)
        test = TimeWindow("test", test_start, test_end)
        val: TimeWindow | None = None
        if validation_duration is not None and validation_duration > timedelta(0):
            val_start = train_end - validation_duration
            if val_start < first:
                val_start = first
            if val_start < train_end:
                val = TimeWindow("validation", val_start, train_end)

        cycles.append(WalkForwardConfig(
            train_window=train, test_window=test, validation_window=val,
            min_train_observations=min_train_observations,
        ))
        offset += test_duration
        if len(cycles) >= max_attempts:
            raise WalkForwardError("Infinite loop guard triggered")

    if not cycles:
        raise WalkForwardError("Time range too short for any walk-forward cycle")
    return cycles


def split_observations(
    timestamps: Sequence[datetime],
    config: WalkForwardConfig,
) -> tuple[list[datetime], list[datetime], list[datetime]]:
    train: list[datetime] = []
    validation: list[datetime] = []
    test: list[datetime] = []

    for ts in timestamps:
        aware = _ensure_aware(ts)
        if config.test_window.contains(aware):
            test.append(aware)
        elif config.validation_window is not None and config.validation_window.contains(aware):
            validation.append(aware)
        elif config.train_window.contains(aware):
            train.append(aware)

    return train, validation, test


def validate_walk_forward_config(
    cycles: list[WalkForwardConfig],
    all_timestamps: Sequence[datetime],
    *,
    strict_test_size: int | None = None,
) -> list[str]:
    errors: list[str] = []

    if not cycles:
        return ["No walk-forward cycles provided for validation"]

    if strict_test_size is not None:
        try:
            _positive_int(strict_test_size, "strict_test_size")
        except WalkForwardError as exc:
            errors.append(str(exc))

    sorted_times = sorted(_ensure_aware(ts) for ts in all_timestamps)
    if not sorted_times:
        return ["No timestamps available for walk-forward validation"]

    for idx, cycle in enumerate(cycles):
        label = f"Cycle {idx}"
        train, validation, test = split_observations(sorted_times, cycle)
        effective_train = len(train)
        if effective_train < cycle.min_train_observations:
            val_note = f" ({len(validation)} assigned to validation)" if validation else ""
            errors.append(
                f"{label}: train window has {effective_train} effective observations"
                f"{val_note}, "
                f"need at least {cycle.min_train_observations}"
            )
        if not test:
            errors.append(f"{label}: test window has zero observations")
        if strict_test_size is not None and len(test) < strict_test_size:
            errors.append(
                f"{label}: test window has {len(test)} observations, "
                f"need at least {strict_test_size}"
            )
    return errors