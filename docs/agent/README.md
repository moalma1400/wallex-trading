# Independent Wallex Agent — Shadow Runner

The standalone `wallex-agent` command runs independently of Smart98. It reads only public market metadata, screens Spot markets, and appends auditable JSONL output. It **never places, changes, or cancels orders**.

## Install and run

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
wallex-agent --quote-asset USDT --once
```

Replace USDT with a quote asset verified for the contest. Omit `--once` for continuous polling. Default interval is 60 seconds, bounded to 1–3600 seconds. No API key is needed for public market metadata.

Default output is `var/wallex-agent/shadow.jsonl`; SQLite price observations are persisted at `var/wallex-agent/observations.sqlite3`. Use `--output PATH` and `--state-db PATH` to change them. The state database contains public price observations only, not credentials or account information.

## Cost-adjusted momentum (optional)

The base screen returns `WATCH` or `SKIP`, based on Spot status, quote asset, optional exact symbol allowlist, valid bid/ask and price, maximum spread, and the raw `change_24h` field. It does not infer the unit of `change_24h`.

To enable the additional *research-only* cost estimate, pass explicit per-side fee and slippage assumptions:

```sh
wallex-agent --quote-asset USDT \
  --fee-bps-per-side 5 \
  --slippage-bps-per-side 2 \
  --minimum-net-edge-bps 1
```

Those numbers are examples only, **not verified Wallex fees or a recommended configuration**. Set values from the applicable official fee schedule and conservative evidence-based slippage estimates. Both fee and slippage must be supplied together; if omitted, output explicitly says `COST_MODEL_DISABLED`. No fee default is silently assumed.

The model compares the previous persisted market price to the current public market price and subtracts the current quoted spread plus two-sided fee and slippage reserves. It reports `WATCH_EDGE`, `NET_EDGE_BELOW_COST`, `NON_POSITIVE_MOMENTUM`, `STALE_BASELINE`, or a data-quality status. The first observation is a warm-up only. The output is not a buy/sell recommendation and does not predict future returns. It does not model order-book depth, queue position, real fills, taxes, account-specific fee tiers, adverse selection, or contest rules.

Options: `--minimum-change-24h-raw`, `--maximum-spread-bps`, `--symbols`, `--interval-seconds`, `--maximum-observation-gap-seconds`, `--output`, and `--state-db`. Fee and slippage can also be supplied through `WALLEX_AGENT_FEE_BPS_PER_SIDE` and `WALLEX_AGENT_SLIPPAGE_BPS_PER_SIDE`.

## Ranked shadow opportunities

When the explicit fee and slippage assumptions are supplied, each cycle also includes `ranked_opportunities`: eligible assessments with a `WATCH_EDGE` result, ordered by highest estimated net edge, then lowest spread, then symbol. The label is `SHADOW_CANDIDATE`, not a BUY instruction. Without cost assumptions the list remains empty. See [cost-aware opportunity ranking](OPPORTUNITY-RANKING.md).

## Walk-forward evaluation

Use `wallex-walk-forward` to select the baseline parameters on chronological training blocks and evaluate on later disjoint test blocks. See [the walk-forward guide](WALK-FORWARD.md). It is offline research only and never submits orders.

## Offline paper broker

The independent `wallex-paper` CLI replays explicit JSONL order events, while `wallex-paper-candles` applies a simple long-only momentum baseline to local candles; both write to a persistent virtual ledger. Neither is wired to the shadow runner or provides exchange fill reconciliation or live risk-gate integration. See [Paper Trading](PAPER-TRADING.md).

For the bounded 20-candle audit + paper + Wallex/CoinGecko reconciliation run, including the paper kill switch and the manual read-only provider check, see the [20-candle offline paper mission](PAPER-MISSION-20M.md).

## Safety and limitations

- Smart98 is not a runtime dependency.
- Only the public `GET /hector/web/v1/markets` route is called through the repository-owned fixed-host read client.
- No API key, balance, order, cancellation, or transfer endpoint is used.
- Errors are logged by exception type only; API secrets/headers are not copied to the audit file.
- The spread estimate uses the market metadata's fair bid/ask; this is not guaranteed to be an executable quote.
- Historical backtest, walk-forward research, and the SQLite paper broker are offline tools. The paper broker is not connected to the shadow runner and does not provide exchange fill reconciliation or live risk-gate integration.
- This is not a proven profitable strategy. Live execution remains a separate future feature and must not be enabled by this runner.
