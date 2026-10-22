"""Deterministic OHLCV validation. Findings never cause automatic data repair."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Iterable

from .models import Candle


@dataclass(frozen=True, slots=True)
class QualityIssue:
    code: str
    severity: str
    row: int | None
    message: str


@dataclass(frozen=True, slots=True)
class QualityReport:
    rows_checked: int
    issues: tuple[QualityIssue, ...]
    cadence_checked: bool

    @property
    def is_valid(self) -> bool:
        return not any(issue.severity == "error" for issue in self.issues)


def audit_candles(candles: Iterable[Candle], *, expected_interval: timedelta | None = None) -> QualityReport:
    rows = list(candles)
    issues: list[QualityIssue] = []
    if expected_interval is not None and expected_interval <= timedelta(0):
        raise ValueError("expected_interval must be greater than zero")
    if not rows:
        return QualityReport(0, (QualityIssue("EMPTY_DATASET", "error", None, "dataset contains no candles"),), expected_interval is not None)

    first_symbol = rows[0].symbol
    seen: set = set()
    previous: Candle | None = None
    for index, current in enumerate(rows, start=1):
        if current.symbol != first_symbol:
            issues.append(QualityIssue("MIXED_SYMBOLS", "error", index, "single-series dataset contains more than one symbol"))
        if current.timestamp in seen:
            issues.append(QualityIssue("DUPLICATE_TIMESTAMP", "error", index, "timestamp is repeated; data is not deduplicated"))
        seen.add(current.timestamp)
        if previous is not None:
            delta = current.timestamp - previous.timestamp
            if delta <= timedelta(0):
                issues.append(QualityIssue("NON_MONOTONIC_TIMESTAMP", "error", index, "timestamps must be strictly increasing; rows are not sorted"))
            if expected_interval is not None and delta != expected_interval:
                code = "INTERVAL_GAP" if delta > expected_interval else "INTERVAL_MISMATCH"
                issues.append(QualityIssue(code, "error", index, f"observed interval {delta} differs from explicitly supplied interval {expected_interval}"))
        previous = current
    return QualityReport(len(rows), tuple(issues), expected_interval is not None)
