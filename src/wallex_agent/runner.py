"""Standalone periodic shadow runner. No account reads and no order writes."""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence
from wallex_mcp.wallex_client import WallexClient
from .engine import ScreenConfig, assess_markets

class MarketReader(Protocol):
    def get_markets(self) -> Any: ...

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def _rows(response: Any) -> list[dict[str, Any]]:
    if hasattr(response, "markets"):
        return [row.model_dump(mode="json") if hasattr(row, "model_dump") else dict(row) for row in response.markets]
    if isinstance(response, dict):
        rows = response.get("markets")
        if rows is None and isinstance(response.get("result"), dict):
            rows = response["result"].get("markets")
        if isinstance(rows, list):
            return [row for row in rows if isinstance(row, dict)]
    raise ValueError("markets response did not contain a markets array")

def run_shadow(client: MarketReader, config: ScreenConfig, output_path: str | Path, *,
               interval_seconds: float = 60, max_cycles: int = 0,
               sleep: Callable[[float], None] = time.sleep,
               clock: Callable[[], str] = utc_now,
               on_cycle: Callable[[dict[str, Any]], None] | None = None) -> int:
    """Run one or more public-data cycles and append a JSONL audit trail."""
    if not 1 <= interval_seconds <= 3600:
        raise ValueError("interval_seconds must be between 1 and 3600")
    if max_cycles < 0:
        raise ValueError("max_cycles cannot be negative")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    cycles = 0
    while max_cycles == 0 or cycles < max_cycles:
        try:
            rows = _rows(client.get_markets())
            assessed = assess_markets(rows, config)
            payload = {"timestamp_utc": clock(), "mode": "shadow",
                "strategy_id": "positive-change-tight-spread-screen-v1",
                "markets_seen": len(rows), "watch_candidates": sum(x.eligible for x in assessed),
                "assessments": [x.as_dict() for x in assessed], "order_submission_attempted": False}
        except Exception as exc:
            payload = {"timestamp_utc": clock(), "mode": "shadow", "cycle_status": "error",
                       "error_type": type(exc).__name__, "order_submission_attempted": False}
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n")
        if on_cycle:
            on_cycle(payload)
        cycles += 1
        if max_cycles == 0 or cycles < max_cycles:
            sleep(interval_seconds)
    return cycles

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="wallex-agent", description="Independent Wallex market screen; shadow mode only.")
    parser.add_argument("--quote-asset", default=os.getenv("WALLEX_AGENT_QUOTE_ASSET", ""))
    parser.add_argument("--interval-seconds", type=float, default=60)
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--output", default="var/wallex-agent/shadow.jsonl")
    parser.add_argument("--minimum-change-24h-raw", default="0")
    parser.add_argument("--maximum-spread-bps", default="80")
    parser.add_argument("--symbols", default="", help="Optional comma-separated exact symbol allowlist")
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.quote_asset.strip():
        print("error: pass --quote-asset or set WALLEX_AGENT_QUOTE_ASSET", file=sys.stderr)
        return 2
    try:
        config = ScreenConfig(args.quote_asset, args.minimum_change_24h_raw, args.maximum_spread_bps,
            frozenset(part.strip().upper() for part in args.symbols.split(",") if part.strip()))
        if not 1 <= args.interval_seconds <= 3600:
            raise ValueError("interval-seconds must be between 1 and 3600")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    def emit(payload: dict[str, Any]) -> None:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), flush=True)
    try:
        run_shadow(WallexClient(), config, args.output, interval_seconds=args.interval_seconds,
                   max_cycles=1 if args.once else 0, on_cycle=emit)
    except KeyboardInterrupt:
        print("shadow runner interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: runner failed ({type(exc).__name__})", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
