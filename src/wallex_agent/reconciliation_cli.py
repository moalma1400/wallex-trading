"""Offline CLI: reconcile local Wallex candles against CoinGecko references.

Reads only local files. To obtain a CoinGecko ``/simple/price`` payload file
in an authorized environment, use the repository's read-only CoinGecko MCP
server or client; this CLI itself never uses the network or any API key.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

from .provider_reconciliation import (
    ReconciliationError,
    coingecko_observations_from_price_payload,
    coingecko_observations_from_rows,
    reconcile,
    wallex_observations_from_candles,
)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ReconciliationError(f"invalid JSON on line {line_no} of {path}") from exc
        if not isinstance(row, dict):
            raise ReconciliationError(f"line {line_no} of {path} must be a JSON object")
        rows.append(row)
    return rows


def _parse_base_by_id(raw: str | None) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for part in (raw or "").split(","):
        part = part.strip()
        if not part:
            continue
        if "=" not in part:
            raise ReconciliationError("--base-by-id entries must look like bitcoin=BTC")
        coin_id, base = part.split("=", 1)
        mapping[coin_id.strip()] = base.strip().upper()
    return mapping


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="wallex-reconcile",
        description="Compare local Wallex candle closes with supplied CoinGecko reference prices; offline only.",
    )
    parser.add_argument("--wallex-candles", required=True, help="Wallex candle JSONL (e.g. recorder output)")
    parser.add_argument("--symbol", required=True, help="Wallex symbol for the candle file, e.g. BTCUSDT")
    parser.add_argument("--interval-seconds", type=int, required=True, help="Candle interval; closes are known at bucket end")
    parser.add_argument("--coingecko-file", required=True,
                        help="CoinGecko /simple/price JSON payload file, or normalized reference JSONL")
    parser.add_argument("--base-by-id", help="For payload files: coin-id=BASE pairs, e.g. bitcoin=BTC,ethereum=ETH")
    parser.add_argument("--fetched-at", help="Fallback observation time (ISO-8601) when a payload lacks last_updated_at")
    parser.add_argument("--max-deviation-bps", required=True, help="Caller-selected material-deviation threshold")
    parser.add_argument("--max-staleness-seconds", type=int, required=True, help="Caller-selected reference staleness limit")
    parser.add_argument("--allow-quote-mismatch", action="store_true",
                        help="Compare across different quote currencies, flagged; never converted")
    parser.add_argument("--output", help="Optional JSON report path; defaults to stdout")
    args = parser.parse_args(argv)
    try:
        wallex = wallex_observations_from_candles(
            _load_jsonl(Path(args.wallex_candles)),
            symbol=args.symbol, interval_seconds=args.interval_seconds,
            source=f"wallex_candle_close:{args.wallex_candles}",
        )
        cg_path = Path(args.coingecko_file)
        cg_text = cg_path.read_text(encoding="utf-8").strip()
        payload: Any = None
        if cg_text.startswith("{"):
            try:
                payload = json.loads(cg_text)
            except json.JSONDecodeError:
                payload = None
        if isinstance(payload, dict) and payload and not any(
            key in payload for key in ("price", "timestamp", "base", "quote", "open", "close")
        ):
            base_by_id = _parse_base_by_id(args.base_by_id)
            if not base_by_id:
                raise ReconciliationError("--base-by-id is required for a CoinGecko price-payload file")
            if not args.fetched_at and not any(
                isinstance(v, dict) and "last_updated_at" in v for v in payload.values()
            ):
                raise ReconciliationError("--fetched-at is required when the payload has no last_updated_at")
            coingecko = coingecko_observations_from_price_payload(
                payload, base_by_id=base_by_id,
                fetched_at=args.fetched_at or "1970-01-01T00:00:00Z",
                source=f"coingecko_simple_price:{args.coingecko_file}",
            )
        else:
            coingecko = coingecko_observations_from_rows(
                _load_jsonl(cg_path), source=f"coingecko_reference:{args.coingecko_file}",
            )
        report = reconcile(
            wallex, coingecko,
            max_deviation_bps=args.max_deviation_bps,
            max_staleness_seconds=args.max_staleness_seconds,
            allow_quote_mismatch=args.allow_quote_mismatch,
        )
        report["input_files"] = {"wallex_candles": args.wallex_candles, "coingecko": args.coingecko_file}
        encoded = json.dumps(report, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            target = Path(args.output)
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(encoded, encoding="utf-8")
        else:
            print(encoded, end="")
        return 0 if report["status"] == "OK" else 1
    except (OSError, ValueError, ReconciliationError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
