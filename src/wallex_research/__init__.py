"""Offline, strategy-neutral market-data research primitives.

This package intentionally has no exchange, account, network, or credential adapter.
"""

from .data_quality import QualityIssue, QualityReport, audit_candles
from .csv_io import CSVDataError, load_candles
from .models import (
    Candle,
    ConfigError,
    DataError,
    LedgerPoint,
    ReplayResult,
    SimulationConfig,
    SimulatedFill,
    SimulatedOrderOutcome,
    TargetExposure,
)
from .replay import ReplayError, run_replay

__all__ = [
    "Candle",
    "CSVDataError",
    "ConfigError",
    "DataError",
    "LedgerPoint",
    "QualityIssue",
    "QualityReport",
    "ReplayError",
    "ReplayResult",
    "SimulationConfig",
    "SimulatedFill",
    "SimulatedOrderOutcome",
    "TargetExposure",
    "audit_candles",
    "load_candles",
    "run_replay",
]
