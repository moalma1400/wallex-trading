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
from .historical import (
    CODE_VERSION, CandleRecord, DatasetContext, FairPriceSnapshotRecord, HistoricalDataError,
    HistoricalDataProvider, MarketMetadataRecord, BookLevel,
    OrderBookSideSnapshotRecord, OrderBookSnapshotRecord, Provenance,
    HistoricalDataRequest, PublicTradeRecord, SCHEMA_VERSION, parse_local_bytes, record_to_dict,
)
from .dataset_store import DatasetStore, ImportResult
from .historical_quality import (
    AuditIssue, AuditPolicy, AuditReport, audit_dataset, export_replay_csv,
    write_audit_reports,
)

__all__ = [
    "Candle",
    "CODE_VERSION",
    "CandleRecord",
    "DatasetContext",
    "ImportResult",
    "DatasetStore",
    "FairPriceSnapshotRecord",
    "HistoricalDataError",
    "HistoricalDataProvider",
    "HistoricalDataRequest",
    "MarketMetadataRecord",
    "BookLevel",
    "OrderBookSideSnapshotRecord",
    "OrderBookSnapshotRecord",
    "Provenance",
    "PublicTradeRecord",
    "SCHEMA_VERSION",
    "AuditIssue",
    "AuditPolicy",
    "AuditReport",
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
    "audit_dataset",
    "export_replay_csv",
    "parse_local_bytes",
    "record_to_dict",
    "write_audit_reports",
    "load_candles",
    "run_replay",
]
