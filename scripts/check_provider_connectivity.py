#!/usr/bin/env python3
"""Manual, read-only Wallex + CoinGecko connectivity check.

This script is NEVER run by offline CI or the paper-trading workflow. Run it
only in an owner-authorized environment (locally, or via the manually
dispatched ``Provider read-only check`` GitHub Actions workflow on the
default branch).

Safety properties:
- Wallex: only the allowlisted public ``GET /hector/web/v1/markets`` route
  is called, through the repository client constructed *without* an API
  key. ``WALLEX_API_KEY`` presence is reported as a boolean only; the key is
  not sent to the public endpoint and no account endpoint is called.
- CoinGecko: only documented read-only Demo endpoints (``GET /ping`` and
  ``GET /simple/price``) via the repository client, which reads
  ``COINGECKO_DEMO_API_KEY`` and sends it only in the ``x-cg-demo-api-key``
  header.
- Output contains statuses, counts, and timestamps only: no secret values,
  no response bodies, no account data. No order, cancellation, transfer,
  deposit, or withdrawal capability exists in either client path used here.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from coingecko_mcp.client import CoinGeckoClient, CoinGeckoError  # noqa: E402
from wallex_mcp.config import MARKETS_PATH, WALLEX_OFFICIAL_HOST  # noqa: E402
from wallex_mcp.wallex_client import WallexClient, WallexClientError  # noqa: E402


def _now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def config_report() -> dict:
    coingecko = CoinGeckoClient()
    return {
        "checked_at_utc": _now(),
        "mode": "config_only_no_network",
        "wallex": {
            "public_endpoint": f"GET https://{WALLEX_OFFICIAL_HOST}{MARKETS_PATH}",
            "WALLEX_API_KEY_configured": bool(os.getenv("WALLEX_API_KEY", "").strip()),
            "note": "key is not required for, and is never sent to, the public markets endpoint",
        },
        "coingecko": {
            "base_url": coingecko.base_url,
            "COINGECKO_DEMO_API_KEY_configured": coingecko.api_key_configured,
        },
        "live_trading_enabled": False,
        "order_submission_attempted": False,
    }


def live_report() -> tuple[dict, bool]:
    report = config_report()
    report["mode"] = "read_only_connectivity_check"
    ok = True

    try:
        markets = WallexClient().get_markets()  # no api_key: public route only
        report["wallex"]["public_markets"] = {
            "status": "ok", "market_count": len(markets.markets),
        }
    except (WallexClientError, ValueError) as exc:
        ok = False
        report["wallex"]["public_markets"] = {
            "status": "error", "error_type": type(exc).__name__,
        }

    try:
        client = CoinGeckoClient()
        ping = client.ping()
        price = client.get_price("bitcoin", "usd")
        bitcoin = price.get("bitcoin") if isinstance(price, dict) else None
        report["coingecko"]["ping"] = {"status": "ok", **ping}
        report["coingecko"]["simple_price_bitcoin_usd"] = {
            "status": "ok" if isinstance(bitcoin, dict) and "usd" in bitcoin else "unexpected_payload",
            "last_updated_at": bitcoin.get("last_updated_at") if isinstance(bitcoin, dict) else None,
        }
        if report["coingecko"]["simple_price_bitcoin_usd"]["status"] != "ok":
            ok = False
    except (CoinGeckoError, ValueError) as exc:
        ok = False
        report["coingecko"]["ping"] = {
            "status": "error", "error_type": type(exc).__name__, "error": str(exc),
        }
    report["checked_at_utc"] = _now()
    return report, ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--config-only", action="store_true",
        help="Report which secret env names are configured (booleans only); make no network calls",
    )
    args = parser.parse_args()
    if args.config_only:
        print(json.dumps(config_report(), indent=2))
        return 0
    report, ok = live_report()
    print(json.dumps(report, indent=2))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
