# Historical Backtest (research only)

`wallex-backtest` evaluates a simple long-only threshold-momentum baseline on a user-supplied historical candle JSONL file. It is independent of Smart98 and never calls Wallex, accesses account data, or submits orders.

## Gate on data quality before backtesting

For recorder datasets, opt into the audit gate:

```sh
wallex-backtest --input data/BTCUSDT-60s.jsonl \
  --audit-input-data --expected-symbol BTCUSDT --expected-interval-seconds 60 \
  --initial-cash 1000 --lookback-bars 3 \
  --fee-bps-per-side 5 --slippage-bps-per-side 2 \
  --spread-bps-per-side 1 --audit-output reports/data-audit.json \
  --output reports/backtest.json
```

The audit automatically reads the recorder's `INPUT.manifest.json` sidecar if one exists. An `INVALID` dataset is always blocked. A `REVIEW` dataset (for example, because of timestamp gaps or reconnect warnings) is blocked by default; inspect the report and pass `--allow-review-data` only after you understand the gaps. The backtest result records an audit summary. This gate does not prove feed completeness or make a questionable dataset reliable.

## Candle input

One JSON object per line with UTC/offset-aware ISO-8601 `timestamp` and positive `open`, `high`, `low`, `close`, non-negative `volume`. Candles must be strictly chronological with unique timestamps. Naive timestamps, invalid OHLC relationships, and malformed data are rejected.

## Run

```sh
wallex-backtest --input ./candles.jsonl \
  --initial-cash 1000 \
  --lookback-bars 3 \
  --entry-return-bps 20 \
  --exit-return-bps 0 \
  --fee-bps-per-side 5 \
  --slippage-bps-per-side 2 \
  --spread-bps-per-side 1 \
  --output ./reports/baseline.json
```

The numbers are illustrative configuration values, not Wallex fee claims, recommendations, or contest settings. Initial cash is denominated in the same quote currency as the candles. Cost assumptions are required explicitly.

## Execution and accounting assumptions

- Long-only; one position at a time; no leverage, shorting, or capital transfers.
- Momentum signal uses the close at bar t relative to the close `lookback_bars` earlier.
- Orders are simulated at the next bar's open, never at the same close that generated the signal.
- Each side pays the configured fee, slippage, and spread reserve in basis points.
- Equity is marked at each bar close. An open position at the end is marked to market, not silently liquidated.
- The current baseline does not model order book depth, partial fills, queue priority, variable liquidity, gaps within candles, taxes, exchange fee tiers, or outages.
- The threshold-momentum baseline is for testing the research pipeline, not an endorsed or proven profitable strategy.

## Walk-forward partitions

The helper `partition_walk_forward(total_bars, folds, train_size, test_size)` returns chronological, half-open train/test index ranges with **no index reused between any partition**. Insufficient data is rejected; leftover bars after the last complete fold are unused. The helper does not itself optimize parameters or claim out-of-sample profitability; callers must use only each training partition to select parameters and evaluate once on its subsequent test partition.

## Next validation gates

Supply verified historical data, document its source/interval/symbol and gaps, compare simple baselines against fee-aware benchmarks, report drawdown and turnover, and use disjoint walk-forward evaluation before considering paper trading. No live mode is part of this command.
