"""Offline-only paper broker with SQLite persistence; never connects to an exchange."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal, InvalidOperation
import json
from pathlib import Path
import sqlite3
from typing import Any


class PaperTradingError(ValueError):
    """Rejected paper order or invalid simulator configuration."""


def _decimal(value: Any, field: str) -> Decimal:
    try:
        parsed = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError) as exc:
        raise PaperTradingError(f"{field} must be a finite decimal") from exc
    if not parsed.is_finite():
        raise PaperTradingError(f"{field} must be a finite decimal")
    return parsed


class PaperBroker:
    """Deterministic virtual spot broker.

    Inputs are supplied market observations. This class deliberately has no HTTP,
    exchange client, API-key, or live-order integration. A repeated event_id is
    idempotent and returns the original fill.
    """

    def __init__(
        self,
        db_path: str | Path,
        *,
        initial_cash: Any,
        fee_bps: Any = "0",
        slippage_bps: Any = "0",
        max_order_notional: Any,
        max_daily_loss_percent: Any = "5",
    ) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initial_cash = _decimal(initial_cash, "initial_cash")
        self.fee_bps = _decimal(fee_bps, "fee_bps")
        self.slippage_bps = _decimal(slippage_bps, "slippage_bps")
        self.max_order_notional = _decimal(max_order_notional, "max_order_notional")
        self.max_daily_loss_percent = _decimal(max_daily_loss_percent, "max_daily_loss_percent")
        if self.initial_cash <= 0 or self.max_order_notional <= 0:
            raise PaperTradingError("initial_cash and max_order_notional must be positive")
        if not Decimal("0") <= self.fee_bps <= Decimal("10000"):
            raise PaperTradingError("fee_bps must be between 0 and 10000")
        if not Decimal("0") <= self.slippage_bps <= Decimal("10000"):
            raise PaperTradingError("slippage_bps must be between 0 and 10000")
        if not Decimal("0") <= self.max_daily_loss_percent < Decimal("100"):
            raise PaperTradingError("max_daily_loss_percent must be in [0, 100)")
        with self._connect() as db:
            db.execute("CREATE TABLE IF NOT EXISTS account (id INTEGER PRIMARY KEY CHECK(id=1), cash TEXT NOT NULL)")
            db.execute("""CREATE TABLE IF NOT EXISTS positions (
                symbol TEXT PRIMARY KEY, units TEXT NOT NULL, avg_cost TEXT NOT NULL, last_price TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS daily_baselines (
                day TEXT PRIMARY KEY, start_equity TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS fills (
                event_id TEXT PRIMARY KEY, timestamp TEXT NOT NULL, symbol TEXT NOT NULL, side TEXT NOT NULL,
                quantity TEXT NOT NULL, reference_price TEXT NOT NULL, fill_price TEXT NOT NULL,
                fee TEXT NOT NULL, cash_after TEXT NOT NULL, result_json TEXT NOT NULL)""")
            db.execute("CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            configured = {
                "initial_cash": format(self.initial_cash.normalize(), "f"),
                "fee_bps": format(self.fee_bps.normalize(), "f"),
                "slippage_bps": format(self.slippage_bps.normalize(), "f"),
                "max_order_notional": format(self.max_order_notional.normalize(), "f"),
                "max_daily_loss_percent": format(self.max_daily_loss_percent.normalize(), "f"),
            }
            for key, value in configured.items():
                saved = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
                if saved is not None and saved[0] != value:
                    raise PaperTradingError(
                        f"paper ledger configuration mismatch for {key}; use the original settings or a fresh database"
                    )
                db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)", (key, value))
            db.execute("INSERT OR IGNORE INTO account(id,cash) VALUES(1,?)", (str(self.initial_cash),))

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.db_path, timeout=10, isolation_level=None)
        db.execute("PRAGMA busy_timeout=10000")
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _equity(self, db: sqlite3.Connection) -> Decimal:
        cash = Decimal(db.execute("SELECT cash FROM account WHERE id=1").fetchone()[0])
        inventory = db.execute("SELECT units,last_price FROM positions").fetchall()
        return cash + sum((Decimal(units) * Decimal(price) for units, price in inventory), Decimal("0"))

    def snapshot(self) -> dict[str, Any]:
        with self._connect() as db:
            cash = Decimal(db.execute("SELECT cash FROM account WHERE id=1").fetchone()[0])
            positions = {
                symbol: {"units": units, "average_cost": avg_cost, "last_price": last_price}
                for symbol, units, avg_cost, last_price in db.execute(
                    "SELECT symbol,units,avg_cost,last_price FROM positions ORDER BY symbol"
                ).fetchall()
                if Decimal(units) > 0
            }
            equity = cash + sum(
                (Decimal(item["units"]) * Decimal(item["last_price"]) for item in positions.values()),
                Decimal("0"),
            )
        return {"mode": "paper", "cash": str(cash), "equity_marked": str(equity),
                "positions": positions, "live_trading_enabled": False, "order_submission_attempted": False}

    def execute_market_order(
        self, *, event_id: str, timestamp: str, symbol: str, side: str,
        quantity: Any, reference_price: Any,
    ) -> dict[str, Any]:
        event_id = event_id.strip()
        symbol = symbol.strip().upper()
        side = side.strip().lower()
        if not event_id or not symbol or side not in {"buy", "sell"}:
            raise PaperTradingError("event_id, symbol, and side=buy|sell are required")
        try:
            parsed_timestamp = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
            if parsed_timestamp.tzinfo is None or parsed_timestamp.utcoffset() is None:
                raise ValueError("timezone is required")
            day = parsed_timestamp.date().isoformat()
        except (ValueError, TypeError, AttributeError) as exc:
            raise PaperTradingError("timestamp must be timezone-aware ISO-8601") from exc
        qty = _decimal(quantity, "quantity")
        reference = _decimal(reference_price, "reference_price")
        if qty <= 0 or reference <= 0:
            raise PaperTradingError("quantity and reference_price must be positive")
        reference_notional = qty * reference
        if reference_notional > self.max_order_notional:
            raise PaperTradingError("order exceeds max_order_notional")

        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                existing = db.execute(
                    "SELECT timestamp,symbol,side,quantity,reference_price,result_json FROM fills WHERE event_id=?",
                    (event_id,),
                ).fetchone()
                if existing:
                    identity = (existing[0], existing[1], existing[2], existing[3], existing[4])
                    requested = (timestamp, symbol, side, str(qty), str(reference))
                    if identity != requested:
                        raise PaperTradingError("event_id already exists with different order details")
                    db.execute("COMMIT")
                    return json.loads(existing[5])

                db.execute("INSERT OR IGNORE INTO positions(symbol,units,avg_cost,last_price) VALUES(?,?,?,?)",
                           (symbol, "0", "0", str(reference)))
                # On a new day, capture equity using the prior persisted marks before
                # applying today's price observation; otherwise the first mark could
                # hide an overnight/daily loss.
                baseline = db.execute("SELECT start_equity FROM daily_baselines WHERE day=?", (day,)).fetchone()
                if baseline is None:
                    start_equity = self._equity(db)
                    db.execute("INSERT INTO daily_baselines(day,start_equity) VALUES(?,?)", (day, str(start_equity)))
                else:
                    start_equity = Decimal(baseline[0])
                db.execute("UPDATE positions SET last_price=? WHERE symbol=?", (str(reference), symbol))
                equity = self._equity(db)
                loss_limit = start_equity * self.max_daily_loss_percent / Decimal("100")
                if start_equity - equity >= loss_limit:
                    # A rejected order is still a valid market-price observation: keep
                    # the mark so retries cannot evade the daily-loss guard by rollback.
                    db.execute("COMMIT")
                    raise PaperTradingError("max daily loss limit reached")

                cash = Decimal(db.execute("SELECT cash FROM account WHERE id=1").fetchone()[0])
                row = db.execute("SELECT units,avg_cost FROM positions WHERE symbol=?", (symbol,)).fetchone()
                units, avg_cost = Decimal(row[0]), Decimal(row[1])
                slip = self.slippage_bps / Decimal("10000")
                fill_price = reference * (Decimal("1") + slip if side == "buy" else Decimal("1") - slip)
                notional = qty * fill_price
                fee = notional * self.fee_bps / Decimal("10000")
                if side == "buy":
                    total = notional + fee
                    if total > cash:
                        raise PaperTradingError("insufficient virtual cash")
                    new_cash = cash - total
                    new_units = units + qty
                    new_avg = ((units * avg_cost) + total) / new_units
                else:
                    if qty > units:
                        raise PaperTradingError("insufficient virtual position")
                    new_cash = cash + notional - fee
                    new_units = units - qty
                    new_avg = avg_cost if new_units > 0 else Decimal("0")

                db.execute("UPDATE account SET cash=? WHERE id=1", (str(new_cash),))
                db.execute("UPDATE positions SET units=?,avg_cost=?,last_price=? WHERE symbol=?",
                           (str(new_units), str(new_avg), str(reference), symbol))
                result = {
                    "mode": "paper", "event_id": event_id, "timestamp": timestamp, "symbol": symbol,
                    "side": side, "quantity": str(qty), "reference_price": str(reference),
                    "fill_price": str(fill_price), "fee": str(fee), "cash_after": str(new_cash),
                    "equity_marked_after": str(self._equity(db)), "live_trading_enabled": False,
                    "order_submission_attempted": False,
                }
                db.execute("""INSERT INTO fills(event_id,timestamp,symbol,side,quantity,reference_price,
                    fill_price,fee,cash_after,result_json) VALUES(?,?,?,?,?,?,?,?,?,?)""",
                    (event_id, timestamp, symbol, side, str(qty), str(reference), str(fill_price),
                     str(fee), str(new_cash), json.dumps(result, separators=(",", ":"))))
                db.execute("COMMIT")
                return result
            except Exception:
                if db.in_transaction:
                    db.execute("ROLLBACK")
                raise
