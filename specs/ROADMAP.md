# Repository roadmap

This roadmap tracks bounded research/engineering slices, not exchange capabilities or performance promises. Live trading, network access, account access, and state-changing actions require separate explicit review and authorization.

| Feature | Scope | Status | Evidence / remaining gate |
|---|---|---|---|
| 001 — Wallex official documentation inventory | Persian-first public-source inventory and discrepancy tracking | In progress | Sitemap coverage is a dated snapshot; many page bodies and all byte-exact source archives remain incomplete. |
| 002 — Offline research kernel | Local candle validation, deterministic replay, simulated ledger and explicit cost/risk inputs | Initial offline slice delivered | No live adapter; Spot-only research/paper scope; next-bar-open timing retained. |
| 003 — Historical market data and data quality | Local CSV/JSON import, immutable raw retention, canonical records, strict audit/reporting and gated Feature 002 export | Local-only implementation; validation recorded in this PR | No remote provider. Exact OpenAPI bytes/checksums unavailable; remaining Swagger reader chunks and source evidence gaps stay open. |

No strategy, asset, timeframe, parameter, risk tolerance, or execution mode is selected by this roadmap. No profitability or safety guarantee is implied.
