"""Small local SQLite store for restart-safe shadow price observations."""
from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Any

class ObservationStore:
    """Persist latest observation per symbol; contains no credentials/account data."""
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS latest_prices (
                symbol TEXT PRIMARY KEY, price TEXT NOT NULL, observed_at TEXT NOT NULL
            )""")

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.execute("PRAGMA busy_timeout=5000")
        return db

    def get(self, symbol: str) -> tuple[str, str] | None:
        with self._connect() as db:
            row = db.execute("SELECT price, observed_at FROM latest_prices WHERE symbol=?", (symbol,)).fetchone()
        return (str(row[0]), str(row[1])) if row else None

    def put(self, symbol: str, price: Any, observed_at: str) -> None:
        with self._connect() as db:
            db.execute("INSERT INTO latest_prices(symbol,price,observed_at) VALUES(?,?,?) "
                       "ON CONFLICT(symbol) DO UPDATE SET price=excluded.price, observed_at=excluded.observed_at",
                       (symbol, str(price), observed_at))
