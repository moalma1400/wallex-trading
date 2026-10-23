# Walk-forward evaluation (offline research)

`wallex-walk-forward` selects parameters using each chronological training block, then evaluates the selected configuration once on that fold's later, disjoint test block. It calls no exchange endpoint, reads no account state, and never submits orders.

## Example

```sh
wallex-walk-forward --input data/BTCUSDT-60s.jsonl \
  --audit-input-data --expected-symbol BTCUSDT --expected-interval-seconds 60 \
  --initial-cash 1000 --folds 3 --train-size 500 --test-size 100 \
  --lookbacks 3,5,10 --entry-thresholds-bps 10,20,30 \
  --exit-thresholds-bps 0,5 --fee-bps-per-side 5 \
  --slippage-bps-per-side 2 --spread-bps-per-side 1 \
  --output reports/walk-forward.json
```

The numeric costs are illustrative only, not verified Wallex fees. Use the applicable official fee schedule and documented conservative execution assumptions. A data audit with status `INVALID` always blocks the run; `REVIEW` blocks by default and requires explicit review before `--allow-review-data`.

## Method

- Candles must be valid, timestamped and strictly chronological.
- Folds use consecutive, non-overlapping train/test blocks; leftover rows are unused.
- Every fold selects among the provided lookback, entry-threshold and exit-threshold grids using training return only. Ties prefer lower training drawdown, then simpler numeric parameters.
- The selected parameters are evaluated on the subsequent test block exactly once.
- Test blocks are isolated simulations, each with fresh initial cash; aggregate statistics are descriptive fold summaries, not a continuous portfolio curve.
- Test blocks are never used to choose parameters. Nevertheless, repeated human iteration over the same test set can cause research-level leakage and overfitting.

## Interpretation and limits

This is a baseline validation tool, not proof of an edge or a recommendation. It reports each test fold's marked net return, max drawdown, completed round trips and win rate when available, plus mean/best/worst fold return. It does not model depth, queue position, partial fills, taxes, variable fees, outages, or intrabar execution. Validate data provenance, candle interval, missing periods and cost assumptions before interpreting results. No live trading is enabled.
