---
name: backtest-audit
description: Review deterministic offline backtests for causality, explicit assumptions, cost accounting, and honest interpretation.
compatibility: Applies to the local strategy-neutral replay package; no exchange connection is present.
metadata:
  owner: wallex-trading
  scope: offline-backtesting
---

# Offline backtest audit procedure

1. Confirm the signal generator is separately selected by the user and is not being silently added by this procedure. Strategy-neutral engines consume supplied decisions; never choose a market, interval, parameter, or strategy.
2. Validate data provenance/quality, chronological ordering, timezone handling, and any explicitly supplied interval. Missing data remains missing.
3. Check that every required assumption is explicit: starting cash/currency, commission, slippage, position/exposure cap, fill timing, and any simplifications. Generic costs are not Wallex fee claims.
4. Verify causal timing: a decision observed at close cannot execute at that close or earlier. Check that the execution model accounts for fees/slippage and has no future-bar leakage.
5. Audit cash/position reconciliation, Spot-only bounds, drawdown arithmetic, partial affordability behavior, and deterministic repeated outputs. Reject unsupported shorts/leverage.
6. Report modeled fills and outputs as scenario arithmetic only. Include uncertainty, drawdowns, costs, data limitations, and out-of-sample limitations; never claim profitability, expected return, suitability, or future execution performance.
7. Do not connect a backtest to Wallex or Smart98, request keys, or query APIs. Real-use proposals require separate technical/security/risk and jurisdiction-specific legal/compliance review.
