# Repository roadmap

This roadmap tracks bounded research/engineering slices, not exchange capabilities or performance promises. Live trading, network access, account access, and state-changing actions require separate explicit review and authorization.

| Feature | Scope | Status | Evidence / remaining gate |
|---|---|---|---|
| 001 — Wallex official documentation inventory | Persian-first public-source inventory and discrepancy tracking | In progress | Sitemap coverage is a dated snapshot; many page bodies and all byte-exact source archives remain incomplete. |
| 002 — Offline research kernel | Local candle validation, deterministic replay, simulated ledger and explicit cost/risk inputs | Initial offline slice delivered | No live adapter; Spot-only research/paper scope; next-bar-open timing retained. |
| 003 — Historical market data and data quality | Local CSV/JSON import, immutable raw retention, canonical records, strict audit/reporting and gated Feature 002 export | Local-only implementation; validation recorded in this PR | No remote provider. Exact OpenAPI bytes/checksums unavailable; remaining Swagger reader chunks and source evidence gaps stay open. |
| 004 — Wallex/Starcoach hackathon knowledge base and offline policy | Provenance-tagged rules, raw/canonical disabled Spot pairs, fail-closed eligibility/risk, audit events, mode isolation and settlement readiness | Local implementation in progress | Only user-provided brief evidence; official cutoff/current markets/fees/routes/risk limits/final rubric unresolved; no live adapter or audio review. |
| 005 — Smart98-mediated public Spot market data | Draft proposal for public read-only market-data contract, provenance/freshness validation, and a future Smart98-only adapter | **Draft for governance review; implementation blocked** | Current constitution and AGENTS.md still require offline-only work. No adapter, network request, or runtime test is authorized until amendments and exact Smart98 tool contracts are reviewed and accepted. |

No strategy, asset, timeframe, parameter, risk tolerance, or execution mode is selected by this roadmap. No profitability or safety guarantee is implied.
