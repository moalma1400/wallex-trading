"""Strict local CSV ingestion; this module has no networking or repair behavior."""
from __future__ import annotations

import csv
from datetime import datetime
from pathlib import Path

from .models import Candle, DataError

REQUIRED_COLUMNS = ("symbol", "timestamp", "open", "high", "low", "close", "volume")


class CSVDataError(ValueError):
    """Local dataset cannot be parsed under the declared input schema."""


def load_candles(path: str | Path) -> list[Candle]:
    candles: list[Candle] = []
    try:
        with Path(path).open("r", encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            if tuple(reader.fieldnames or ()) != REQUIRED_COLUMNS:
                raise CSVDataError("CSV header must be exactly: " + ",".join(REQUIRED_COLUMNS))
            for row_number, row in enumerate(reader, start=2):
                if None in row or any(row.get(column) is None or not row[column].strip() for column in REQUIRED_COLUMNS):
                    raise CSVDataError(f"row {row_number}: missing or extra CSV field")
                timestamp_text = row["timestamp"].strip()
                try:
                    timestamp = datetime.fromisoformat(timestamp_text[:-1] + "+00:00" if timestamp_text.endswith("Z") else timestamp_text)
                    candles.append(Candle(
                        symbol=row["symbol"],
                        timestamp=timestamp,
                        open=row["open"].strip(),
                        high=row["high"].strip(),
                        low=row["low"].strip(),
                        close=row["close"].strip(),
                        volume=row["volume"].strip(),
                    ))
                except (ValueError, DataError) as exc:
                    raise CSVDataError(f"row {row_number}: {exc}") from exc
    except OSError as exc:
        raise CSVDataError(f"cannot read local CSV file: {exc}") from exc
    return candles
