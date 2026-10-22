# Tasks — Feature 005 (Draft)

**Status: Approved for bounded public read-only adapter work; live execution remains disabled and separately gated.**

- [x] T001 Review and record constitution v1.2.0 amendment for bounded Smart98-mediated public read-only Spot data.
- [x] T002 Review and align AGENTS.md with the approved adapter scope and separately gated autonomous challenge execution.
- [ ] T003 Verify authoritative Smart98 mediation/tool contract, exact schemas/permissions, and source/version for market data and challenge-account order lifecycle tools.
- [ ] T004 Review security, privacy, risk, and jurisdiction/compliance gates.
- [ ] T005 Inspect existing market data models, source register, disabled-pair registry, replay/shadow interfaces, and validators.
- [ ] T006 Define provider-neutral data types and provenance/freshness/completeness contracts.
- [ ] T007 Implement only the approved Smart98-mediated public market-data adapter; do not implement order submission in this task; never direct-call Wallex.
- [ ] T008 Add sanitized offline fixtures and negative/fail-closed tests, including order idempotency, timeout ambiguity, partial fills and reconciliation.
- [ ] T009 Run full offline suite and every applicable repository validator.
- [ ] T010 Update evidence, architecture, research log, unresolved questions, and report.
- [ ] T011 Commit/push to the existing PR branch and verify PR #1 head; do not merge.

**Gate:** T003–T006 remain required before adapter implementation. Public read-only Smart98 data validation is allowed only after the actual tool contract and access path are verified; no direct Wallex calls. No new MCP may be installed/configured by the agent. Order submission and live activation are out of scope and require a separate explicit owner activation decision after challenge-account permissions, official rules, allowed Spot markets, deterministic risk controls, reconciliation and relevant compliance constraints are verified.