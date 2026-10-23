"""Standalone periodic shadow runner. No account reads and no order writes."""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Callable, Protocol, Sequence
from wallex_mcp.wallex_client import WallexClient
from .cost_model import CostModelConfig, evaluate_momentum
from .engine import ScreenConfig, assess_markets
from .state import ObservationStore
from .opportunity_ranker import rank_cost_adjusted_opportunities

class MarketReader(Protocol):
    def get_markets(self) -> Any: ...

def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")

def _parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("clock must return an ISO-8601 timestamp with timezone")
    return parsed.astimezone(timezone.utc)

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

def _positive_price(value: Any) -> bool:
    try:
        parsed = Decimal(str(value))
        return parsed.is_finite() and parsed > 0
    except (InvalidOperation, ValueError):
        return False

def _add_cost_assessments(rows: list[dict[str, Any]], assessments: list[Any],
                          store: ObservationStore, now: str,
                          cost_config: CostModelConfig | None) -> list[dict[str, Any]]:
    timestamp = _parse_time(now)
    market_by_symbol = {str(row.get("symbol", "")).upper(): row for row in rows if row.get("symbol")}
    result = []
    for assessment in assessments:
        item = assessment.as_dict()
        market = market_by_symbol.get(assessment.symbol, {})
        fair = market.get("fair_price") if isinstance(market.get("fair_price"), dict) else {}
        current_price = market.get("price")
        if cost_config is None:
            item["cost_adjusted_momentum"] = {"status": "COST_MODEL_DISABLED"}
        elif not assessment.eligible:
            item["cost_adjusted_momentum"] = {"status": "SCREEN_FILTERED"}
        elif not _positive_price(current_price) or not _positive_price(fair.get("bid")) or not _positive_price(fair.get("ask")):
            item["cost_adjusted_momentum"] = {"status": "INVALID_DATA"}
        else:
            previous = store.get(assessment.symbol)
            if previous is None:
                item["cost_adjusted_momentum"] = {"status": "WARMUP_NO_BASELINE"}
            else:
                previous_price, previous_at = previous
                try:
                    elapsed = int((timestamp - _parse_time(previous_at)).total_seconds())
                    item["cost_adjusted_momentum"] = evaluate_momentum(
                        previous_price=previous_price, current_price=current_price,
                        bid=fair["bid"], ask=fair["ask"], elapsed_seconds=elapsed,
                        config=cost_config)
                except (ValueError, TypeError, OverflowError):
                    item["cost_adjusted_momentum"] = {"status": "INVALID_TIMESTAMP"}
        # Persist only positive numeric prices, after evaluating against prior data.
        if _positive_price(current_price):
            store.put(assessment.symbol, current_price, now)
        result.append(item)
    return result

def run_shadow(client: MarketReader, config: ScreenConfig, output_path: str | Path, *,
               interval_seconds: float = 60, max_cycles: int = 0,
               sleep: Callable[[float], None] = time.sleep,
               clock: Callable[[], str] = utc_now,
               on_cycle: Callable[[dict[str, Any]], None] | None = None,
               cost_config: CostModelConfig | None = None,
               state_path: str | Path | None = None) -> int:
    """Run public-data cycles, append audit records and optionally assess net edge."""
    if not 1 <= interval_seconds <= 3600:
        raise ValueError("interval_seconds must be between 1 and 3600")
    if max_cycles < 0:
        raise ValueError("max_cycles cannot be negative")
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    store = ObservationStore(state_path or path.with_name(path.stem + "-state.sqlite3"))
    cycles = 0
    while max_cycles == 0 or cycles < max_cycles:
        timestamp = clock()
        try:
            rows = _rows(client.get_markets())
            assessed = assess_markets(rows, config)
            output_assessments = _add_cost_assessments(rows, assessed, store, timestamp, cost_config)
            payload = {"timestamp_utc": timestamp, "mode": "shadow",
                "strategy_id": "positive-change-tight-spread-screen-v1",
                "cost_model_enabled": cost_config is not None,
                "markets_seen": len(rows),
                "watch_candidates": sum(x.eligible for x in assessed),
                "cost_edge_candidates": sum(x.get("cost_adjusted_momentum", {}).get("status") == "WATCH_EDGE" for x in output_assessments),
                "assessments": output_assessments,
                "ranked_opportunities": rank_cost_adjusted_opportunities(output_assessments),
                "live_trading_enabled": False, "order_submission_attempted": False}
        except Exception as exc:
            payload = {"timestamp_utc": timestamp, "mode": "shadow", "cycle_status": "error",
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
    parser.add_argument("--state-db", default="var/wallex-agent/observations.sqlite3")
    parser.add_argument("--minimum-change-24h-raw", default="0")
    parser.add_argument("--maximum-spread-bps", default="80")
    parser.add_argument("--symbols", default="", help="Optional comma-separated exact symbol allowlist")
    parser.add_argument("--fee-bps-per-side", default=os.getenv("WALLEX_AGENT_FEE_BPS_PER_SIDE"),
                        help="Explicit fee assumption per side; no default is inferred")
    parser.add_argument("--slippage-bps-per-side", default=os.getenv("WALLEX_AGENT_SLIPPAGE_BPS_PER_SIDE"),
                        help="Explicit slippage reserve per side; no default is inferred")
    parser.add_argument("--minimum-net-edge-bps", default="0")
    parser.add_argument("--maximum-observation-gap-seconds", type=int, default=180)
    return parser

def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not args.quote_asset.strip():
        print("error: pass --quote-asset or set WALLEX_AGENT_QUOTE_ASSET", file=sys.stderr)
        return 2
    if (args.fee_bps_per_side is None) != (args.slippage_bps_per_side is None):
        print("error: fee and slippage assumptions must both be supplied, or both omitted", file=sys.stderr)
        return 2
    try:
        config = ScreenConfig(args.quote_asset, args.minimum_change_24h_raw, args.maximum_spread_bps,
            frozenset(part.strip().upper() for part in args.symbols.split(",") if part.strip()))
        cost_config = None
        if args.fee_bps_per_side is not None:
            cost_config = CostModelConfig(args.fee_bps_per_side, args.slippage_bps_per_side,
                args.minimum_net_edge_bps, args.maximum_observation_gap_seconds)
        if not 1 <= args.interval_seconds <= 3600:
            raise ValueError("interval-seconds must be between 1 and 3600")
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    def emit(payload: dict[str, Any]) -> None:
        print(json.dumps(payload, ensure_ascii=False, separators=(",", ":")), flush=True)
    try:
        run_shadow(WallexClient(), config, args.output, interval_seconds=args.interval_seconds,
                   max_cycles=1 if args.once else 0, on_cycle=emit,
                   cost_config=cost_config, state_path=args.state_db)
    except KeyboardInterrupt:
        print("shadow runner interrupted", file=sys.stderr)
        return 130
    except Exception as exc:
        print(f"error: runner failed ({type(exc).__name__})", file=sys.stderr)
        return 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
