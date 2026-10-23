# Independent Wallex Agent — Phase 1 Shadow Runner

The repository now has an independent, standalone market-screening loop. It runs without Smart98 and only reads public market metadata. It never places, changes, or cancels orders.

## Install and run

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install -e ".[test]"
    wallex-agent --quote-asset USDT --once

Replace USDT only with a verified quote asset relevant to the contest. It is an illustrative example, not a recommendation. Omit --once for continuous polling. Default interval is 60 seconds, bounded to 1–3600 seconds. No API key is needed because this phase reads public market metadata only.

Set WALLEX_AGENT_QUOTE_ASSET to supply the quote asset via environment. Use --output PATH to choose the append-only JSONL audit path, --symbols BTCUSDT,ETHUSDT for an optional exact symbol filter, --maximum-spread-bps 80 for the spread threshold, and --minimum-change-24h-raw 0 for a raw change_24h threshold. No assumed unit conversion is applied to change_24h.

## What the v1 screen does

It screens active Spot markets by configured quote asset and optional exact symbol allowlist; requires valid positive bid/ask and current price; filters spreads above the configured cap; and lists candidates whose raw change_24h exceeds the threshold. Output statuses are WATCH or SKIP, not BUY or SELL recommendations. It cannot call the live order client.

This is a deterministic screening baseline for instrumentation, not an established profitable strategy. It does not yet use depth snapshots, candles, WebSocket streams, actual account fees, slippage, order-book liquidity, contest rules, or portfolio state. Public market metadata alone is not an executable quote; do not use this watchlist alone to authorize a live order.

## Runtime behavior

- Smart98 is not a runtime dependency.
- Only the public GET /hector/web/v1/markets path is used through the fixed-host Wallex read client.
- Each cycle appends an audit record. Failures are recorded by exception type only.
- Ctrl-C ends continuous shadow mode.
- No API key, balances, order creation, cancellation, or transfer endpoints are used.

## Next gates

Before any live strategy, add verified time-series/depth/trade data, an evidence-backed fee model, historical replay and walk-forward tests, a paper portfolio and fill reconciliation, data-staleness/liquidity checks, drawdown and daily-loss limits connected to the runner, restart recovery, and separately reviewed integration tests. Existing live MCP tools are not wired into this runner.
