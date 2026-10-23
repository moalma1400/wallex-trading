"""Local audit for candle JSONL datasets; never connects to Wallex or trades."""
from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import json
from pathlib import Path
from typing import Any, Iterable, Mapping

from .backtest import BacktestError, Candle


def _parse_timestamp(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError("timestamp must include timezone")
    return parsed.astimezone(timezone.utc)


def audit_candles(
    lines: Iterable[str],
    *,
    expected_symbol: str | None = None,
    expected_interval_seconds: int | None = None,
    manifest: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Audit candle lines and distinguish hard structure errors from possible gaps.

    Timestamp gaps are advisory: a no-trade interval can legitimately produce no
    candle, so the tool reports potential missing buckets instead of claiming
    that every absent interval is a feed outage.
    """
    if expected_interval_seconds is not None and (
        isinstance(expected_interval_seconds, bool)
        or not isinstance(expected_interval_seconds, int)
        or expected_interval_seconds < 1
    ):
        raise ValueError("expected_interval_seconds must be a positive integer")
    if expected_symbol is not None:
        expected_symbol = expected_symbol.strip().upper()
        if not expected_symbol:
            raise ValueError("expected_symbol must be non-empty when supplied")

    issues: list[dict[str, Any]] = []
    records: list[dict[str, Any]] = []
    valid = []
    blank_lines = 0
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            blank_lines += 1
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            issues.append({"code": "INVALID_JSON", "line": line_number, "severity": "error"})
            continue
        if not isinstance(row, dict):
            issues.append({"code": "ROW_NOT_OBJECT", "line": line_number, "severity": "error"})
            continue
        try:
            candle = Candle.from_mapping(row)
        except (BacktestError, ValueError, TypeError) as exc:
            issues.append({
                "code": "INVALID_CANDLE",
                "line": line_number,
                "severity": "error",
                "detail": str(exc)[:180],
            })
            continue
        timestamp = _parse_timestamp(candle.timestamp)
        symbol_value = row.get("symbol")
        symbol = symbol_value.strip().upper() if isinstance(symbol_value, str) and symbol_value.strip() else None
        interval_value = row.get("interval_seconds")
        interval = None
        if interval_value is not None:
            if isinstance(interval_value, bool) or not isinstance(interval_value, int) or interval_value < 1:
                issues.append({"code": "INVALID_INTERVAL_METADATA", "line": line_number, "severity": "error"})
            else:
                interval = interval_value
        if symbol is None:
            issues.append({"code": "MISSING_SYMBOL_METADATA", "line": line_number, "severity": "warning"})
        if interval is None:
            if interval_value is None:
                issues.append({"code": "MISSING_INTERVAL_METADATA", "line": line_number, "severity": "warning"})
        elif expected_interval_seconds is not None and interval != expected_interval_seconds:
            issues.append({"code": "INTERVAL_MISMATCH", "line": line_number, "severity": "error",
                           "expected": expected_interval_seconds, "actual": interval})
        if expected_symbol and symbol and symbol != expected_symbol:
            issues.append({"code": "SYMBOL_MISMATCH", "line": line_number, "severity": "error",
                           "expected": expected_symbol, "actual": symbol})
        records.append({"line": line_number, "timestamp": timestamp, "symbol": symbol,
                        "interval_seconds": interval, "candle": candle})
        valid.append(candle)

    effective_intervals = {r["interval_seconds"] for r in records if r["interval_seconds"] is not None}
    effective_symbols = {r["symbol"] for r in records if r["symbol"] is not None}
    interval_seconds = expected_interval_seconds
    if interval_seconds is None and len(effective_intervals) == 1:
        interval_seconds = next(iter(effective_intervals))
    if len(effective_intervals) > 1:
        issues.append({"code": "MIXED_INTERVALS", "severity": "error",
                       "values": sorted(effective_intervals)})
    if len(effective_symbols) > 1:
        issues.append({"code": "MIXED_SYMBOLS", "severity": "error",
                       "values": sorted(effective_symbols)})
    if expected_symbol and effective_symbols and effective_symbols != {expected_symbol}:
        # Row-level issues already carry line numbers; this summary makes the dataset-level fact explicit.
        pass

    gaps = []
    duplicate_timestamps = 0
    out_of_order = 0
    unaligned = 0
    seen: set[datetime] = set()
    previous: dict[str, Any] | None = None
    for record in records:
        timestamp = record["timestamp"]
        if timestamp in seen:
            duplicate_timestamps += 1
            issues.append({"code": "DUPLICATE_TIMESTAMP", "line": record["line"],
                           "severity": "error", "timestamp": timestamp.isoformat()})
        seen.add(timestamp)
        if interval_seconds is not None and int(timestamp.timestamp()) % interval_seconds != 0:
            unaligned += 1
            issues.append({"code": "UNALIGNED_CANDLE_START", "line": record["line"],
                           "severity": "error", "timestamp": timestamp.isoformat(),
                           "interval_seconds": interval_seconds})
        if previous is not None:
            delta = (timestamp - previous["timestamp"]).total_seconds()
            if delta < 0:
                out_of_order += 1
                issues.append({"code": "OUT_OF_ORDER_TIMESTAMP", "line": record["line"],
                               "severity": "error", "seconds_from_previous": int(delta)})
            elif delta > 0 and interval_seconds is not None and delta > interval_seconds:
                missing = max(0, int(delta // interval_seconds) - 1) if delta % interval_seconds == 0 else None
                gap = {
                    "from": previous["timestamp"].isoformat().replace("+00:00", "Z"),
                    "to": timestamp.isoformat().replace("+00:00", "Z"),
                    "elapsed_seconds": int(delta),
                    "potential_missing_buckets": missing,
                    "interpretation": "potential_gap_or_no_trades; verify before backtesting",
                }
                gaps.append(gap)
                issues.append({"code": "POTENTIAL_TIMESTAMP_GAP", "line": record["line"],
                               "severity": "warning", "elapsed_seconds": int(delta),
                               "potential_missing_buckets": missing})
            # Keep the last processed timestamp as reference to detect actual file ordering.
        previous = record

    first_ts = min((r["timestamp"] for r in records), default=None)
    last_ts = max((r["timestamp"] for r in records), default=None)
    error_count = sum(issue["severity"] == "error" for issue in issues)
    warning_count = sum(issue["severity"] == "warning" for issue in issues)
    status = "INVALID" if error_count else ("REVIEW" if warning_count or gaps else "OK")
    manifest_summary = None
    if isinstance(manifest, Mapping):
        manifest_summary = {
            key: manifest.get(key) for key in (
                "symbol", "interval_seconds", "status", "closed_candles_written_this_run",
                "malformed_or_unmatched_messages", "connection_count", "reconnect_count",
                "connection_errors", "discarded_partial_candles", "gaps_possible_on_disconnect",
                "last_closed_candle_utc",
            ) if key in manifest
        }
        if manifest.get("gaps_possible_on_disconnect") is True or manifest.get("connection_errors", 0):
            issues.append({"code": "RECORDER_MANIFEST_REPORTS_CONNECTION_GAPS", "severity": "warning"})
            warning_count += 1
            if status == "OK":
                status = "REVIEW"

    def iso(value: datetime | None) -> str | None:
        return value.isoformat().replace("+00:00", "Z") if value else None

    return {
        "schema_version": 1,
        "status": status,
        "input_rows_valid": len(valid),
        "input_blank_lines": blank_lines,
        "invalid_records": sum(issue["code"] in {"INVALID_JSON", "ROW_NOT_OBJECT", "INVALID_CANDLE"} for issue in issues),
        "duplicate_timestamps": duplicate_timestamps,
        "out_of_order_timestamps": out_of_order,
        "unaligned_candle_starts": unaligned,
        "potential_gaps": len(gaps),
        "potential_missing_buckets_known": sum(g["potential_missing_buckets"] or 0 for g in gaps),
        "symbol": expected_symbol or (next(iter(effective_symbols)) if len(effective_symbols) == 1 else None),
        "interval_seconds": interval_seconds,
        "first_timestamp_utc": iso(first_ts),
        "last_timestamp_utc": iso(last_ts),
        "elapsed_seconds": int((last_ts - first_ts).total_seconds()) if first_ts and last_ts else None,
        "error_count": error_count,
        "warning_count": warning_count,
        "gaps": gaps,
        "manifest": manifest_summary,
        "issues": issues,
        "note": "Timestamp gaps may be legitimate no-trade intervals; verify before interpreting backtest results.",
        "order_submission_attempted": False,
    }


def audit_file(
    input_path: str | Path,
    *,
    expected_symbol: str | None = None,
    expected_interval_seconds: int | None = None,
    manifest_path: str | Path | None = None,
) -> dict[str, Any]:
    path = Path(input_path)
    manifest = None
    manifest_candidate = Path(manifest_path) if manifest_path else Path(str(path) + ".manifest.json")
    if manifest_candidate.exists():
        try:
            parsed = json.loads(manifest_candidate.read_text(encoding="utf-8"))
            if isinstance(parsed, dict):
                manifest = parsed
        except (OSError, json.JSONDecodeError):
            manifest = None
    return audit_candles(
        path.read_text(encoding="utf-8").splitlines(),
        expected_symbol=expected_symbol,
        expected_interval_seconds=expected_interval_seconds,
        manifest=manifest,
    )
