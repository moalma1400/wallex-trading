# Tasks — Feature 005 (Draft)

**Status: Blocked pending governance review; not an execution authorization.**

- [ ] T001 Review proposed constitution amendment; retain offline-only baseline until accepted.
- [ ] T002 Review proposed AGENTS.md amendment and explicit autonomous challenge-account Spot trading boundary.
- [ ] T003 Verify authoritative Smart98 mediation/tool contract, exact schemas/permissions, and source/version for market data and challenge-account order lifecycle tools.
- [ ] T004 Review security, privacy, risk, and jurisdiction/compliance gates.
- [ ] T005 Inspect existing market data models, source register, disabled-pair registry, replay/shadow interfaces, and validators.
- [ ] T006 Define provider-neutral data types and provenance/freshness/completeness contracts.
- [ ] T007 Implement only approved Smart98-mediated market-data and explicitly authorized challenge Spot order mappings; never direct-call Wallex.
- [ ] T008 Add sanitized offline fixtures and negative/fail-closed tests, including order idempotency, timeout ambiguity, partial fills and reconciliation.
- [ ] T009 Run full offline suite and every applicable repository validator.
- [ ] T010 Update evidence, architecture, research log, unresolved questions, and report.
- [ ] T011 Commit/push to the existing PR branch and verify PR #1 head; do not merge.

**Gate:** T007–T011 must not begin until T001–T006 are reviewed and approved. No network/runtime request is authorized by this task list. After governance approval, any separate live activation must be explicitly authorized and confined to the challenge account and verified permitted Spot actions.