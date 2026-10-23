# 20-Candle Offline Paper Mission (Wallex + CoinGecko)

A bounded, reproducible engineering check: audit 20 consecutive one-minute
candles, run the offline paper ledger over them, and reconcile the Wallex
closes against independent CoinGecko reference prices. It is a pipeline
verification, **not** a profitability test and not exchange-connected paper
trading. Nothing here places, changes, or cancels an order, reads an
account, or uses an API key.

## Provider roles

| Provider | Role in this workflow | Never used for |
| --- | --- | --- |
| Wallex | Exchange-specific candles from the public-trade candle recorder (`wallex-candle-recorder`, PR #23 Centrifugo v2 implementation); simulated fills reference these candles | Account reads here; the recorder and paper tools use no key |
| CoinGecko | Independent reference / market-context prices for reconciliation only | Simulated execution prices; prices are never averaged with Wallex |

CoinGecko Demo facts are implemented from the official documentation: root
URL `https://api.coingecko.com/api/v3/` with the recommended
`x-cg-demo-api-key` header [CG-DEMO-AUTH](https://docs.coingecko.com/demo/reference/authentication);
`GET /ping` server status [CG-PING](https://docs.coingecko.com/demo/reference/ping-server);
`GET /simple/price` with `include_last_updated_at` freshness timestamps
[CG-SIMPLE-PRICE](https://docs.coingecko.com/demo/reference/simple-price).
The key is read from the `COINGECKO_DEMO_API_KEY` environment variable by
`coingecko_mcp.client.CoinGeckoClient` and is never printed, logged, or
placed in a URL by this repository's client. The offline mission below does
not call CoinGecko at all; it consumes a previously saved payload/JSONL file
or the labeled synthetic fixture.

## Symbol conventions (normalize before comparing)

- Recorder/Wallex style: `BTCUSDT` (no separator). Paper docs also show
  `BTC_USDT`. `wallex_agent.provider_reconciliation.split_symbol` parses
  `BTCUSDT`, `BTC_USDT`, `BTC-USDT`, and `BTC/USDT` into `BTC` + `USDT`
  and refuses symbols it cannot parse instead of guessing.
- CoinGecko uses coin **IDs** (e.g. `bitcoin`) plus `vs_currencies`
  (e.g. `usdt`). The ID-to-base mapping is always caller-supplied
  (`--base-by-id bitcoin=BTC`); identically named assets on different
  venues are not assumed to be the same market.
- Quote currencies must match to compare (`USDT` vs `USD` returns
  `INCOMPARABLE_QUOTE` unless the caller explicitly passes
  `--allow-quote-mismatch`, which flags rather than converts).

## Inputs for the committed demonstration run

- `tests/fixtures/synthetic_20x1m_candles.jsonl` — 20 invented one-minute
  candles around price 100 labeled `synthetic_fixture_not_market_data` in
  every row. They are **not** BTC or Wallex data.
- `tests/fixtures/synthetic_coingecko_reference.jsonl` — 5 invented
  reference observations (+0.1% versus the corresponding synthetic closes),
  same labeling.
- Demonstration settings copied from [Paper Trading](PAPER-TRADING.md)
  examples (initial cash 1,000,000; max order notional 100,000; fee
  10 bps/side; slippage 20 bps/side; lookback 5; entry 20 bps; exit 0 bps;
  daily loss 3%) and reconciliation thresholds (500 bps deviation,
  600 seconds staleness). These are documentation examples for pipeline
  testing only, **not verified Wallex fees and not an owner-approved
  strategy configuration**. Real runs require the owner to supply market,
  capital, fee/slippage, and strategy parameters explicitly.

## Run it (offline)

```sh
python -m venv .venv && . .venv/bin/activate
python -m pip install -e ".[test]"

# 1. Audit first; exit 0 only on OK (see DATA-AUDIT.md for statuses).
wallex-data-audit --input tests/fixtures/synthetic_20x1m_candles.jsonl \
  --symbol BTCUSDT --interval-seconds 60 \
  --as-of 2026-01-01T00:20:00Z --max-staleness-seconds 600 \
  --output var/paper-mission/audit.json

# 2. Paper simulation with the audit gate enforced inside the CLI.
wallex-paper-candles --input tests/fixtures/synthetic_20x1m_candles.jsonl \
  --symbol BTCUSDT --db var/paper-mission/paper.sqlite3 \
  --initial-cash 1000000 --max-order-notional 100000 \
  --fee-bps 10 --slippage-bps 20 --lookback-bars 5 \
  --entry-return-bps 20 --exit-return-bps 0 --max-daily-loss-percent 3 \
  --audit-input-data --expected-interval-seconds 60 \
  --audit-as-of 2026-01-01T00:20:00Z --audit-max-staleness-seconds 600 \
  --output var/paper-mission/report.json

# 3. Reconcile Wallex closes against CoinGecko reference observations.
wallex-reconcile --wallex-candles tests/fixtures/synthetic_20x1m_candles.jsonl \
  --symbol BTCUSDT --interval-seconds 60 \
  --coingecko-file tests/fixtures/synthetic_coingecko_reference.jsonl \
  --max-deviation-bps 500 --max-staleness-seconds 600 \
  --output var/paper-mission/reconciliation.json
```

Use a fresh `--db` path for an independent run; the ledger locks itself to
its original settings. Outputs under `var/` are local-only and git-ignored.
For recorded data, replace the fixture with recorder output
(`wallex-candle-recorder --symbol <SYMBOL> --interval-seconds 60 ...` in an
authorized environment; see [Candle Recorder](CANDLE-RECORDER.md)), keep
its `.manifest.json` beside the JSONL so the audit can read it, and inspect
any `REVIEW` audit before considering `--allow-review-data`.

For a live CoinGecko reference file, save a `/simple/price` payload obtained
through the read-only CoinGecko MCP/client in an authorized environment
(request `include_last_updated_at` so staleness is measurable), then pass
`--base-by-id bitcoin=BTC` to `wallex-reconcile`. Request the same quote
currency as the Wallex pair (e.g. `vs_currencies=usdt`) or expect
`INCOMPARABLE_QUOTE` by design.

## Safety switches

- `WALLEX_PAPER_DISABLE=1` — paper kill switch: broker creation, marks,
  and simulated orders are refused.
- `WALLEX_ENABLE_LIVE_TRADING=1` in the process environment also blocks the
  paper ledger, so paper and live modes cannot share a process by
  misconfiguration. The paper modules import no HTTP/WebSocket/live code
  at all (enforced by tests), report `live_trading_enabled: false` and
  `order_submission_attempted: false`, and have no order endpoint to call.

## Read-only provider connectivity check (authorized environments only)

`scripts/check_provider_connectivity.py` is never run by offline CI.

```sh
# Which secret names are configured? Booleans only, no network:
python scripts/check_provider_connectivity.py --config-only

# Read-only checks (Wallex public markets without any key; CoinGecko
# /ping and /simple/price with COINGECKO_DEMO_API_KEY as a header):
COINGECKO_DEMO_API_KEY=... WALLEX_API_KEY=... \
  python scripts/check_provider_connectivity.py
```

In GitHub Actions the same script is wired to the manually dispatched
`Provider read-only check` workflow (`workflow_dispatch`, default branch
only), with both values supplied from repository secrets. Until that
workflow (or a local run) succeeds, authenticated provider access must be
reported as **unverified**; configuration presence alone proves nothing.
`WALLEX_API_KEY` is never sent to the public markets endpoint by the check
script — public endpoints do not need it — and no account endpoint is
called.

## Interpretation limits

- 20 candles cannot establish profitability, edge, or strategy quality.
- A sparse reference means measured deviation also includes ordinary price
  movement between observations; thresholds are caller policy, not facts.
- `OK` audit/reconciliation statuses do not prove feed completeness or
  that either price was executable (no order book, depth, queue, partial
  fills, taxes, or tiered fees are modeled).
- Synthetic fixture results say nothing about any real Wallex market.
