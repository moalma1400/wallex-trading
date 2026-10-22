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
from .challenge import (
    ChallengeModePolicy, ChallengePolicyError, DisabledPairRegistry,
    EligibilityDecision, MarketRequest, MarketSnapshot, build_disabled_pair_registry,
    is_challenge_spot_market_allowed, load_challenge_mode_policy, normalize_spot_pair,
)
from .challenge_risk import (
    ChallengeRiskLimits, RiskGateDecision, RiskObservation, RiskProposal,
    evaluate_challenge_risk, load_challenge_risk_limits,
)
from .challenge_execution import DispatchResult, ExecutionMode, dispatch_order_intent
from .challenge_settlement import (
    SettlementReadiness, SettlementSnapshot, validate_settlement_readiness,
)
from .decision_log import (
    DecisionAuditLog, DecisionEvent, DecisionLogError, EventOrigin,
    StructuredAIOutput,
)
from .risk import (
    AllCapitalError, InsufficientFundsError, RiskViolation,
    validate_available_balance, validate_capital_evidence,
    validate_not_all_capital, validate_sufficient_funds,
    validate_target_exposure,
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
    "ChallengeModePolicy",
    "ChallengePolicyError",
    "build_disabled_pair_registry",
    "DisabledPairRegistry",
    "EligibilityDecision",
    "MarketRequest",
    "MarketSnapshot",
    "is_challenge_spot_market_allowed",
    "load_challenge_mode_policy",
    "normalize_spot_pair",
    "ChallengeRiskLimits",
    "RiskGateDecision",
    "RiskObservation",
    "RiskProposal",
    "evaluate_challenge_risk",
    "load_challenge_risk_limits",
    "DispatchResult",
    "ExecutionMode",
    "dispatch_order_intent",
    "SettlementReadiness",
    "SettlementSnapshot",
    "validate_settlement_readiness",
    "DecisionAuditLog",
    "DecisionEvent",
    "DecisionLogError",
    "EventOrigin",
    "StructuredAIOutput",
    "load_candles",
    "run_replay",
    # Risk primitives
    "AllCapitalError",
    "InsufficientFundsError",
    "RiskViolation",
    "validate_available_balance",
    "validate_capital_evidence",
    "validate_not_all_capital",
    "validate_sufficient_funds",
    "validate_target_exposure",
]
