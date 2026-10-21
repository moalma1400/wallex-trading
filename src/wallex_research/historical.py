"""Versioned canonical local market records and strict offline source parsers.

No exchange/API client is implemented here. Raw files are retained separately by
DatasetStore; these records are deterministic normalized derivatives.
"""
from __future__ import annotations

import csv
import hashlib
import io
import json
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence, TypeAlias
from types import MappingProxyType
from urllib.parse import urlsplit

from .models import Candle, DataError

SCHEMA_VERSION = "1.0"
CODE_VERSION = "0.3.0"
CANDLE_CSV_COLUMNS = ("symbol", "timestamp", "open", "high", "low", "close", "volume")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


class HistoricalDataError(ValueError):
    """Local source data is ambiguous or violates the canonical import schema."""


def decimal_exact(value: Any, name: str) -> Decimal:
    """Parse JSON/CSV decimal values without a binary float conversion."""
    if isinstance(value, bool) or isinstance(value, float):
        raise HistoricalDataError(f"{name} must be decimal text, Decimal, or integer; binary floats are rejected")
    if not isinstance(value, (str, int, Decimal)):
        raise HistoricalDataError(f"{name} must be decimal text, Decimal, or integer")
    try:
        result = value if isinstance(value, Decimal) else Decimal(value)
    except (InvalidOperation, ValueError) as exc:
        raise HistoricalDataError(f"{name} is not a valid decimal") from exc
    if not result.is_finite():
        raise HistoricalDataError(f"{name} must be finite")
    return result


def utc_time(value: Any, name: str) -> datetime:
    if isinstance(value, str):
        try:
            text = value[:-1] + "+00:00" if value.endswith("Z") else value
            value = datetime.fromisoformat(text)
        except ValueError as exc:
            raise HistoricalDataError(f"{name} must be ISO-8601 with an explicit UTC offset") from exc
    if not isinstance(value, datetime) or value.tzinfo is None or value.utcoffset() is None:
        raise HistoricalDataError(f"{name} must be timezone-aware; naive timestamps are ambiguous")
    return value.astimezone(timezone.utc)


def time_text(value: datetime) -> str:
    normalized = utc_time(value, "timestamp")
    if not normalized.microsecond:
        return normalized.strftime("%Y-%m-%dT%H:%M:%SZ")
    text = normalized.isoformat(timespec="microseconds").replace("+00:00", "Z")
    return text[:-1].rstrip("0").rstrip(".") + "Z"


def _required_text(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise HistoricalDataError(f"{name} must be a non-empty string")
    return value.strip()


def _optional_bool(value: Any, name: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise HistoricalDataError(f"{name} must be a boolean when present")
    return value


def _json_no_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise HistoricalDataError(f"duplicate JSON object key: {key}")
        result[key] = value
    return result


def _reject_json_constant(value: str) -> None:
    raise HistoricalDataError(f"non-standard JSON numeric constant is not accepted: {value}")


@dataclass(frozen=True, slots=True)
class Provenance:
    source_id: str
    source_url: str
    retrieval_method: str
    retrieved_at_utc: datetime
    ingested_at_utc: datetime
    raw_sha256: str
    schema_version: str = SCHEMA_VERSION
    code_version: str = CODE_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "source_id", _required_text(self.source_id, "source_id"))
        object.__setattr__(self, "source_url", _required_text(self.source_url, "source_url"))
        parsed = urlsplit(self.source_url)
        if parsed.scheme not in {"https", "urn"}:
            raise HistoricalDataError("source_url must be HTTPS or an explicit URN (synthetic fixtures may use example.invalid)")
        object.__setattr__(self, "retrieval_method", _required_text(self.retrieval_method, "retrieval_method"))
        object.__setattr__(self, "retrieved_at_utc", utc_time(self.retrieved_at_utc, "retrieved_at_utc"))
        object.__setattr__(self, "ingested_at_utc", utc_time(self.ingested_at_utc, "ingested_at_utc"))
        if not _SHA256_RE.fullmatch(self.raw_sha256):
            raise HistoricalDataError("raw_sha256 must be 64 lowercase hexadecimal characters")
        if self.schema_version != SCHEMA_VERSION:
            raise HistoricalDataError(f"unsupported normalized schema version: {self.schema_version}")
        object.__setattr__(self, "code_version", _required_text(self.code_version, "code_version"))


@dataclass(frozen=True, slots=True)
class DatasetContext:
    record_type: str
    source_id: str
    source_url: str
    retrieval_method: str
    retrieved_at_utc: datetime
    ingested_at_utc: datetime
    captured_at_utc: datetime | None = None
    symbol: str | None = None
    interval_seconds: int | None = None
    code_version: str = CODE_VERSION

    def __post_init__(self) -> None:
        allowed = {"candles", "market_metadata", "public_trades", "fair_price_snapshot", "order_book_snapshot", "order_book_side"}
        if self.record_type not in allowed:
            raise HistoricalDataError(f"record_type must be one of {', '.join(sorted(allowed))}")
        object.__setattr__(self, "source_id", _required_text(self.source_id, "source_id"))
        object.__setattr__(self, "source_url", _required_text(self.source_url, "source_url"))
        if urlsplit(self.source_url).scheme not in {"https", "urn"}:
            raise HistoricalDataError("source_url must use HTTPS or URN")
        object.__setattr__(self, "retrieval_method", _required_text(self.retrieval_method, "retrieval_method"))
        object.__setattr__(self, "retrieved_at_utc", utc_time(self.retrieved_at_utc, "retrieved_at_utc"))
        object.__setattr__(self, "ingested_at_utc", utc_time(self.ingested_at_utc, "ingested_at_utc"))
        if self.captured_at_utc is not None:
            object.__setattr__(self, "captured_at_utc", utc_time(self.captured_at_utc, "captured_at_utc"))
        if self.record_type in {"order_book_snapshot", "order_book_side"} and self.captured_at_utc is None:
            raise HistoricalDataError("depth import requires explicit captured_at_utc; ingestion time is not market capture time")
        if self.symbol is not None:
            object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))
        if self.interval_seconds is not None and (isinstance(self.interval_seconds, bool) or not isinstance(self.interval_seconds, int) or self.interval_seconds <= 0):
            raise HistoricalDataError("interval_seconds must be a positive integer")
        if self.record_type == "candles" and (self.symbol is None or self.interval_seconds is None):
            raise HistoricalDataError("candle imports require explicit symbol and interval_seconds context")
        object.__setattr__(self, "code_version", _required_text(self.code_version, "code_version"))

    def identity(self, raw_sha256: str, input_format: str) -> dict[str, Any]:
        """Stable dataset identity excludes re-import time but includes parser format."""
        normalized_format = input_format.lower()
        if normalized_format not in {".csv", ".json", ".jsonl"}:
            raise HistoricalDataError("input_format must be .csv, .json, or .jsonl")
        return {
            "schema_version": SCHEMA_VERSION,
            "code_version": self.code_version,
            "record_type": self.record_type,
            "input_format": normalized_format,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "retrieval_method": self.retrieval_method,
            "symbol": self.symbol,
            "interval_seconds": self.interval_seconds,
            "captured_at_utc": time_text(self.captured_at_utc) if self.captured_at_utc else None,
            "raw_sha256": raw_sha256,
        }


@dataclass(frozen=True, slots=True)
class CandleRecord:
    symbol: str
    interval_seconds: int
    timestamp_utc: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    provenance: Provenance
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))
        if isinstance(self.interval_seconds, bool) or not isinstance(self.interval_seconds, int) or self.interval_seconds <= 0:
            raise HistoricalDataError("interval_seconds must be a positive integer")
        object.__setattr__(self, "timestamp_utc", utc_time(self.timestamp_utc, "candle timestamp"))
        for field in ("open", "high", "low", "close", "volume"):
            object.__setattr__(self, field, decimal_exact(getattr(self, field), field))
        if min(self.open, self.high, self.low, self.close) <= 0:
            raise HistoricalDataError("candle OHLC prices must be positive")
        if self.volume < 0:
            raise HistoricalDataError("candle volume must be nonnegative")
        if self.low > self.high or not self.low <= self.open <= self.high or not self.low <= self.close <= self.high:
            raise HistoricalDataError("candle OHLC values must satisfy low <= open/close <= high")
        if self.schema_version != SCHEMA_VERSION:
            raise HistoricalDataError(f"unsupported candle schema version: {self.schema_version}")

    def to_replay_candle(self) -> Candle:
        return Candle(self.symbol, self.timestamp_utc, self.open, self.high, self.low, self.close, self.volume)


@dataclass(frozen=True, slots=True)
class MarketMetadataRecord:
    symbol: str
    base_asset: str
    quote_asset: str
    is_spot: bool | None
    is_otc: bool | None
    is_margin: bool | None
    price_precision: int | None
    amount_precision: int | None
    provenance: Provenance
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        for field in ("symbol", "base_asset", "quote_asset"):
            object.__setattr__(self, field, _required_text(getattr(self, field), field))
        for field in ("is_spot", "is_otc", "is_margin"):
            object.__setattr__(self, field, _optional_bool(getattr(self, field), field))
        for field in ("price_precision", "amount_precision"):
            value = getattr(self, field)
            if value is not None and (isinstance(value, bool) or not isinstance(value, int) or value < 0):
                raise HistoricalDataError(f"{field} must be a nonnegative integer when present")
        if self.schema_version != SCHEMA_VERSION:
            raise HistoricalDataError(f"unsupported metadata schema version: {self.schema_version}")


@dataclass(frozen=True, slots=True)
class PublicTradeRecord:
    symbol: str
    timestamp_utc: datetime
    quantity: Decimal
    price: Decimal
    is_buy_order: bool | None
    sum: Decimal | None
    provenance: Provenance
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))
        object.__setattr__(self, "timestamp_utc", utc_time(self.timestamp_utc, "trade timestamp"))
        object.__setattr__(self, "quantity", decimal_exact(self.quantity, "quantity"))
        object.__setattr__(self, "price", decimal_exact(self.price, "price"))
        if self.quantity <= 0 or self.price <= 0:
            raise HistoricalDataError("trade quantity and price must be positive")
        object.__setattr__(self, "is_buy_order", _optional_bool(self.is_buy_order, "isBuyOrder"))
        if self.sum is not None:
            object.__setattr__(self, "sum", decimal_exact(self.sum, "sum"))
            if self.sum < 0:
                raise HistoricalDataError("trade sum must be nonnegative")
        if self.schema_version != SCHEMA_VERSION:
            raise HistoricalDataError(f"unsupported trade schema version: {self.schema_version}")


@dataclass(frozen=True, slots=True)
class FairPriceSnapshotRecord:
    timestamp_utc: datetime
    prices: Mapping[str, Decimal]
    provenance: Provenance
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "timestamp_utc", utc_time(self.timestamp_utc, "fair-price timestamp"))
        normalized: dict[str, Decimal] = {}
        for symbol, price in self.prices.items():
            normalized[_required_text(symbol, "price symbol")] = decimal_exact(price, f"price[{symbol}]")
            if normalized[symbol] <= 0:
                raise HistoricalDataError(f"price[{symbol}] must be positive")
        if not normalized:
            raise HistoricalDataError("fair-price snapshot must contain at least one available symbol")
        object.__setattr__(self, "prices", MappingProxyType(dict(sorted(normalized.items()))))
        if self.schema_version != SCHEMA_VERSION:
            raise HistoricalDataError(f"unsupported ticker schema version: {self.schema_version}")


@dataclass(frozen=True, slots=True)
class BookLevel:
    price: Decimal
    quantity: Decimal
    sum: Decimal | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "price", decimal_exact(self.price, "book price"))
        object.__setattr__(self, "quantity", decimal_exact(self.quantity, "book quantity"))
        if self.price <= 0 or self.quantity < 0:
            raise HistoricalDataError("book price must be positive and quantity nonnegative")
        if self.sum is not None:
            object.__setattr__(self, "sum", decimal_exact(self.sum, "book sum"))
            if self.sum < 0:
                raise HistoricalDataError("book sum must be nonnegative")


@dataclass(frozen=True, slots=True)
class OrderBookSnapshotRecord:
    symbol: str
    captured_at_utc: datetime
    bids: tuple[BookLevel, ...]
    asks: tuple[BookLevel, ...]
    provenance: Provenance
    source_timestamp_utc: datetime | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))
        object.__setattr__(self, "captured_at_utc", utc_time(self.captured_at_utc, "capture timestamp"))
        if self.source_timestamp_utc is not None:
            object.__setattr__(self, "source_timestamp_utc", utc_time(self.source_timestamp_utc, "source timestamp"))
        object.__setattr__(self, "bids", tuple(self.bids))
        object.__setattr__(self, "asks", tuple(self.asks))
        if not self.bids and not self.asks:
            raise HistoricalDataError("order book must contain at least one documented side")
        if self.schema_version != SCHEMA_VERSION:
            raise HistoricalDataError(f"unsupported order-book schema version: {self.schema_version}")


@dataclass(frozen=True, slots=True)
class OrderBookSideSnapshotRecord:
    symbol: str
    side: str
    captured_at_utc: datetime
    levels: tuple[BookLevel, ...]
    provenance: Provenance
    source_timestamp_utc: datetime | None = None
    schema_version: str = SCHEMA_VERSION

    def __post_init__(self) -> None:
        object.__setattr__(self, "symbol", _required_text(self.symbol, "symbol"))
        if self.side not in {"bid", "ask"}:
            raise HistoricalDataError("depth side must be 'bid' or 'ask'")
        object.__setattr__(self, "captured_at_utc", utc_time(self.captured_at_utc, "capture timestamp"))
        if self.source_timestamp_utc is not None:
            object.__setattr__(self, "source_timestamp_utc", utc_time(self.source_timestamp_utc, "source timestamp"))
        object.__setattr__(self, "levels", tuple(self.levels))
        if not self.levels:
            raise HistoricalDataError("order-book side snapshot must contain at least one level")
        if self.schema_version != SCHEMA_VERSION:
            raise HistoricalDataError(f"unsupported order-book schema version: {self.schema_version}")


MarketRecord: TypeAlias = CandleRecord | MarketMetadataRecord | PublicTradeRecord | FairPriceSnapshotRecord | OrderBookSnapshotRecord | OrderBookSideSnapshotRecord


@dataclass(frozen=True, slots=True)
class HistoricalDataRequest:
    record_type: str
    symbol: str
    start_utc: datetime
    end_utc: datetime
    interval_seconds: int | None = None

    def __post_init__(self) -> None:
        if self.record_type not in {"candles", "public_trades"}:
            raise HistoricalDataError("future historical query supports only candles or public_trades")
        object.__setattr__(self, "symbol", _required_text(self.symbol, "query symbol"))
        object.__setattr__(self, "start_utc", utc_time(self.start_utc, "query start"))
        object.__setattr__(self, "end_utc", utc_time(self.end_utc, "query end"))
        if self.end_utc <= self.start_utc:
            raise HistoricalDataError("query end must be later than query start")
        if self.record_type == "candles" and (self.interval_seconds is None or isinstance(self.interval_seconds, bool) or not isinstance(self.interval_seconds, int) or self.interval_seconds <= 0):
            raise HistoricalDataError("candle query requires explicit positive interval_seconds")


class HistoricalDataProvider(Protocol):
    """Future read-only source seam. No implementation or network behavior exists."""

    def read(self, request: HistoricalDataRequest) -> Iterable[Mapping[str, Any]]:
        """Yield records for an explicit query; protocol alone has no side effects."""
        ...


def parse_local_bytes(data: bytes, path: Path, context: DatasetContext, raw_sha256: str) -> tuple[MarketRecord, ...]:
    provenance = Provenance(context.source_id, context.source_url, context.retrieval_method, context.retrieved_at_utc, context.ingested_at_utc, raw_sha256, code_version=context.code_version)
    suffix = path.suffix.lower()
    if suffix == ".csv":
        if context.record_type != "candles":
            raise HistoricalDataError("CSV input is currently supported only for candles")
        return _parse_candle_csv(data, context, provenance)
    if suffix not in {".json", ".jsonl"}:
        raise HistoricalDataError("local input extension must be .csv, .json, or .jsonl")
    try:
        text = data.decode("utf-8-sig")
        if suffix == ".jsonl":
            value = [json.loads(line, parse_float=Decimal, parse_int=int, object_pairs_hook=_json_no_duplicate_keys, parse_constant=_reject_json_constant) for line in text.splitlines() if line.strip()]
        else:
            value = json.loads(text, parse_float=Decimal, parse_int=int, object_pairs_hook=_json_no_duplicate_keys, parse_constant=_reject_json_constant)
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise HistoricalDataError(f"invalid UTF-8 JSON source: {exc}") from exc
    return _parse_json_value(value, context, provenance)


def _parse_candle_csv(data: bytes, context: DatasetContext, provenance: Provenance) -> tuple[CandleRecord, ...]:
    try:
        text = data.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text, newline=""))
        if tuple(reader.fieldnames or ()) != CANDLE_CSV_COLUMNS:
            raise HistoricalDataError("CSV header must be exactly: " + ",".join(CANDLE_CSV_COLUMNS))
        result: list[CandleRecord] = []
        for row_number, row in enumerate(reader, start=2):
            if None in row or any(row.get(field) is None or not row[field].strip() for field in CANDLE_CSV_COLUMNS):
                raise HistoricalDataError(f"row {row_number}: missing or extra CSV field")
            if row["symbol"].strip() != context.symbol:
                raise HistoricalDataError(f"row {row_number}: symbol differs from explicit import symbol")
            try:
                result.append(CandleRecord(
                    symbol=context.symbol or "",
                    interval_seconds=context.interval_seconds or 0,
                    timestamp_utc=utc_time(row["timestamp"].strip(), f"row {row_number} timestamp"),
                    open=decimal_exact(row["open"].strip(), f"row {row_number} open"),
                    high=decimal_exact(row["high"].strip(), f"row {row_number} high"),
                    low=decimal_exact(row["low"].strip(), f"row {row_number} low"),
                    close=decimal_exact(row["close"].strip(), f"row {row_number} close"),
                    volume=decimal_exact(row["volume"].strip(), f"row {row_number} volume"),
                    provenance=provenance,
                ))
            except (HistoricalDataError, DataError) as exc:
                raise HistoricalDataError(f"row {row_number}: {exc}") from exc
        return tuple(result)
    except UnicodeDecodeError as exc:
        raise HistoricalDataError("CSV source must be valid UTF-8") from exc
    except csv.Error as exc:
        raise HistoricalDataError(f"malformed CSV source: {exc}") from exc


def _extract_list(value: Any, keys: Sequence[str]) -> list[Any]:
    current = value
    if isinstance(current, dict):
        for key in keys:
            if key in current:
                current = current[key]
                break
    if not isinstance(current, list):
        raise HistoricalDataError(f"expected a JSON array at one of these documented fields: {', '.join(keys)}")
    return current


def _parse_json_value(value: Any, context: DatasetContext, provenance: Provenance) -> tuple[MarketRecord, ...]:
    kind = context.record_type
    if kind == "candles":
        return _parse_candle_json(value, context, provenance)
    if kind == "market_metadata":
        current = value.get("result", value) if isinstance(value, dict) else value
        rows = _extract_list(current, ("markets",))
        return tuple(_parse_market(row, provenance) for row in rows)
    if kind == "public_trades":
        current = value
        if isinstance(current, dict) and "result" in current:
            current = current["result"]
        rows = _extract_list(current, ("latestTrades", "trades"))
        return tuple(_parse_trade(row, context, provenance) for row in rows)
    if kind == "fair_price_snapshot":
        current = value
        if isinstance(current, dict) and "push" in current:
            current = current["push"].get("pub", {}).get("data")
        if not isinstance(current, dict) or not isinstance(current.get("prices"), dict):
            raise HistoricalDataError("fair-price JSON requires documented object {ts, prices}")
        prices = {symbol: decimal_exact(price, f"prices[{symbol}]") for symbol, price in current["prices"].items()}
        return (FairPriceSnapshotRecord(utc_time(current.get("ts"), "fair-price ts"), prices, provenance),)
    if kind == "order_book_snapshot":
        current = value.get("result") if isinstance(value, dict) and "result" in value else value
        if not isinstance(current, dict) or not isinstance(current.get("bid"), list) or not isinstance(current.get("ask"), list):
            raise HistoricalDataError("REST depth JSON requires documented result.bid and result.ask arrays")
        if context.symbol is None:
            raise HistoricalDataError("order-book imports require explicit symbol context")
        bids = tuple(_parse_level(row) for row in current["bid"])
        asks = tuple(_parse_level(row) for row in current["ask"])
        return (OrderBookSnapshotRecord(context.symbol, context.captured_at_utc or context.ingested_at_utc, bids, asks, provenance),)
    if kind == "order_book_side":
        return (_parse_order_book_side(value, context, provenance),)
    raise HistoricalDataError(f"unsupported record type: {kind}")


def _parse_candle_json(value: Any, context: DatasetContext, provenance: Provenance) -> tuple[CandleRecord, ...]:
    if context.symbol is None or context.interval_seconds is None:
        raise HistoricalDataError("candle JSON requires explicit symbol and interval_seconds context")
    if isinstance(value, dict) and all(field in value for field in ("t", "o", "h", "l", "c", "v")):
        if value.get("s") not in (None, "ok"):
            raise HistoricalDataError(f"UDF candle status is not ok: {value.get('s')}")
        arrays = [value[field] for field in ("t", "o", "h", "l", "c", "v")]
        if any(not isinstance(array, list) for array in arrays):
            raise HistoricalDataError("UDF candle fields t/o/h/l/c/v must all be arrays")
        if len({len(array) for array in arrays}) != 1:
            raise HistoricalDataError("UDF candle arrays have inconsistent lengths")
        rows = []
        for index, (timestamp, open_, high, low, close, volume) in enumerate(zip(*arrays, strict=True)):
            if isinstance(timestamp, bool) or not isinstance(timestamp, int):
                raise HistoricalDataError(f"UDF t[{index}] must be Unix integer seconds")
            when = datetime(1970, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=timestamp)
            rows.append({"symbol": context.symbol, "timestamp": when, "open": open_, "high": high, "low": low, "close": close, "volume": volume})
    else:
        rows = _extract_list(value, ("candles", "records")) if isinstance(value, dict) else value
        if not isinstance(rows, list):
            raise HistoricalDataError("candle JSON must be a UDF array payload or a list of candle records")
    result = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise HistoricalDataError(f"candle JSON row {index} must be an object")
        symbol = _required_text(row.get("symbol", context.symbol), f"candle row {index} symbol")
        if symbol != context.symbol:
            raise HistoricalDataError(f"candle row {index} symbol differs from explicit import symbol")
        result.append(CandleRecord(
            symbol=symbol,
            interval_seconds=context.interval_seconds,
            timestamp_utc=utc_time(row.get("timestamp", row.get("timestamp_utc")), f"candle row {index} timestamp"),
            open=decimal_exact(row.get("open"), f"candle row {index} open"),
            high=decimal_exact(row.get("high"), f"candle row {index} high"),
            low=decimal_exact(row.get("low"), f"candle row {index} low"),
            close=decimal_exact(row.get("close"), f"candle row {index} close"),
            volume=decimal_exact(row.get("volume"), f"candle row {index} volume"),
            provenance=provenance,
        ))
    return tuple(result)


def _parse_market(row: Any, provenance: Provenance) -> MarketMetadataRecord:
    if not isinstance(row, dict):
        raise HistoricalDataError("market metadata entries must be objects")
    return MarketMetadataRecord(
        symbol=row.get("symbol"), base_asset=row.get("base_asset"), quote_asset=row.get("quote_asset"),
        is_spot=row.get("is_spot"), is_otc=row.get("is_otc"), is_margin=row.get("is_margin"),
        price_precision=row.get("price_precision"), amount_precision=row.get("amount_precision"), provenance=provenance,
    )


def _parse_trade(row: Any, context: DatasetContext, provenance: Provenance) -> PublicTradeRecord:
    if not isinstance(row, dict):
        raise HistoricalDataError("public trade entries must be objects")
    symbol = row.get("symbol", context.symbol)
    if symbol is None:
        raise HistoricalDataError("trade row lacks a symbol and no explicit context symbol was supplied")
    return PublicTradeRecord(
        symbol=symbol,
        timestamp_utc=utc_time(row.get("timestamp"), "trade timestamp"),
        quantity=decimal_exact(row.get("quantity"), "trade quantity"),
        price=decimal_exact(row.get("price"), "trade price"),
        is_buy_order=row.get("isBuyOrder"),
        sum=decimal_exact(row["sum"], "trade sum") if row.get("sum") is not None else None,
        provenance=provenance,
    )


def _parse_level(row: Any) -> BookLevel:
    if not isinstance(row, dict):
        raise HistoricalDataError("order-book level must be an object")
    return BookLevel(decimal_exact(row.get("price"), "book price"), decimal_exact(row.get("quantity"), "book quantity"), decimal_exact(row["sum"], "book sum") if row.get("sum") is not None else None)


def _parse_order_book_side(value: Any, context: DatasetContext, provenance: Provenance) -> OrderBookSideSnapshotRecord:
    current = value
    channel = None
    if isinstance(current, list) and len(current) == 2 and isinstance(current[0], str):
        channel, current = current
    elif isinstance(current, dict) and "push" in current:
        push = current["push"]
        channel = push.get("channel")
        current = push.get("pub", {}).get("data")
    elif isinstance(current, dict):
        channel = current.get("channel")
        current = current.get("data", current.get("levels"))
    if channel is None or not isinstance(channel, str):
        raise HistoricalDataError("order-book side JSON must retain its documented channel name")
    match = re.fullmatch(r"(?:orderbook:)?([^@]+)@(buyDepth|sellDepth)", channel)
    if not match:
        raise HistoricalDataError("depth channel must end with the documented buyDepth or sellDepth channel")
    symbol = match.group(1)
    if context.symbol is not None and context.symbol != symbol:
        raise HistoricalDataError("depth channel symbol differs from explicit import symbol")
    levels_data = current
    if isinstance(current, dict):
        levels_data = current.get("data")
    if not isinstance(levels_data, list):
        raise HistoricalDataError("depth side payload must be a list of levels")
    side = "bid" if match.group(2) == "buyDepth" else "ask"
    levels = tuple(_parse_level(level) for level in levels_data)
    return OrderBookSideSnapshotRecord(symbol, side, context.captured_at_utc or context.ingested_at_utc, levels, provenance)


def record_to_dict(record: MarketRecord) -> dict[str, Any]:
    common = {"schema_version": record.schema_version, "provenance": provenance_to_dict(record.provenance)}
    if isinstance(record, CandleRecord):
        return {"record_type": "candles", **common, "symbol": record.symbol, "interval_seconds": record.interval_seconds, "timestamp_utc": time_text(record.timestamp_utc), **{field: str(getattr(record, field)) for field in ("open", "high", "low", "close", "volume")}}
    if isinstance(record, MarketMetadataRecord):
        return {"record_type": "market_metadata", **common, **{field: getattr(record, field) for field in ("symbol", "base_asset", "quote_asset", "is_spot", "is_otc", "is_margin", "price_precision", "amount_precision")}}
    if isinstance(record, PublicTradeRecord):
        return {"record_type": "public_trades", **common, "symbol": record.symbol, "timestamp_utc": time_text(record.timestamp_utc), "quantity": str(record.quantity), "price": str(record.price), "is_buy_order": record.is_buy_order, "sum": str(record.sum) if record.sum is not None else None}
    if isinstance(record, FairPriceSnapshotRecord):
        return {"record_type": "fair_price_snapshot", **common, "timestamp_utc": time_text(record.timestamp_utc), "prices": {key: str(value) for key, value in sorted(record.prices.items())}}
    if isinstance(record, OrderBookSnapshotRecord):
        return {"record_type": "order_book_snapshot", **common, "symbol": record.symbol, "captured_at_utc": time_text(record.captured_at_utc), "source_timestamp_utc": time_text(record.source_timestamp_utc) if record.source_timestamp_utc else None, "bids": [level_to_dict(level) for level in record.bids], "asks": [level_to_dict(level) for level in record.asks]}
    if isinstance(record, OrderBookSideSnapshotRecord):
        return {"record_type": "order_book_side", **common, "symbol": record.symbol, "side": record.side, "captured_at_utc": time_text(record.captured_at_utc), "source_timestamp_utc": time_text(record.source_timestamp_utc) if record.source_timestamp_utc else None, "levels": [level_to_dict(level) for level in record.levels]}
    raise TypeError(f"unsupported record class: {type(record).__name__}")


def level_to_dict(level: BookLevel) -> dict[str, str | None]:
    return {"price": str(level.price), "quantity": str(level.quantity), "sum": str(level.sum) if level.sum is not None else None}


def provenance_to_dict(value: Provenance) -> dict[str, Any]:
    return {"source_id": value.source_id, "source_url": value.source_url, "retrieval_method": value.retrieval_method, "retrieved_at_utc": time_text(value.retrieved_at_utc), "ingested_at_utc": time_text(value.ingested_at_utc), "raw_sha256": value.raw_sha256, "schema_version": value.schema_version, "code_version": value.code_version}


def record_from_dict(value: Mapping[str, Any]) -> MarketRecord:
    if value.get("schema_version") != SCHEMA_VERSION:
        raise HistoricalDataError(f"unsupported normalized schema version: {value.get('schema_version')}")
    raw_provenance = value.get("provenance")
    if not isinstance(raw_provenance, dict):
        raise HistoricalDataError("normalized record is missing provenance")
    provenance = Provenance(raw_provenance["source_id"], raw_provenance["source_url"], raw_provenance["retrieval_method"], utc_time(raw_provenance["retrieved_at_utc"], "retrieved_at_utc"), utc_time(raw_provenance["ingested_at_utc"], "ingested_at_utc"), raw_provenance["raw_sha256"], raw_provenance["schema_version"], raw_provenance["code_version"])
    kind = value.get("record_type")
    if kind == "candles":
        return CandleRecord(value["symbol"], value["interval_seconds"], utc_time(value["timestamp_utc"], "timestamp_utc"), decimal_exact(value["open"], "open"), decimal_exact(value["high"], "high"), decimal_exact(value["low"], "low"), decimal_exact(value["close"], "close"), decimal_exact(value["volume"], "volume"), provenance)
    if kind == "market_metadata":
        return MarketMetadataRecord(value["symbol"], value["base_asset"], value["quote_asset"], value.get("is_spot"), value.get("is_otc"), value.get("is_margin"), value.get("price_precision"), value.get("amount_precision"), provenance)
    if kind == "public_trades":
        return PublicTradeRecord(value["symbol"], utc_time(value["timestamp_utc"], "timestamp_utc"), decimal_exact(value["quantity"], "quantity"), decimal_exact(value["price"], "price"), value.get("is_buy_order"), decimal_exact(value["sum"], "sum") if value.get("sum") is not None else None, provenance)
    if kind == "fair_price_snapshot":
        return FairPriceSnapshotRecord(utc_time(value["timestamp_utc"], "timestamp_utc"), {k: decimal_exact(v, f"prices[{k}]") for k, v in value["prices"].items()}, provenance)
    if kind == "order_book_snapshot":
        return OrderBookSnapshotRecord(value["symbol"], utc_time(value["captured_at_utc"], "captured_at_utc"), tuple(_dict_to_level(v) for v in value["bids"]), tuple(_dict_to_level(v) for v in value["asks"]), provenance, utc_time(value["source_timestamp_utc"], "source_timestamp_utc") if value.get("source_timestamp_utc") else None)
    if kind == "order_book_side":
        return OrderBookSideSnapshotRecord(value["symbol"], value["side"], utc_time(value["captured_at_utc"], "captured_at_utc"), tuple(_dict_to_level(v) for v in value["levels"]), provenance, utc_time(value["source_timestamp_utc"], "source_timestamp_utc") if value.get("source_timestamp_utc") else None)
    raise HistoricalDataError(f"unknown normalized record_type: {kind}")


def _dict_to_level(value: Mapping[str, Any]) -> BookLevel:
    return BookLevel(decimal_exact(value["price"], "book price"), decimal_exact(value["quantity"], "book quantity"), decimal_exact(value["sum"], "book sum") if value.get("sum") is not None else None)


def canonical_json_bytes(value: Any) -> bytes:
    def encode(obj: Any) -> Any:
        if isinstance(obj, Decimal):
            return str(obj)
        if isinstance(obj, datetime):
            return time_text(obj)
        raise TypeError(f"not JSON serializable: {type(obj).__name__}")
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), default=encode, allow_nan=False).encode("utf-8")


def records_jsonl(records: Sequence[MarketRecord]) -> bytes:
    return b"".join(canonical_json_bytes(record_to_dict(record)) + b"\n" for record in records)


def parse_records_jsonl(data: bytes) -> tuple[MarketRecord, ...]:
    try:
        values = [json.loads(line, parse_float=Decimal, parse_int=int, object_pairs_hook=_json_no_duplicate_keys, parse_constant=_reject_json_constant) for line in data.decode("utf-8").splitlines() if line]
        if not all(isinstance(value, dict) for value in values):
            raise HistoricalDataError("normalized JSONL lines must be objects")
        return tuple(record_from_dict(value) for value in values)
    except (UnicodeDecodeError, json.JSONDecodeError, KeyError, TypeError, ValueError) as exc:
        raise HistoricalDataError(f"invalid normalized JSONL: {exc}") from exc


def logical_dedupe_key(record: MarketRecord) -> str:
    """Return an audit key; callers must not use it to delete input records."""
    if isinstance(record, CandleRecord):
        raw = ["candle", record.symbol, record.interval_seconds, time_text(record.timestamp_utc)]
    elif isinstance(record, MarketMetadataRecord):
        raw = ["market", record.symbol]
    elif isinstance(record, PublicTradeRecord):
        raw = ["trade-fallback", record.symbol, time_text(record.timestamp_utc), str(record.price), str(record.quantity), record.is_buy_order, str(record.sum) if record.sum is not None else None]
    elif isinstance(record, FairPriceSnapshotRecord):
        raw = ["fair-price", time_text(record.timestamp_utc)]
    elif isinstance(record, OrderBookSnapshotRecord):
        raw = ["book", record.symbol, time_text(record.captured_at_utc)]
    else:
        raw = ["book-side", record.symbol, record.side, time_text(record.captured_at_utc)]
    return hashlib.sha256(canonical_json_bytes(raw)).hexdigest()
