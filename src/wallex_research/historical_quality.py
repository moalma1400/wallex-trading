"""Explicit-policy audits and reproducible JSON/CSV/Markdown reports."""
from __future__ import annotations

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from typing import Any, Mapping, Sequence

from .data_quality import audit_candles
from .dataset_store import DatasetStore
from .historical import (
    CandleRecord,
    FairPriceSnapshotRecord,
    HistoricalDataError,
    MarketMetadataRecord,
    MarketRecord,
    OrderBookSideSnapshotRecord,
    OrderBookSnapshotRecord,
    PublicTradeRecord,
    canonical_json_bytes,
    logical_dedupe_key,
    record_to_dict,
    time_text,
    utc_time,
)


@dataclass(frozen=True, slots=True)
class AuditIssue:
    code: str
    severity: str
    message: str
    record_index: int | None = None
    logical_key: str | None = None


@dataclass(frozen=True, slots=True)
class AuditPolicy:
    expected_interval_seconds: int | None = None
    expected_start_utc: datetime | None = None
    expected_end_utc: datetime | None = None
    as_of_utc: datetime | None = None
    max_age_seconds: int | None = None
    known_symbols: tuple[str, ...] | None = None
    max_decimal_places: Mapping[str, int] | None = None

    def __post_init__(self) -> None:
        if self.expected_interval_seconds is not None and (isinstance(self.expected_interval_seconds, bool) or not isinstance(self.expected_interval_seconds, int) or self.expected_interval_seconds <= 0):
            raise HistoricalDataError("expected_interval_seconds must be a positive integer")
        if self.expected_start_utc is not None:
            object.__setattr__(self, "expected_start_utc", utc_time(self.expected_start_utc, "expected_start_utc"))
        if self.expected_end_utc is not None:
            object.__setattr__(self, "expected_end_utc", utc_time(self.expected_end_utc, "expected_end_utc"))
        if (self.expected_start_utc is None) != (self.expected_end_utc is None):
            raise HistoricalDataError("expected_start_utc and expected_end_utc must be supplied together")
        if self.expected_start_utc is not None and self.expected_end_utc <= self.expected_start_utc:
            raise HistoricalDataError("expected end must be later than expected start")
        if self.as_of_utc is not None:
            object.__setattr__(self, "as_of_utc", utc_time(self.as_of_utc, "as_of_utc"))
        if self.max_age_seconds is not None and (isinstance(self.max_age_seconds, bool) or not isinstance(self.max_age_seconds, int) or self.max_age_seconds < 0):
            raise HistoricalDataError("max_age_seconds must be a nonnegative integer")
        if (self.as_of_utc is None) != (self.max_age_seconds is None):
            raise HistoricalDataError("as_of_utc and max_age_seconds must be supplied together")
        if self.known_symbols is not None:
            symbols = tuple(sorted({symbol.strip() for symbol in self.known_symbols if isinstance(symbol, str) and symbol.strip()}))
            if len(symbols) != len(self.known_symbols):
                raise HistoricalDataError("known_symbols must contain only non-empty strings")
            object.__setattr__(self, "known_symbols", symbols)
        if self.max_decimal_places is not None:
            scales: dict[str, int] = {}
            for field, places in self.max_decimal_places.items():
                if not isinstance(field, str) or not field or isinstance(places, bool) or not isinstance(places, int) or places < 0:
                    raise HistoricalDataError("max_decimal_places must map field names to nonnegative integers")
                scales[field] = places
            object.__setattr__(self, "max_decimal_places", scales)

    @property
    def complete_for_replay(self) -> bool:
        return (
            self.expected_interval_seconds is not None
            and self.expected_start_utc is not None
            and self.expected_end_utc is not None
            and self.as_of_utc is not None
            and self.max_age_seconds is not None
            and self.known_symbols is not None
            and self.max_decimal_places is not None
            and "price" in self.max_decimal_places
            and "quantity" in self.max_decimal_places
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "expected_interval_seconds": self.expected_interval_seconds,
            "expected_start_utc": time_text(self.expected_start_utc) if self.expected_start_utc else None,
            "expected_end_utc": time_text(self.expected_end_utc) if self.expected_end_utc else None,
            "as_of_utc": time_text(self.as_of_utc) if self.as_of_utc else None,
            "max_age_seconds": self.max_age_seconds,
            "known_symbols": list(self.known_symbols) if self.known_symbols is not None else None,
            "max_decimal_places": dict(sorted(self.max_decimal_places.items())) if self.max_decimal_places is not None else None,
        }


@dataclass(frozen=True, slots=True)
class AuditReport:
    report_id: str
    dataset_id: str
    record_type: str
    schema_version: str
    code_version: str
    source_id: str
    source_url: str
    retrieval_method: str
    retrieved_at_utc: str
    ingested_at_utc: str
    captured_at_utc: str | None
    raw_sha256: str
    normalized_sha256: str
    record_count: int
    symbols: tuple[str, ...]
    interval_seconds: int | None
    event_range_start_utc: str | None
    event_range_end_utc: str | None
    policy: Mapping[str, Any]
    issues: tuple[AuditIssue, ...]
    replay_eligible: bool

    @property
    def has_errors(self) -> bool:
        return any(issue.severity == "error" for issue in self.issues)

    def as_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "dataset_id": self.dataset_id,
            "record_type": self.record_type,
            "schema_version": self.schema_version,
            "code_version": self.code_version,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "retrieval_method": self.retrieval_method,
            "retrieved_at_utc": self.retrieved_at_utc,
            "ingested_at_utc": self.ingested_at_utc,
            "captured_at_utc": self.captured_at_utc,
            "raw_sha256": self.raw_sha256,
            "normalized_sha256": self.normalized_sha256,
            "record_count": self.record_count,
            "symbols": list(self.symbols),
            "interval_seconds": self.interval_seconds,
            "event_range_start_utc": self.event_range_start_utc,
            "event_range_end_utc": self.event_range_end_utc,
            "policy": dict(self.policy),
            "issues": [
                {"code": issue.code, "severity": issue.severity, "message": issue.message, "record_index": issue.record_index, "logical_key": issue.logical_key}
                for issue in self.issues
            ],
            "replay_eligible": self.replay_eligible,
        }


def audit_dataset(store: DatasetStore, dataset_id: str, policy: AuditPolicy) -> AuditReport:
    manifest = store.read_manifest(dataset_id)
    issues: list[AuditIssue] = []
    try:
        records = store.read_records(dataset_id)
    except HistoricalDataError as exc:
        records = ()
        issues.append(AuditIssue("NORMALIZED_LOAD_FAILED", "error", f"Normalized dataset could not be trusted: {exc}"))

    if not records:
        issues.append(AuditIssue("EMPTY_DATASET", "error", "Dataset contains no records."))

    for code in store.verify_raw_and_normalized(dataset_id):
        issues.append(AuditIssue(code, "error", "Raw source and normalized representation failed integrity/reparse verification."))
    for warning in manifest.get("warnings", []):
        issues.append(AuditIssue("SOURCE_TIMESTAMP_MISSING", "warning", str(warning)))

    symbols = tuple(sorted({symbol for record in records for symbol in _record_symbols(record)}))
    if manifest["record_type"] != "candles":
        previous_event: datetime | None = None
        for index, record in enumerate(records):
            event = _event_time(record)
            if event is not None and previous_event is not None and event < previous_event:
                issues.append(AuditIssue("TIMESTAMP_OUT_OF_ORDER", "error", "Source event timestamps decrease; source order is preserved.", index, logical_dedupe_key(record)))
            if event is not None:
                previous_event = event
    if policy.known_symbols is None:
        issues.append(AuditIssue("SYMBOL_REGISTRY_UNKNOWN", "warning", "No explicit known-symbol registry was supplied; symbol identity is unverified."))
    else:
        for index, record in enumerate(records):
            for symbol in _record_symbols(record):
                if symbol not in policy.known_symbols:
                    issues.append(AuditIssue("UNKNOWN_SYMBOL", "error", f"Symbol {symbol!r} is absent from the caller-supplied known-symbol set.", index, logical_dedupe_key(record)))

    duplicate_groups: dict[str, list[int]] = {}
    for index, record in enumerate(records):
        duplicate_groups.setdefault(logical_dedupe_key(record), []).append(index)
    for key, indices in duplicate_groups.items():
        if len(indices) > 1:
            severity = "warning" if isinstance(records[indices[0]], PublicTradeRecord) else "error"
            code = "POSSIBLE_DUPLICATE_TRADE" if isinstance(records[indices[0]], PublicTradeRecord) else "DUPLICATE_LOGICAL_KEY"
            issues.append(AuditIssue(code, severity, f"Logical key occurs at record indices {indices}; source rows are retained.", indices[1], key))
            if isinstance(records[indices[0]], CandleRecord):
                first_payload = _business_payload(records[indices[0]])
                if any(_business_payload(records[index]) != first_payload for index in indices[1:]):
                    issues.append(AuditIssue("CONFLICTING_CANDLE_KEY", "error", "Same candle key has differing normalized values; no version was selected.", indices[1], key))
            if isinstance(records[indices[0]], MarketMetadataRecord):
                first_payload = _business_payload(records[indices[0]])
                if any(_business_payload(records[index]) != first_payload for index in indices[1:]):
                    issues.append(AuditIssue("CONFLICTING_MARKET_METADATA", "error", "Same symbol has conflicting metadata in one dataset; no update was selected.", indices[1], key))

    candles = [record.to_replay_candle() for record in records if isinstance(record, CandleRecord)]
    if manifest["record_type"] == "candles":
        if any(not isinstance(record, CandleRecord) for record in records):
            issues.append(AuditIssue("RECORD_TYPE_CONFLICT", "error", "Candle dataset contains non-candle normalized records."))
        for index, record in enumerate(records):
            if isinstance(record, CandleRecord) and record.interval_seconds != policy.expected_interval_seconds:
                if policy.expected_interval_seconds is None:
                    continue
                issues.append(AuditIssue("INCONSISTENT_INTERVAL", "error", f"Record interval {record.interval_seconds}s differs from explicit policy {policy.expected_interval_seconds}s.", index, logical_dedupe_key(record)))
        qreport = audit_candles(candles, expected_interval=timedelta(seconds=policy.expected_interval_seconds) if policy.expected_interval_seconds is not None else None)
        for issue in qreport.issues:
            severity = "error" if issue.severity == "error" else "warning"
            issues.append(AuditIssue(issue.code, severity, issue.message, issue.row - 1 if issue.row else None))
        if policy.expected_interval_seconds is None:
            issues.append(AuditIssue("INTERVAL_UNKNOWN", "warning", "Expected interval is not supplied; cadence and internal completeness are unknown."))
        if policy.expected_start_utc is None or policy.expected_end_utc is None:
            issues.append(AuditIssue("COMPLETENESS_UNKNOWN", "warning", "Expected start/end boundaries are not supplied; leading/trailing omissions cannot be assessed."))
        elif candles:
            if candles[0].timestamp != policy.expected_start_utc:
                issues.append(AuditIssue("INCOMPLETE_START", "error", "First candle does not match caller-supplied expected start."))
            if candles[-1].timestamp != policy.expected_end_utc:
                issues.append(AuditIssue("INCOMPLETE_END", "error", "Last candle does not match caller-supplied expected end."))
        if candles and policy.as_of_utc is not None and policy.max_age_seconds is not None:
            age = (policy.as_of_utc - candles[-1].timestamp).total_seconds()
            if age < 0:
                issues.append(AuditIssue("FUTURE_DATA", "error", "Latest market event is later than the explicit as-of time."))
            elif age > policy.max_age_seconds:
                issues.append(AuditIssue("STALE_DATA", "error", f"Latest market event is {age:g}s old, exceeding explicit max age {policy.max_age_seconds}s."))
        else:
            issues.append(AuditIssue("FRESHNESS_UNKNOWN", "warning", "An explicit as-of timestamp and maximum age are required to assess staleness."))
    else:
        if policy.expected_interval_seconds is not None:
            issues.append(AuditIssue("INTERVAL_NOT_APPLICABLE", "info", "Interval policy is only applied to candle datasets."))
        event_times_for_type = [when for record in records if (when := _event_time(record)) is not None]
        if policy.expected_start_utc is None or policy.expected_end_utc is None:
            issues.append(AuditIssue("RANGE_POLICY_UNKNOWN", "warning", "No expected event-time range was supplied."))
        elif not event_times_for_type:
            issues.append(AuditIssue("EVENT_RANGE_UNAVAILABLE", "warning", "This record type has no documented event timestamp; capture time is not substituted."))
        else:
            if min(event_times_for_type) != policy.expected_start_utc:
                issues.append(AuditIssue("INCOMPLETE_START", "error", "Earliest source event does not match caller-supplied expected start."))
            if max(event_times_for_type) != policy.expected_end_utc:
                issues.append(AuditIssue("INCOMPLETE_END", "error", "Latest source event does not match caller-supplied expected end."))
        if policy.as_of_utc is None or policy.max_age_seconds is None:
            issues.append(AuditIssue("FRESHNESS_UNKNOWN", "warning", "An explicit as-of timestamp and maximum age are required to assess staleness."))
        elif not event_times_for_type:
            issues.append(AuditIssue("FRESHNESS_UNAVAILABLE", "warning", "No documented event timestamp is available for stale-data assessment."))
        else:
            age = (policy.as_of_utc - max(event_times_for_type)).total_seconds()
            if age < 0:
                issues.append(AuditIssue("FUTURE_DATA", "error", "Latest market event is later than the explicit as-of time."))
            elif age > policy.max_age_seconds:
                issues.append(AuditIssue("STALE_DATA", "error", f"Latest market event is {age:g}s old, exceeding explicit max age {policy.max_age_seconds}s."))

    _audit_precision(records, policy, issues)
    if policy.max_decimal_places is None:
        issues.append(AuditIssue("PRECISION_POLICY_UNKNOWN", "warning", "No explicit maximum decimal-place policy was supplied."))
    elif "price" not in policy.max_decimal_places or "quantity" not in policy.max_decimal_places:
        issues.append(AuditIssue("PRECISION_POLICY_INCOMPLETE", "warning", "Explicit precision limits for both price and quantity are required for replay readiness."))

    if not records:
        event_times: list[datetime] = []
    else:
        event_times = [when for record in records if (when := _event_time(record)) is not None]
    start = time_text(min(event_times)) if event_times else None
    end = time_text(max(event_times)) if event_times else None

    non_info = [issue for issue in issues if issue.severity != "info"]
    eligible = (
        manifest["record_type"] == "candles"
        and policy.complete_for_replay
        and not any(issue.severity == "error" for issue in issues)
        and not any(issue.code in {"SYMBOL_REGISTRY_UNKNOWN", "COMPLETENESS_UNKNOWN", "FRESHNESS_UNKNOWN", "PRECISION_POLICY_UNKNOWN", "PRECISION_POLICY_INCOMPLETE", "INTERVAL_UNKNOWN"} for issue in non_info)
    )
    summary = {
        "dataset_id": dataset_id,
        "raw_sha256": manifest["raw_sha256"],
        "normalized_sha256": manifest["normalized_sha256"],
        "policy": policy.as_dict(),
        "retrieval_method": manifest["retrieval_method"],
        "retrieved_at_utc": manifest["retrieved_at_utc"],
        "ingested_at_utc": manifest["ingested_at_utc"],
        "captured_at_utc": manifest.get("captured_at_utc"),
        "issues": [{"code": issue.code, "severity": issue.severity, "message": issue.message, "record_index": issue.record_index, "logical_key": issue.logical_key} for issue in issues],
        "replay_eligible": eligible,
    }
    report_id = hashlib.sha256(canonical_json_bytes(summary)).hexdigest()
    return AuditReport(
        report_id, dataset_id, manifest["record_type"], manifest["schema_version"], manifest["code_version"],
        manifest["source_id"], manifest["source_url"], manifest["retrieval_method"], manifest["retrieved_at_utc"], manifest["ingested_at_utc"], manifest.get("captured_at_utc"), manifest["raw_sha256"], manifest["normalized_sha256"],
        len(records), symbols, manifest.get("interval_seconds"), start, end, policy.as_dict(), tuple(issues), eligible,
    )


def _record_symbols(record: MarketRecord) -> tuple[str, ...]:
    if isinstance(record, FairPriceSnapshotRecord):
        return tuple(record.prices.keys())
    if hasattr(record, "symbol"):
        return (record.symbol,)
    return ()


def _event_time(record: MarketRecord) -> datetime | None:
    value = getattr(record, "timestamp_utc", None)
    if value is not None:
        return value
    return getattr(record, "source_timestamp_utc", None)


def _business_payload(record: MarketRecord) -> dict[str, Any]:
    value = record_to_dict(record).copy()
    value.pop("provenance", None)
    return value


def _decimal_places(value: Decimal) -> int:
    return max(0, -value.as_tuple().exponent)


def _audit_precision(records: Sequence[MarketRecord], policy: AuditPolicy, issues: list[AuditIssue]) -> None:
    scales: dict[str, set[int]] = {"price": set(), "quantity": set()}
    for index, record in enumerate(records):
        fields: list[tuple[str, Decimal]] = []
        if isinstance(record, CandleRecord):
            fields.extend(("price", getattr(record, field)) for field in ("open", "high", "low", "close"))
            fields.append(("quantity", record.volume))
        elif isinstance(record, PublicTradeRecord):
            fields.extend((("price", record.price), ("quantity", record.quantity)))
        elif isinstance(record, FairPriceSnapshotRecord):
            fields.extend(("price", value) for value in record.prices.values())
        elif isinstance(record, OrderBookSnapshotRecord):
            fields.extend((kind, value) for side in (record.bids, record.asks) for level in side for kind, value in (("price", level.price), ("quantity", level.quantity)))
        elif isinstance(record, OrderBookSideSnapshotRecord):
            fields.extend((kind, value) for level in record.levels for kind, value in (("price", level.price), ("quantity", level.quantity)))
        for kind, value in fields:
            places = _decimal_places(value)
            scales[kind].add(places)
            maximum = (policy.max_decimal_places or {}).get(kind)
            if maximum is not None and places > maximum:
                issues.append(AuditIssue("PRECISION_EXCEEDS_POLICY", "error", f"{kind} value uses {places} decimal places; explicit maximum is {maximum}.", index, logical_dedupe_key(record)))
    for kind, observed in scales.items():
        if len(observed) > 1:
            issues.append(AuditIssue("PRECISION_SCALE_VARIATION", "warning", f"Observed {kind} decimal scales vary: {sorted(observed)}; variation is not itself proof of invalidity."))


def write_audit_reports(report: AuditReport, output_dir: str | Path) -> tuple[Path, Path, Path]:
    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    json_path = directory / f"{report.report_id}.json"
    csv_path = directory / f"{report.report_id}.issues.csv"
    markdown_path = directory / f"{report.report_id}.md"
    json_bytes = canonical_json_bytes(report.as_dict()) + b"\n"

    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=("code", "severity", "message", "record_index", "logical_key"), lineterminator="\n")
    writer.writeheader()
    for issue in report.issues:
        writer.writerow({"code": issue.code, "severity": issue.severity, "message": issue.message, "record_index": issue.record_index if issue.record_index is not None else "", "logical_key": issue.logical_key or ""})
    csv_bytes = buffer.getvalue().encode("utf-8")

    lines = [
        f"# Dataset audit `{report.report_id}`", "",
        f"- Dataset ID: `{report.dataset_id}`", f"- Type/schema: `{report.record_type}` / `{report.schema_version}`",
        f"- Source: `{report.source_id}` — {report.source_url}", f"- Retrieval method: `{report.retrieval_method}`", f"- Retrieved at: `{report.retrieved_at_utc}`", f"- Ingested at: `{report.ingested_at_utc}`", f"- Captured at: `{report.captured_at_utc or 'not supplied'}`", f"- Records: {report.record_count}",
        f"- Symbols: {', '.join(f'`{symbol}`' for symbol in report.symbols) or 'unknown'}",
        f"- Interval seconds: `{report.interval_seconds}`", f"- Event range: `{report.event_range_start_utc}` → `{report.event_range_end_utc}`",
        f"- Raw SHA-256: `{report.raw_sha256}`", f"- Normalized SHA-256: `{report.normalized_sha256}`",
        f"- Replay eligible: **{'yes' if report.replay_eligible else 'no'}**", "", "## Audit policy", "",
        "```json", canonical_json_bytes(dict(report.policy)).decode("utf-8"), "```", "", "## Findings", "",
    ]
    if report.issues:
        lines.extend(f"- **{issue.severity.upper()} `{issue.code}`**" + (f" (row/index {issue.record_index})" if issue.record_index is not None else "") + f": {issue.message}" for issue in report.issues)
    else:
        lines.append("No structural findings under the explicit policy. This does not prove source authenticity or exchange compatibility.")
    lines.extend(("", "Machine-readable files: JSON summary and CSV issue list.", ""))
    markdown_bytes = "\n".join(lines).encode("utf-8")
    _write_reproducible_output(json_path, json_bytes)
    _write_reproducible_output(csv_path, csv_bytes)
    _write_reproducible_output(markdown_path, markdown_bytes)
    return json_path, csv_path, markdown_path


def export_replay_csv(store: DatasetStore, report: AuditReport, output_path: str | Path) -> tuple[Path, Path]:
    if not report.replay_eligible:
        raise HistoricalDataError("replay export blocked: dataset audit is not replay-eligible")
    if report.record_type != "candles":
        raise HistoricalDataError("only candle datasets can be exported to Feature 002 replay CSV")
    records = store.read_records(report.dataset_id)
    if not records or not all(isinstance(record, CandleRecord) for record in records):
        raise HistoricalDataError("candle dataset contains no replayable candles")
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(("symbol", "timestamp", "open", "high", "low", "close", "volume"))
    for record in records:
        assert isinstance(record, CandleRecord)
        writer.writerow((record.symbol, time_text(record.timestamp_utc), str(record.open), str(record.high), str(record.low), str(record.close), str(record.volume)))
    content = buffer.getvalue().encode("utf-8")
    sidecar = output.with_suffix(output.suffix + ".manifest.json")
    sidecar_data = {
        "export_schema": "wallex-replay-csv-1",
        "dataset_id": report.dataset_id,
        "audit_report_id": report.report_id,
        "audit_policy": dict(report.policy),
        "csv_sha256": hashlib.sha256(content).hexdigest(),
        "record_count": len(records),
        "feature_002_csv_columns": ["symbol", "timestamp", "open", "high", "low", "close", "volume"],
    }
    sidecar_bytes = canonical_json_bytes(sidecar_data) + b"\n"
    _write_reproducible_output(output, content)
    _write_reproducible_output(sidecar, sidecar_bytes)
    return output, sidecar


def _write_reproducible_output(path: Path, content: bytes) -> None:
    """Create an output once; permit exact idempotent reruns, never clobber differences."""
    if path.is_symlink():
        raise HistoricalDataError(f"refusing to write through symlink: {path}")
    if path.exists():
        if not path.is_file() or path.read_bytes() != content:
            raise HistoricalDataError(f"refusing to overwrite conflicting output: {path}")
        return
    try:
        with path.open("xb") as stream:
            stream.write(content)
    except FileExistsError:
        if not path.is_file() or path.read_bytes() != content:
            raise HistoricalDataError(f"refusing to overwrite conflicting output: {path}")
