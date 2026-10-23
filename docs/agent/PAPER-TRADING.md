# Offline Paper Trading Broker

`wallex_agent.paper_trading.PaperBroker` is a local, virtual Spot ledger. It does not make HTTP requests, read balances, use API keys, or submit exchange orders. It is separate from both the shadow runner and the live MCP server.

## Example

```python
from wallex_agent.paper_trading import PaperBroker

broker = PaperBroker(
    "var/paper/paper.sqlite3",
    initial_cash="1000000",
    fee_bps="10",                 # illustrative only: 0.10% per side
    slippage_bps="20",            # illustrative only: 0.20% per side
    max_order_notional="100000",
    max_daily_loss_percent="3",
)
fill = broker.execute_market_order(
    event_id="candle-BTC_USDT-2026-10-23T10:00:00Z-buy",
    timestamp="2026-10-23T10:00:00Z",
    symbol="BTC_USDT",
    side="buy",
    quantity="0.001",
    reference_price="100000",
)
print(fill)
print(broker.snapshot())
```

Use a deterministic, unique `event_id` for each intended simulated order. Retrying the same ID returns the original result and does not apply a second fill. SQLite persists virtual cash, positions and fills across process restarts.

## Simulator behavior

- Applies adverse slippage to the reference price and fees to simulated notional.
- Rejects non-positive quantities/prices, orders over the notional cap, buys exceeding virtual cash, and sells exceeding virtual inventory.
- Maintains a per-day marked-equity baseline and rejects orders when the configured daily-loss limit has been reached.
- Reports marked equity and explicit `live_trading_enabled: false` / `order_submission_attempted: false` fields.
- Uses decimal arithmetic for money/quantity calculations.

## Important limitations

This is a deterministic research simulator, not a market-data service or complete trading system. The caller must provide timestamps, symbols, quantities and reference prices. It does not implement candle-based signal generation, automatic mark-to-market for all symbols, partial fills, order-book depth, queue priority, taxes, exchange-specific fee tiers, portfolio allocation, or reconciliation with Wallex. Daily loss checks use the stored position marks and the order's supplied reference price. Do not treat illustrative fee/slippage settings as official Wallex rates. No profitability is implied.

## JSONL command-line mode

The optional `wallex-paper` command accepts explicit simulated orders in a local JSONL file. Every non-empty line must be a JSON object with `event_id`, timezone-aware ISO-8601 `timestamp`, `symbol`, `side` (`buy` or `sell`), `quantity`, and `reference_price`.

Example input:

```json
{"event_id":"demo-1","timestamp":"2026-10-23T10:00:00Z","symbol":"BTC_USDT","side":"buy","quantity":"0.001","reference_price":"100000"}
```

Run:

```sh
wallex-paper --input events.jsonl --db var/paper/paper.sqlite3 \
  --initial-cash 1000000 --max-order-notional 100000 \
  --fee-bps 10 --slippage-bps 20 --max-daily-loss-percent 3
```

All amounts and fee assumptions above are examples only. The ledger persists across runs; use a fresh database path for an independent experiment. This CLI replays only explicit order events: it does not derive strategy signals from candles or subscribe to market data.

## Candle-driven strategy simulation

The `wallex-paper-candles` command runs a simple long-only momentum rule on a local chronological OHLCV JSONL dataset and writes simulated fills to the persistent virtual ledger. It uses prior candle closes for signals and the next candle's open as the simulated execution reference.

```sh
wallex-paper-candles --input candles.jsonl --symbol BTC_USDT \
  --db var/paper/btc-paper.sqlite3 --initial-cash 1000000 \
  --max-order-notional 100000 --fee-bps 10 --slippage-bps 20 \
  --lookback-bars 5 --entry-return-bps 20 --exit-return-bps 0 \
  --max-daily-loss-percent 3 --output var/paper/report.json
```

The input should contain at least `lookback-bars + 2` valid, strictly chronological candles with `timestamp`, `open`, `high`, `low`, `close`, and `volume`. If rows include `symbol`, it must match `--symbol`. Use a fresh database for an independent run; a persistent ledger rejects changes to its original cash/cost/risk settings. The strategy is a small baseline for testing the paper pipeline, not a recommendation or evidence of profitability.

### Optional mandatory data-quality gate

For a safer run, add `--audit-input-data --expected-interval-seconds 60` (replace 60 with the dataset's actual interval). The simulator blocks `INVALID` data. A `REVIEW` report (for example, possible timestamp gaps or missing metadata) blocks by default; only after inspecting the audit report may an operator explicitly pass `--allow-review-data`. The output report records the audit summary and whether the review override was used.

```sh
wallex-paper-candles --input candles.jsonl --symbol BTC_USDT \
  --db var/paper/btc-paper.sqlite3 --initial-cash 1000000 \
  --max-order-notional 100000 --fee-bps 10 --slippage-bps 20 \
  --lookback-bars 5 --entry-return-bps 20 --exit-return-bps 0 \
  --max-daily-loss-percent 3 --audit-input-data \
  --expected-interval-seconds 60 --output var/paper/report.json
```

The audit is local-only and does not prove that the public feed is complete or that a strategy is profitable.
