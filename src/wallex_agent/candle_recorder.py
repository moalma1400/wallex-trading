"""Record Wallex public trade WebSocket messages as local OHLCV candles."""
from __future__ import annotations
import argparse
import asyncio
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, AsyncIterator, Callable, Sequence

WALLEX_WS_URL = "wss://api.wallex.ir/ws"
TRADE_DOC_URL = "https://developers.wallex.ir/socket/trade"

def _decimal(value: Any, field: str) -> Decimal:
    if isinstance(value, bool):
        raise ValueError(f"{field} must be a finite decimal")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(f"{field} must be a finite decimal") from exc
    if not result.is_finite():
        raise ValueError(f"{field} must be a finite decimal")
    return result

def parse_trade_message(message: str | bytes, symbol: str) -> tuple[datetime, Decimal, Decimal] | None:
    """Parse only the documented [SYMBOL@trade, {price, quantity, timestamp}] envelope."""
    if isinstance(message, bytes):
        message = message.decode("utf-8")
    try:
        payload = json.loads(message)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    # Handle documented/application keepalive control messages without treating them as trades.
    if payload == "PING" or payload == ["PING"]:
        return None
    if not isinstance(payload, list) or len(payload) != 2 or payload[0] != f"{symbol}@trade" or not isinstance(payload[1], dict):
        return None
    trade = payload[1]
    try:
        price = _decimal(trade.get("price"), "price")
        quantity = _decimal(trade.get("quantity"), "quantity")
        stamp = trade.get("timestamp")
        if not isinstance(stamp, str):
            return None
        parsed = datetime.fromisoformat(stamp.replace("Z", "+00:00"))
        if parsed.tzinfo is None or parsed.utcoffset() is None:
            return None
        parsed = parsed.astimezone(timezone.utc)
        if price <= 0 or quantity <= 0:
            return None
        return parsed, price, quantity
    except (ValueError, TypeError, OverflowError):
        return None

@dataclass(slots=True)
class CandleAccumulator:
    start: datetime
    interval_seconds: int
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    trade_count: int = 1

    @classmethod
    def from_trade(cls, timestamp: datetime, price: Decimal, quantity: Decimal, interval_seconds: int) -> "CandleAccumulator":
        epoch = int(timestamp.timestamp())
        bucket = datetime.fromtimestamp(epoch - epoch % interval_seconds, timezone.utc)
        return cls(bucket, interval_seconds, price, price, price, price, quantity, 1)

    def add(self, price: Decimal, quantity: Decimal) -> None:
        self.high = max(self.high, price)
        self.low = min(self.low, price)
        self.close = price
        self.volume += quantity
        self.trade_count += 1

    def as_dict(self, symbol: str) -> dict[str, Any]:
        return {"timestamp": self.start.isoformat().replace("+00:00", "Z"),
                "open": str(self.open), "high": str(self.high), "low": str(self.low),
                "close": str(self.close), "volume": str(self.volume), "symbol": symbol,
                "interval_seconds": self.interval_seconds, "trade_count": self.trade_count,
                "source": "wallex_public_trade_websocket", "source_url": TRADE_DOC_URL}

class CandleWriter:
    """Append closed candles and maintain a minimal source/freshness manifest."""
    def __init__(self, output: str | Path, symbol: str, interval_seconds: int) -> None:
        self.output = Path(output)
        self.output.parent.mkdir(parents=True, exist_ok=True)
        self.symbol = symbol
        self.interval_seconds = interval_seconds
        self.manifest_path = self.output.with_suffix(self.output.suffix + ".manifest.json")
        self.started_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        self.written = 0
        self.malformed = 0
        self.last_candle: str | None = None
        self._write_manifest("recording")

    def write_candle(self, candle: CandleAccumulator) -> None:
        record = candle.as_dict(self.symbol)
        with self.output.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, separators=(",", ":")) + "\n")
        self.written += 1
        self.last_candle = record["timestamp"]
        self._write_manifest("recording")

    def _write_manifest(self, status: str) -> None:
        manifest = {"schema_version": 1, "symbol": self.symbol, "interval_seconds": self.interval_seconds,
                    "websocket_url": WALLEX_WS_URL, "documentation_url": TRADE_DOC_URL,
                    "started_at_utc": self.started_at,
                    "updated_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "status": status, "closed_candles_written_this_run": self.written,
                    "malformed_or_unmatched_messages": self.malformed, "last_closed_candle_utc": self.last_candle,
                    "gaps_possible_on_disconnect": True}
        self.manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

async def record_trades(symbol: str, interval_seconds: int, output: str | Path, *,
                        max_runtime_seconds: float = 0,
                        connector: Callable[..., Any] | None = None,
                        clock: Callable[[], float] | None = None) -> int:
    """Record live public trade feed. Intended for data collection, not order execution."""
    if not symbol or not symbol.isascii() or not symbol.replace("_", "").isalnum() or symbol.upper() != symbol:
        raise ValueError("symbol must be an uppercase alphanumeric Wallex market symbol")
    if not 1 <= interval_seconds <= 86400:
        raise ValueError("interval-seconds must be between 1 and 86400")
    if max_runtime_seconds < 0:
        raise ValueError("max-runtime-seconds cannot be negative")
    if connector is None:
        try:
            from websockets.asyncio.client import connect
        except ImportError as exc:
            raise RuntimeError("install project dependencies including websockets") from exc
        connector = connect
    import time
    now = clock or time.monotonic
    writer = CandleWriter(output, symbol, interval_seconds)
    active: CandleAccumulator | None = None
    deadline = now() + max_runtime_seconds if max_runtime_seconds else None
    try:
        async with connector(WALLEX_WS_URL, open_timeout=15, close_timeout=5, ping_interval=20, ping_timeout=20, max_size=1_000_000) as websocket:
            await websocket.send(json.dumps(["subscribe", {"channel": f"{symbol}@trade"}]))
            async for message in websocket:
                if deadline is not None and now() >= deadline:
                    break
                trade = parse_trade_message(message, symbol)
                if trade is None:
                    writer.malformed += 1
                    continue
                timestamp, price, quantity = trade
                next_candle = CandleAccumulator.from_trade(timestamp, price, quantity, interval_seconds)
                if active is None:
                    active = next_candle
                elif next_candle.start == active.start:
                    active.add(price, quantity)
                elif next_candle.start > active.start:
                    writer.write_candle(active)
                    active = next_candle
                else:
                    # Out-of-order old trade: do not rewrite a closed candle or contaminate current OHLCV.
                    writer.malformed += 1
        if active is not None:
            # Never emit an unfinished candle as if it were complete.
            pass
    finally:
        writer._write_manifest("stopped")
    return writer.written

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wallex-candle-recorder", description="Record public Wallex trade messages into local OHLCV JSONL; no trading.")
    parser.add_argument("--symbol", required=True, help="Exact uppercase Spot symbol, e.g. BTCUSDT")
    parser.add_argument("--interval-seconds", type=int, default=60)
    parser.add_argument("--output", default="data/candles.jsonl")
    parser.add_argument("--max-runtime-seconds", type=float, default=0, help="0 means run until interrupted")
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        count = asyncio.run(record_trades(args.symbol, args.interval_seconds, args.output, max_runtime_seconds=args.max_runtime_seconds))
        print(json.dumps({"closed_candles_written": count, "output": args.output, "trading_enabled": False}))
        return 0
    except KeyboardInterrupt:
        print("recorder interrupted; partial candle was not written", file=sys.stderr)
        return 130
    except (OSError, ValueError, RuntimeError) as exc:
        print(f"error: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
