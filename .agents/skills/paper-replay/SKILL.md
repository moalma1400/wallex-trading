---
name: paper-replay
description: Conduct local deterministic paper-ledger replay from offline fixtures only.
compatibility: No live feed or exchange adapter; requires explicit simulation configuration.
metadata:
  owner: wallex-trading
  scope: offline-paper-simulation
---

# Offline paper replay procedure

1. Confirm the data and decisions are local/synthetic and their provenance/licensing is understood. No remote feed, account, or private data may enter the run.
2. Require the user to supply every simulation assumption. Do not provide defaults or treat a market example, cost rate, initial balance, or risk cap as a recommendation.
3. Inspect output semantics: decisions at candle close, modeled fill no earlier than next bar open, explicit fees and slippage, cash limits, Spot-only position, and marked-to-close equity/drawdown.
4. Call the output a local paper ledger or modeled replay, not exchange-connected paper trading and not a real fill. Record limitations; no order API, key, private WebSocket, wallet, transfer, or withdrawal is allowed.
5. Compare repeat runs for determinism and validate all arithmetic with tests. `run_replay` consumes caller-supplied `TargetExposure`; it is not a signal generator. If no selected strategy and valid local dataset are supplied, report strategy evaluation as NOT RUN rather than substituting sample rules or synthetic returns. No strategy performance or profitability conclusion follows from successful replay.
6. Stop and require a separate feature/legal/security review if asked to connect a feed, exchange, or Smart98 service.

## Challenge-mode isolation

- `backtest`, `shadow` and `dry_run` remain local record-only modes. Assert no submitter invocation in tests; `live` must return a blocker because no live adapter exists.
- Fail closed on unknown market state, disabled-list integrity errors, missing risk limits, stale signals, unknown fees or unreconciled state. Never infer permission from absence in the excluded list.
- Separate realized/unrealized P&L, fees, TMN cash, non-TMN assets and internal estimates. Do not mark settlement ready without exact official cutoff and a permitted evidenced conversion route.
