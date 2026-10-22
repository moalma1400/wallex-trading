# Feature Specification: Wallex/Starcoach Hackathon Knowledge Base and Offline Policy

**Feature Directory**: `004-wallex-hackathon-policy`
**Session Branch**: `arena/81f9fa39-wallex-trading` (fixed by Arena)
**Created**: 2026-10-21
**Status**: Local implementation and offline validation complete; official challenge facts, audio and any live authorization remain unresolved/out of scope
**Input**: User-attached `arena_wallex_hackathon_knowledge_base_prompt.md`; it is user-provided evidence, not independently verified official policy.

## Context and boundaries

Provide an auditable, searchable knowledge base and purely offline, fail-closed controls for the provided spot-only challenge brief. Preserve the source-list appendix byte-for-byte and derive one deterministic normalized pair registry with explicit duplicate/malformed reporting. Keep all challenge facts tagged `PROVIDED_BY_CHALLENGE_BRIEF`, `OFFICIAL_SOURCE_VERIFIED`, `INFERRED`, `UNRESOLVED`, or `REQUIRES_ORGANIZER_CONFIRMATION`. None of the supplied challenge terms is independently official-verified in this feature.

Feature 004 remains the challenge-policy and offline-control source of truth. The separate Feature 005 now governs the approved Smart98-mediated public read-only Spot market-data adapter. Feature 004 itself adds no order adapter, private-account access, credentials, deposit/transfer/withdrawal code, real challenge-account data, or account member PII. Backtest/shadow/dry-run are isolated. Existing Feature 002 causal next-bar-open replay and explicit cost interface remain unchanged. No strategy, market, fee, AI provider, official market status, cutoff, conversion route, numeric risk limit, final rubric or profitability is invented. Proposed rubric is labeled proposed. Audio review remains incomplete because no audio was attached.

## User Scenarios & Testing

### User Story 1 — Find the challenge rules and evidence (P1)
As an operator or judge, I can locate the challenge rules, market exclusions, source provenance, unresolved questions and submission guide without mistaking a user attachment for official verification.

**Independent Test**: All challenge claims carry explicit status; source-register hash checks pass; raw list and canonical JSON match and report parse defects; no duplicate list is embedded as a competing canonical source.

### User Story 2 — Fail closed on market eligibility and risk (P1)
As an offline researcher, I can obtain machine-readable allow/deny reasons for a pair/order proposal, and missing, stale, contradictory, untrusted or unconfigured evidence prevents approval.

**Independent Test**: Synthetic-only metadata can pass only with explicit test mode and warning; unknown/not-disabled is denied; non-spot, disabled pair, missing strategy/risk approval, unsupported quote, stale data, invalid order precision/minimums, missing risk cap or non-reconciled state blocks.

### User Story 3 — Reproduce and audit an offline run (P1)
As a judge, I can match versioned decision events to a code commit, config, strategy, source data, and deterministic local run without any private exchange or network interaction.

**Independent Test**: Required event fields, stable IDs, provenance and event versions are validated; secret/PII-like fields and exchange-origin records are rejected; backtest/shadow/dry-run never submit and live fails closed.

### User Story 4 — Assess end-state readiness honestly (P1)
As an operator, I can distinguish realized and unrealized P&L, fees, TMN cash, non-TMN inventory, and internal estimates from official valuation, and readiness is blocked without exact cutoff and permitted conversion evidence.

**Independent Test**: Unresolved/mismatched cutoff, unreconciled balances, unknown fees/unrealized P&L, or residual non-TMN inventory blocks readiness; no stale/invented price route is used.

## Functional Requirements

- **FR-001**: Maintain a canonical internal challenge-rules page and linked market-restrictions page with provenance status for every material challenge claim.
- **FR-002**: Register the attachment as a repository-local user-provided source with verified content hash and no fabricated public URL/retrieval time. Do not grant it official status.
- **FR-003**: Preserve the raw supplied disabled-market list verbatim. Derive an uppercase strict `BASE/QUOTE` canonical list, report raw/unique/duplicate/duplicate-excess/malformed counts, and refuse malformed or duplicate runtime registries. Do not maintain a second copy of canonical pairs.
- **FR-004**: Apply spot-only policy. Deny margin, leverage, borrowing, shorts, derivatives, manual performance trades, self/coordinated/wash trading, artificial volume, manipulation, disabled pairs, withdrawals, transfers, deposits and unverified settlement routes.
- **FR-005**: Default live execution off. Feature 004 does not implement a network adapter; the separately approved Feature 005 may implement verified public read-only Spot market data through Smart98 only. Offline backtest/shadow/dry-run cannot invoke a submitter; live dispatch must fail closed with a machine-readable reason until a separate explicit activation gate is satisfied.
- **FR-006**: Eligibility requires explicit challenge context, valid spot metadata, active/orderable/enabled trusted state, not disabled, fresh and noncontradictory source evidence, strategy and risk approvals, supported quote/settlement path, verified precision/minimum order semantics, and complete configuration. “Not disabled” alone MUST NOT authorize.
- **FR-007**: Risk evaluation is offline and configurable; missing/invalid limits or unknown reconciliation/data/signal/cost state veto proposals. Internal limits are not exchange or organizer limits.
- **FR-008**: Preserve a versioned, deterministic, provenance-complete decision/trade-event contract and append-only local log; validate typed payloads, provenance, model/prompt evidence for AI events, timestamps, code/config identifiers and safe fields.
- **FR-009**: Invalid AI output falls back to HOLD. Do not claim a model/provider or AI-derived rationale not actually implemented. Any later AI must materially affect a future decision and remain subordinate to deterministic safety gates. No present-day model backfill for historical runs.
- **FR-010**: Settlement readiness distinguishes realized/unrealized P&L, fees, TMN cash, non-TMN holdings, internal estimates and official valuation. Missing official cutoff/permitted conversion route blocks readiness; never invent route or use stale conversion valuation.
- **FR-011**: Provide offline judge reproduction instructions and a roughly five-minute demo checklist, clearly distinguishing synthetic/replay from live-account performance.
- **FR-012**: Preserve Feature 002 next-bar-open replay semantics and cost interfaces; do not claim synthetic or historical replay alone proves profitability.
- **FR-013**: Keep member PII and private account data/secrets out of repository, fixtures, CI and logs.
- **FR-014**: Record the proposed detailed score breakdown as proposed, not confirmed official scoring. Record organizer confirmation questions without filling unknown values.
- **FR-015**: Update relevant specs, skills, contracts, operator/judge docs, and research/source documentation without replacing the existing Spec Kit setup or disturbing unrelated work.

## Success Criteria

- **SC-001**: Rules and exclusions have a single linked source of truth, intact raw evidence, deterministic canonical data and complete provenance.
- **SC-002**: All unknown/untrusted/stale/contradictory/unconfigured policy inputs deny market/risk/settlement approval with machine-readable reasons.
- **SC-003**: Offline modes demonstrably cannot submit orders; Feature 005 public read-only data access remains separate from order execution; live order dispatch remains unimplemented and blocked until separately activated.
- **SC-004**: Event records are deterministic, versioned, reproducible, auditable and reject secret/PII/exchange-origin data.
- **SC-005**: TMN settlement readiness only reports a value when cutoff, reconciliation, costs and inventory conditions are evidenced; estimates are not presented as official valuation.
- **SC-006**: Existing Feature 002 behavior remains regression-tested and unchanged.
- **SC-007**: Offline tests and repository source/document validators pass; no network, credentials, private account, order, transfer, deposit or withdrawal action is used.

## Deferred and unresolved decisions

Official event timing and cutoff; current disabled/orderable markets and update process; account setup/funding/credit terms; exact feed/API/order/precision/fee/rate semantics; freshness thresholds; strategy; numeric risk limits; allowed TMN conversion routes; settlement rules; final scoring/tie-breaks; data retention and privacy requirements; model/AI evaluation details; submission/video mechanics; and audio contents. All require a traceable organizer/official source. This feature does not authorize live account/order activity. Public read-only market-data integration is governed by Feature 005 and constitution v1.2.0.
