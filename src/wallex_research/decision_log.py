"""Versioned, replayable decision/event logs for offline and shadow research only."""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any, Mapping, Sequence

from .challenge import ChallengePolicyError, _decimal
from .historical import canonical_json_bytes, utc_time


class DecisionLogError(ValueError):
    """An event is incomplete, unsafe to persist, or not reproducible."""


class EventOrigin(StrEnum):
    BACKTEST = "backtest"
    SHADOW = "shadow"
    DRY_RUN = "dry_run"
    EXCHANGE = "exchange"  # Reserved schema value; rejected by this feature.


EVENT_TYPES = {
    "market_snapshot", "feature_snapshot", "ai_analysis", "signal", "risk_check",
    "order_intent", "order_submission_result", "fill", "partial_fill", "rejection",
    "fee", "balance", "realized_pnl", "unrealized_pnl_estimate", "end_state", "run_summary",
}
REQUIRED_EVENT_PAYLOAD_FIELDS = {
    "market_snapshot": {"snapshot_ref", "pair", "observed_at_utc", "source_id", "source_sha256", "evidence_status"},
    "feature_snapshot": {"snapshot_ref", "feature_refs", "source_data_refs", "dataset_manifest_sha256"},
    "ai_analysis": {"action", "confidence", "horizon", "supporting_feature_refs", "counter_evidence", "rationale"},
    "signal": {"signal_id", "action", "evidence_refs", "strategy_version"},
    "risk_check": {"proposal_id", "allowed", "reason_codes", "risk_config_sha256"},
    "order_intent": {"intent_id", "idempotency_key", "pair", "side", "quantity", "notional_tmn", "risk_event_id"},
    "order_submission_result": {"intent_id", "status", "exchange_order_id"},
    "fill": {"intent_id", "fill_id", "quantity", "price", "fee", "fee_asset"},
    "partial_fill": {"intent_id", "fill_id", "quantity", "remaining_quantity", "price", "fee", "fee_asset"},
    "rejection": {"intent_id", "reason_code", "risk_event_id"},
    "fee": {"intent_id", "amount", "asset", "source_ref"},
    "balance": {"asset", "amount", "observed_at_utc", "source_ref"},
    "realized_pnl": {"trade_ref", "pnl_tmn", "fees_tmn", "balance_event_ref"},
    "unrealized_pnl_estimate": {"asset", "amount", "mark_price", "mark_timestamp_utc", "mark_source_ref"},
    "end_state": {"snapshot_ref", "official_cutoff_utc", "settlement_ready", "reason_codes"},
    "run_summary": {"run_status", "started_at_utc", "ended_at_utc", "result_refs", "config_sha256", "data_manifest_sha256", "dataset_source_ids", "range_start_utc", "range_end_utc", "dataset_schema_version"},
}
FORBIDDEN_KEY_PARTS = (
    "api_key", "apikey", "authorization", "password", "secret", "cookie", "token",
    "phone", "national_id", "date_of_birth", "dob", "email", "personal_id",
)
SECRET_VALUE_PATTERNS = (
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    re.compile(r"-----BEGIN (?:RSA|OPENSSH|EC) PRIVATE KEY-----"),
)


def _check_safe_payload(value: Any, path: str = "payload") -> None:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if not isinstance(key, str):
                raise DecisionLogError(f"{path} object keys must be strings")
            normalized = re.sub(r"[^a-z0-9]+", "_", key.lower()).strip("_")
            if any(part in normalized for part in FORBIDDEN_KEY_PARTS):
                raise DecisionLogError(f"{path}.{key} is prohibited private/credential data")
            _check_safe_payload(item, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check_safe_payload(item, f"{path}[{index}]")
    elif isinstance(value, float):
        raise DecisionLogError(f"{path} contains a binary float; persist exact decimal text instead")
    elif isinstance(value, Decimal):
        if not value.is_finite():
            raise DecisionLogError(f"{path} must be finite")
    elif isinstance(value, str):
        if any(pattern.search(value) for pattern in SECRET_VALUE_PATTERNS):
            raise DecisionLogError(f"{path} resembles a credential; refusing to persist it")


def _validate_event_payload(event_type: str, payload: Mapping[str, Any]) -> None:
    text_fields = {
        "snapshot_ref", "pair", "source_id", "source_sha256", "evidence_status",
        "dataset_manifest_sha256", "signal_id", "strategy_version", "proposal_id",
        "risk_config_sha256", "intent_id", "idempotency_key", "side", "exchange_order_id",
        "fill_id", "reason_code", "asset", "source_ref", "trade_ref", "balance_event_ref",
        "mark_source_ref", "run_status", "config_sha256", "data_manifest_sha256",
        "dataset_schema_version",
    }
    for field in text_fields.intersection(payload):
        value = payload[field]
        if value is not None and (not isinstance(value, str) or not value.strip()):
            raise DecisionLogError(f"{event_type}.{field} must be non-empty text")
    for field in {"source_sha256", "dataset_manifest_sha256", "risk_config_sha256", "config_sha256", "data_manifest_sha256"}.intersection(payload):
        if not isinstance(payload[field], str) or not re.fullmatch(r"[0-9a-f]{64}", payload[field]):
            raise DecisionLogError(f"{event_type}.{field} must be a lowercase SHA-256 fingerprint")
    for field in {"allowed", "settlement_ready"}.intersection(payload):
        if not isinstance(payload[field], bool):
            raise DecisionLogError(f"{event_type}.{field} must be boolean")
    for field in {"reason_codes", "feature_refs", "source_data_refs", "evidence_refs", "supporting_feature_refs", "counter_evidence", "result_refs", "dataset_source_ids"}.intersection(payload):
        value = payload[field]
        if not isinstance(value, (list, tuple)) or not all(isinstance(item, str) and item.strip() for item in value):
            raise DecisionLogError(f"{event_type}.{field} must be a sequence of non-empty text")
    if "action" in payload and payload["action"] not in {"BUY", "SELL", "HOLD"}:
        raise DecisionLogError(f"{event_type}.action must be BUY, SELL, or HOLD")
    for field in {"confidence", "quantity", "notional_tmn", "price", "fee", "remaining_quantity", "amount", "pnl_tmn", "fees_tmn", "mark_price"}.intersection(payload):
        try:
            numeric = _decimal(payload[field], f"{event_type}.{field}", nonnegative=field != "pnl_tmn")
            if field in {"quantity", "notional_tmn", "price", "remaining_quantity", "mark_price"} and numeric <= 0:
                raise DecisionLogError(f"{event_type}.{field} must be positive")
            if field == "confidence" and numeric > 1:
                raise DecisionLogError(f"{event_type}.confidence must be in [0, 1]")
        except ChallengePolicyError as exc:
            raise DecisionLogError(str(exc)) from exc
    for field in {"observed_at_utc", "started_at_utc", "ended_at_utc", "range_start_utc", "range_end_utc", "mark_timestamp_utc", "official_cutoff_utc"}.intersection(payload):
        if payload[field] is None:
            continue
        try:
            utc_time(payload[field], f"{event_type}.{field}")
        except (ChallengePolicyError, TypeError, ValueError) as exc:
            raise DecisionLogError(f"{event_type}.{field} must be a timezone-aware timestamp") from exc
    if "pair" in payload:
        try:
            canonical_pair = normalize_spot_pair(payload["pair"])
        except ChallengePolicyError as exc:
            raise DecisionLogError(f"{event_type}.pair is malformed") from exc
        if canonical_pair != payload["pair"]:
            raise DecisionLogError(f"{event_type}.pair must use canonical uppercase BASE/QUOTE")
    if "side" in payload and payload["side"] not in {"BUY", "SELL"}:
        raise DecisionLogError(f"{event_type}.side must be BUY or SELL")


@dataclass(frozen=True, slots=True)
class StructuredAIOutput:
    action: str
    confidence: Decimal | str | int
    horizon: str
    supporting_feature_refs: tuple[str, ...]
    counter_evidence: tuple[str, ...]
    rationale: str
    fallback_reason: str | None = None

    def __post_init__(self) -> None:
        action = self.action.upper() if isinstance(self.action, str) else ""
        if action not in {"BUY", "SELL", "HOLD"}:
            raise DecisionLogError("AI action must be BUY, SELL, or HOLD")
        object.__setattr__(self, "action", action)
        confidence = _decimal(self.confidence, "AI confidence")
        if confidence > 1:
            raise DecisionLogError("AI confidence must be in [0, 1]")
        object.__setattr__(self, "confidence", confidence)
        for name in ("horizon", "rationale"):
            value = getattr(self, name)
            if not isinstance(value, str) or not value.strip():
                raise DecisionLogError(f"AI {name} must be non-empty")
        object.__setattr__(self, "supporting_feature_refs", tuple(self.supporting_feature_refs))
        object.__setattr__(self, "counter_evidence", tuple(self.counter_evidence))
        if not all(isinstance(item, str) and item.strip() for item in (*self.supporting_feature_refs, *self.counter_evidence)):
            raise DecisionLogError("AI feature references and counter-evidence must be non-empty text")
        _check_safe_payload({"rationale": self.rationale, "counter_evidence": self.counter_evidence})
        if self.fallback_reason is not None and not self.fallback_reason.strip():
            raise DecisionLogError("fallback_reason must be non-empty when present")

    def as_dict(self) -> dict[str, Any]:
        return {
            "schema_version": "1.0",
            "action": self.action,
            "confidence": str(self.confidence),
            "horizon": self.horizon,
            "supporting_feature_refs": list(self.supporting_feature_refs),
            "counter_evidence": list(self.counter_evidence),
            "rationale": self.rationale,
            "fallback_reason": self.fallback_reason,
        }

    @classmethod
    def from_mapping_or_hold(cls, value: Mapping[str, Any] | Any, *, failure_reason: str = "INVALID_OR_MISSING_MODEL_OUTPUT") -> "StructuredAIOutput":
        """Parse exact output schema; any invalid/missing output falls back to HOLD."""
        required = {"action", "confidence", "horizon", "supporting_feature_refs", "counter_evidence", "rationale"}
        if not isinstance(value, Mapping) or set(value) != required:
            return cls("HOLD", "0", "unspecified", ("no-valid-model-output",), ("model-output-unavailable",), "No action: structured model output was missing or invalid.", failure_reason)
        try:
            return cls(
                value["action"], value["confidence"], value["horizon"],
                tuple(value["supporting_feature_refs"]), tuple(value["counter_evidence"]), value["rationale"],
            )
        except (DecisionLogError, ChallengePolicyError, TypeError, ValueError):
            return cls("HOLD", "0", "unspecified", ("no-valid-model-output",), ("schema-validation-failed",), "No action: model output failed schema validation.", failure_reason)


@dataclass(frozen=True, slots=True)
class DecisionEvent:
    run_id: str
    sequence: int
    occurred_at_utc: datetime
    event_type: str
    origin: EventOrigin | str
    code_commit: str
    config_sha256: str
    strategy_version: str
    payload: Mapping[str, Any]
    feature_snapshot_refs: tuple[str, ...] = ()
    model_provider: str | None = None
    model_name: str | None = None
    model_version: str | None = None
    prompt_template_version: str | None = None
    event_schema_version: str = "1.0"
    event_id: str = ""

    def __post_init__(self) -> None:
        if not isinstance(self.run_id, str) or not self.run_id.strip():
            raise DecisionLogError("run_id must be non-empty")
        if isinstance(self.sequence, bool) or not isinstance(self.sequence, int) or self.sequence < 0:
            raise DecisionLogError("sequence must be a nonnegative integer")
        object.__setattr__(self, "occurred_at_utc", utc_time(self.occurred_at_utc, "occurred_at_utc"))
        if self.event_type not in EVENT_TYPES:
            raise DecisionLogError(f"unsupported decision event type: {self.event_type}")
        try:
            origin = self.origin if isinstance(self.origin, EventOrigin) else EventOrigin(self.origin)
        except ValueError as exc:
            raise DecisionLogError("unsupported event origin") from exc
        if origin is EventOrigin.EXCHANGE:
            raise DecisionLogError("exchange-origin events are reserved for a separately authorized future feature")
        object.__setattr__(self, "origin", origin)
        if self.event_schema_version != "1.0":
            raise DecisionLogError("unsupported decision event schema version")
        if not isinstance(self.code_commit, str) or not re.fullmatch(r"[0-9a-f]{7,40}", self.code_commit):
            raise DecisionLogError("code_commit must be a hexadecimal Git commit identifier")
        if not re.fullmatch(r"[0-9a-f]{64}", self.config_sha256):
            raise DecisionLogError("config_sha256 must be a lowercase SHA-256 fingerprint")
        if not isinstance(self.strategy_version, str) or not self.strategy_version.strip():
            raise DecisionLogError("strategy_version must be explicit")
        if not isinstance(self.payload, Mapping):
            raise DecisionLogError("payload must be a structured object")
        required_payload = REQUIRED_EVENT_PAYLOAD_FIELDS[self.event_type]
        missing_payload = required_payload - self.payload.keys()
        if missing_payload:
            raise DecisionLogError(f"{self.event_type} payload missing fields: {', '.join(sorted(missing_payload))}")
        _check_safe_payload(self.payload)
        _validate_event_payload(self.event_type, self.payload)
        refs = tuple(self.feature_snapshot_refs)
        if not all(isinstance(ref, str) and ref.strip() for ref in refs):
            raise DecisionLogError("feature_snapshot_refs must contain non-empty IDs/paths")
        object.__setattr__(self, "feature_snapshot_refs", refs)
        if self.event_type == "ai_analysis" and not all((self.model_provider, self.model_name, self.model_version, self.prompt_template_version)):
            raise DecisionLogError("AI analysis events require provider/model/prompt versions")
        calculated = hashlib.sha256(canonical_json_bytes(self.identity_fields())).hexdigest()
        if self.event_id and self.event_id != calculated:
            raise DecisionLogError("event_id does not match deterministic event contents")
        object.__setattr__(self, "event_id", calculated)

    def identity_fields(self) -> dict[str, Any]:
        return {
            "event_schema_version": self.event_schema_version,
            "run_id": self.run_id,
            "sequence": self.sequence,
            "occurred_at_utc": self.occurred_at_utc,
            "event_type": self.event_type,
            "origin": self.origin.value if isinstance(self.origin, EventOrigin) else str(self.origin),
            "code_commit": self.code_commit,
            "config_sha256": self.config_sha256,
            "strategy_version": self.strategy_version,
            "feature_snapshot_refs": self.feature_snapshot_refs,
            "model_provider": self.model_provider,
            "model_name": self.model_name,
            "model_version": self.model_version,
            "prompt_template_version": self.prompt_template_version,
            "payload": dict(self.payload),
        }

    def as_dict(self) -> dict[str, Any]:
        return {"event_id": self.event_id, **self.identity_fields()}

    def to_jsonl(self) -> bytes:
        return canonical_json_bytes(self.as_dict()) + b"\n"


class DecisionAuditLog:
    """Local append-only JSONL writer with stable event IDs and sequence checks."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        if self.path.is_symlink():
            raise DecisionLogError("refusing to follow a symlink for decision audit logs")
        self._event_ids: set[str] = set()
        self._last_sequence_by_run: dict[str, int] = {}
        if self.path.exists():
            self._load_existing()

    def _load_existing(self) -> None:
        try:
            lines = self.path.read_bytes().splitlines()
        except OSError as exc:
            raise DecisionLogError(f"cannot read decision audit log: {exc}") from exc
        for line_number, line in enumerate(lines, 1):
            try:
                item = json.loads(line)
                event = DecisionEvent(
                    run_id=item["run_id"], sequence=item["sequence"], occurred_at_utc=item["occurred_at_utc"],
                    event_type=item["event_type"], origin=item["origin"], code_commit=item["code_commit"],
                    config_sha256=item["config_sha256"], strategy_version=item["strategy_version"], payload=item["payload"],
                    feature_snapshot_refs=tuple(item["feature_snapshot_refs"]), model_provider=item.get("model_provider"),
                    model_name=item.get("model_name"), model_version=item.get("model_version"),
                    prompt_template_version=item.get("prompt_template_version"), event_schema_version=item["event_schema_version"],
                    event_id=item["event_id"],
                )
            except (KeyError, json.JSONDecodeError, TypeError, ValueError) as exc:
                raise DecisionLogError(f"invalid decision event at line {line_number}: {exc}") from exc
            self._track(event)

    def _track(self, event: DecisionEvent) -> None:
        if event.event_id in self._event_ids:
            raise DecisionLogError(f"duplicate event_id: {event.event_id}")
        last = self._last_sequence_by_run.get(event.run_id, -1)
        if event.sequence <= last:
            raise DecisionLogError(f"non-increasing event sequence for run {event.run_id}")
        self._event_ids.add(event.event_id)
        self._last_sequence_by_run[event.run_id] = event.sequence

    def append(self, event: DecisionEvent) -> str:
        if self.path.is_symlink():
            raise DecisionLogError("refusing to append through a symlink decision log")
        if not isinstance(event, DecisionEvent):
            raise DecisionLogError("append requires a validated DecisionEvent")
        if event.event_id in self._event_ids or event.sequence <= self._last_sequence_by_run.get(event.run_id, -1):
            raise DecisionLogError("duplicate event or non-increasing run sequence")
        try:
            with self.path.open("ab") as stream:
                stream.write(event.to_jsonl())
                stream.flush()
        except OSError as exc:
            raise DecisionLogError(f"cannot append decision event: {exc}") from exc
        self._track(event)
        return event.event_id

    @property
    def event_count(self) -> int:
        return len(self._event_ids)
