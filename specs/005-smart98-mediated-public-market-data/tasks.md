# Tasks — Feature 005 (Draft)

**Status: Approved for bounded public read-only adapter work only after evidence gates; live execution remains disabled and separately gated.**

- [x] T001 Review and record constitution v1.2.0 amendment for bounded Smart98-mediated public read-only Spot data.
- [x] T002 Review and align AGENTS.md with the approved adapter scope and separately gated autonomous challenge execution.
- [ ] **T003 — OPEN / BLOCKED:** Verify authoritative Smart98 mediation/tool contract, exact schemas/permissions, and source/version for market data and challenge-account order lifecycle tools. The user reports a Smart98 evidence report, but its body/attachment is absent; only an aggregate operator-reported read-only public-market-data claim can be recorded. Exact tool evidence and authoritative contract/source remain missing; see [`T003–T005 review`](../../docs/research/feature-005-smart98-evidence-review-2026-10-22.md).
- [x] T004 Review and document security, privacy, risk, and jurisdiction/compliance gates. **The review is complete; permission, legal/compliance, organizer, and live-execution gates remain unresolved.** See the T004 review record.
- [x] T005 Inspect and document existing market-data models, source register, disabled-pair registry, replay/shadow interfaces, validators, and gaps. See the architecture inventory in the T004/T005 review record.
- [ ] T006 Define provider-neutral data types and provenance/freshness/completeness contracts. Do not duplicate existing types or treat unverified local parser assumptions as upstream schemas.
- [ ] T007 Implement only the approved Smart98-mediated public market-data adapter after T003–T006 gates pass; do not implement order submission; never direct-call Wallex.
- [ ] T008 Add sanitized offline fixtures and negative/fail-closed tests, including order idempotency, timeout ambiguity, partial fills and reconciliation.
- [x] T009 Run the full offline suite and every applicable repository validator; see the validation record in the dated review and research log.
- [x] T010 Update evidence, architecture, research log, unresolved questions, and report; T003 remains blocked and exact report/tool findings are not inferred.
- [ ] **T011 — BLOCKED:** Commit/push to and verify the existing PR #1 branch. GitHub reports PR #1 is already merged and the Arena session is constrained to a different active branch; do not create a second PR or switch branches without owner direction.

**Gate:** T003–T006 remain required before adapter implementation. Public read-only Smart98 data validation is allowed only after the actual tool contract and access path are verified; no direct Wallex calls. No new MCP may be installed/configured by the agent. Order submission and live activation are out of scope and require a separate explicit owner activation decision after challenge-account permissions, official rules, allowed Spot markets, deterministic risk controls, reconciliation and relevant compliance constraints are verified.
