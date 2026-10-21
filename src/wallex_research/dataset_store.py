"""Content-addressed, offline dataset storage with immutable raw source bytes."""
from __future__ import annotations

import hashlib
import json
import os
import re
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Sequence

from .historical import (
    SCHEMA_VERSION,
    CandleRecord,
    DatasetContext,
    HistoricalDataError,
    MarketRecord,
    canonical_json_bytes,
    parse_local_bytes,
    parse_records_jsonl,
    records_jsonl,
    time_text,
)


@dataclass(frozen=True, slots=True)
class ImportResult:
    dataset_id: str
    manifest_path: Path
    created: bool
    record_count: int
    raw_sha256: str
    normalized_sha256: str


class DatasetStore:
    """A small local store; it has no remote adapter, database, or implicit cleanup."""

    _DATASET_ID = re.compile(r"^[0-9a-f]{64}$")

    @classmethod
    def _check_dataset_id(cls, dataset_id: str) -> None:
        if not isinstance(dataset_id, str) or not cls._DATASET_ID.fullmatch(dataset_id):
            raise HistoricalDataError("dataset_id must be a 64-character lowercase SHA-256 fingerprint")

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def import_local(self, source_path: str | Path, context: DatasetContext) -> ImportResult:
        source = Path(source_path)
        try:
            raw = source.read_bytes()
        except OSError as exc:
            raise HistoricalDataError(f"cannot read local source file: {exc}") from exc
        raw_sha = hashlib.sha256(raw).hexdigest()
        identity = context.identity(raw_sha, source.suffix.lower())
        dataset_id = hashlib.sha256(canonical_json_bytes(identity)).hexdigest()
        raw_path = self.root / "raw" / "sha256" / raw_sha
        dataset_dir = self.root / "datasets" / dataset_id
        manifest_path = dataset_dir / "manifest.json"
        normalized_path = dataset_dir / "records.jsonl"

        self._write_immutable(raw_path, raw)
        if manifest_path.exists():
            manifest = self.read_manifest(dataset_id)
            if manifest.get("identity") != identity:
                raise HistoricalDataError("dataset ID collision or inconsistent import identity; existing data was not overwritten")
            self._verify_hash(normalized_path, manifest.get("normalized_sha256"), "normalized dataset")
            self._verify_hash(raw_path, manifest.get("raw_sha256"), "raw source")
            return ImportResult(dataset_id, manifest_path, False, int(manifest["record_count"]), raw_sha, str(manifest["normalized_sha256"]))

        records = parse_local_bytes(raw, source, context, raw_sha)
        normalized = records_jsonl(records)
        normalized_sha = hashlib.sha256(normalized).hexdigest()
        manifest = self._build_manifest(dataset_id, source, raw_path, context, records, raw_sha, normalized_sha)
        self._write_new(normalized_path, normalized)
        self._write_new(manifest_path, canonical_json_bytes(manifest) + b"\n")
        return ImportResult(dataset_id, manifest_path, True, len(records), raw_sha, normalized_sha)

    def read_manifest(self, dataset_id: str) -> dict[str, Any]:
        self._check_dataset_id(dataset_id)
        path = self.root / "datasets" / dataset_id / "manifest.json"
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HistoricalDataError(f"cannot read dataset manifest: {exc}") from exc
        if not isinstance(value, dict) or value.get("dataset_id") != dataset_id:
            raise HistoricalDataError("manifest is malformed or dataset ID does not match its path")
        if value.get("schema_version") != SCHEMA_VERSION:
            raise HistoricalDataError("unsupported dataset manifest schema version")
        identity = value.get("identity")
        if not isinstance(identity, dict) or hashlib.sha256(canonical_json_bytes(identity)).hexdigest() != dataset_id:
            raise HistoricalDataError("manifest identity fingerprint does not match its dataset ID")
        return value

    def read_records(self, dataset_id: str) -> tuple[MarketRecord, ...]:
        manifest = self.read_manifest(dataset_id)
        path = self.root / "datasets" / dataset_id / "records.jsonl"
        try:
            content = path.read_bytes()
        except OSError as exc:
            raise HistoricalDataError(f"cannot read normalized records: {exc}") from exc
        self._verify_hash(path, manifest.get("normalized_sha256"), "normalized dataset")
        records = parse_records_jsonl(content)
        if len(records) != manifest.get("record_count"):
            raise HistoricalDataError("normalized record count differs from manifest")
        return records

    def verify_raw_and_normalized(self, dataset_id: str) -> tuple[str, ...]:
        """Verify bytes and independently reparse raw input to detect representation conflicts."""
        manifest = self.read_manifest(dataset_id)
        raw_sha = manifest.get("raw_sha256")
        raw_relative = manifest.get("raw_relative_path")
        if not isinstance(raw_sha, str) or not re.fullmatch(r"[0-9a-f]{64}", raw_sha):
            return ("MANIFEST_RAW_PATH_INVALID",)
        expected_raw_relative = Path("raw") / "sha256" / raw_sha
        if not isinstance(raw_relative, str) or Path(raw_relative) != expected_raw_relative:
            return ("MANIFEST_RAW_PATH_INVALID",)
        normalized_relative = manifest.get("normalized_relative_path")
        expected_normalized_relative = Path("datasets") / dataset_id / "records.jsonl"
        if not isinstance(normalized_relative, str) or Path(normalized_relative) != expected_normalized_relative:
            return ("MANIFEST_NORMALIZED_PATH_INVALID",)
        raw_path = self.root / expected_raw_relative
        normalized_path = self.root / expected_normalized_relative
        issues: list[str] = []
        try:
            raw = raw_path.read_bytes()
        except OSError:
            return ("RAW_SOURCE_MISSING",)
        if hashlib.sha256(raw).hexdigest() != manifest.get("raw_sha256"):
            issues.append("RAW_SHA256_MISMATCH")
        try:
            normalized = normalized_path.read_bytes()
        except OSError:
            return tuple((*issues, "NORMALIZED_SOURCE_MISSING"))
        if hashlib.sha256(normalized).hexdigest() != manifest.get("normalized_sha256"):
            issues.append("NORMALIZED_SHA256_MISMATCH")
        try:
            ctx = DatasetContext(
                record_type=manifest["record_type"],
                source_id=manifest["source_id"],
                source_url=manifest["source_url"],
                retrieval_method=manifest["retrieval_method"],
                retrieved_at_utc=datetime.fromisoformat(manifest["retrieved_at_utc"].replace("Z", "+00:00")),
                ingested_at_utc=datetime.fromisoformat(manifest["ingested_at_utc"].replace("Z", "+00:00")),
                captured_at_utc=datetime.fromisoformat(manifest["captured_at_utc"].replace("Z", "+00:00")) if manifest.get("captured_at_utc") else None,
                symbol=manifest.get("symbol"),
                interval_seconds=manifest.get("interval_seconds"),
                code_version=manifest["code_version"],
            )
            replayed = parse_local_bytes(raw, Path(manifest["original_filename"]), ctx, manifest["raw_sha256"])
            if records_jsonl(replayed) != normalized:
                issues.append("RAW_NORMALIZED_CONFLICT")
        except (KeyError, ValueError, HistoricalDataError):
            issues.append("RAW_REPARSE_FAILED")
        return tuple(dict.fromkeys(issues))

    def dataset_dir(self, dataset_id: str) -> Path:
        return self.root / "datasets" / dataset_id

    def _build_manifest(self, dataset_id: str, source: Path, raw_path: Path, context: DatasetContext, records: Sequence[MarketRecord], raw_sha: str, normalized_sha: str) -> dict[str, Any]:
        symbols = sorted({record.symbol for record in records if hasattr(record, "symbol")})
        event_times = []
        for record in records:
            timestamp = getattr(record, "timestamp_utc", None)
            if timestamp is None:
                timestamp = getattr(record, "source_timestamp_utc", None)
            if timestamp is not None:
                event_times.append(timestamp)
        warnings = []
        if context.record_type in {"order_book_snapshot", "order_book_side"} and not event_times:
            warnings.append("Source depth schema has no event timestamp; captured/ingested time is not market event time.")
        if context.record_type == "public_trades":
            warnings.append("Current documented trade schema has no stable trade ID; fallback content keys can collide for distinct equal-valued trades.")
        return {
            "manifest_schema_version": SCHEMA_VERSION,
            "dataset_id": dataset_id,
            "identity": context.identity(raw_sha, source.suffix.lower()),
            "record_type": context.record_type,
            "schema_version": SCHEMA_VERSION,
            "code_version": context.code_version,
            "source_id": context.source_id,
            "source_url": context.source_url,
            "retrieval_method": context.retrieval_method,
            "retrieved_at_utc": time_text(context.retrieved_at_utc),
            "ingested_at_utc": time_text(context.ingested_at_utc),
            "captured_at_utc": time_text(context.captured_at_utc) if context.captured_at_utc else None,
            "original_filename": source.name,
            "original_extension": source.suffix.lower(),
            "raw_relative_path": raw_path.relative_to(self.root).as_posix(),
            "raw_sha256": raw_sha,
            "normalized_relative_path": (Path("datasets") / dataset_id / "records.jsonl").as_posix(),
            "normalized_sha256": normalized_sha,
            "record_count": len(records),
            "symbols": symbols,
            "symbol": context.symbol if context.symbol is not None else (symbols[0] if len(symbols) == 1 else None),
            "interval_seconds": context.interval_seconds,
            "event_range_start_utc": time_text(min(event_times)) if event_times else None,
            "event_range_end_utc": time_text(max(event_times)) if event_times else None,
            "warnings": warnings,
        }

    @staticmethod
    def _write_immutable(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            raise HistoricalDataError(f"refusing to trust symlink at immutable raw path: {path}")
        if path.exists():
            try:
                existing = path.read_bytes()
            except OSError as exc:
                raise HistoricalDataError(f"cannot verify existing immutable raw file: {exc}") from exc
            if existing != data:
                raise HistoricalDataError("content-address collision: raw bytes differ; refusing overwrite")
            return
        DatasetStore._write_new(path, data)

    @staticmethod
    def _write_new(path: Path, data: bytes) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.is_symlink():
            raise HistoricalDataError(f"refusing to write through symlink: {path}")
        if path.exists():
            if path.read_bytes() != data:
                raise HistoricalDataError(f"refusing to overwrite conflicting file: {path}")
            return
        handle, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        try:
            with os.fdopen(handle, "wb") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary_name, path)
            except FileExistsError:
                if path.read_bytes() != data:
                    raise HistoricalDataError(f"concurrent write conflicts with immutable file: {path}")
        finally:
            try:
                os.unlink(temporary_name)
            except FileNotFoundError:
                pass

    @staticmethod
    def _verify_hash(path: Path, expected: Any, description: str) -> None:
        if not isinstance(expected, str) or not path.exists() or hashlib.sha256(path.read_bytes()).hexdigest() != expected:
            raise HistoricalDataError(f"{description} SHA-256 does not match manifest")


def canonical_identity_id(identity: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json_bytes(identity)).hexdigest()
