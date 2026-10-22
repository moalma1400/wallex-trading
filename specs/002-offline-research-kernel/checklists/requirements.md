# Requirements Checklist: Offline Research Kernel

- [x] Scope limited to local/synthetic data and offline deterministic calculations.
- [x] No strategy, market, timeframe, capital, cost, leverage, or personal risk profile chosen.
- [x] Explicit non-goals: network access, account/data access, live/paper exchange connection, orders, transfers, withdrawals, Smart98 adapter, and margin.
- [x] Data-quality edge cases cover malformed decimal/time, OHLC invariants, ordering, duplicates, symbols, and optional explicit interval gaps.
- [x] Causal replay semantics and cost simplifications are stated.
- [x] Jurisdiction-specific compliance gate is documented without legal assurances.
- [x] Implementation acceptance tests pass and source/link validators remain offline.
- [x] User-facing limitations and Feature 001 coverage status are reconciled after implementation.
