# Governance amendment proposal: Smart98-mediated public market data

**Status: PROPOSED FOR REVIEW — NOT EFFECTIVE**
**Date:** 2026-10-22

The repository owner authorized preparing a narrow proposal for a future Smart98-mediated, public read-only Spot market-data interface. This document records a proposal only; it does not authorize implementation or network/runtime testing.

## Current baseline

The current constitution (v1.1.0) and AGENTS.md require local/offline work and prohibit network adapters. Those rules remain binding until an explicit governance amendment is reviewed and accepted through the repository process.

## Proposed scope, if separately accepted

- Public read-only market metadata, candles, order-book snapshots, recent trades, and ticker observations, only where the actual Smart98-mediated tool contract and read-only behavior are verified.
- A provider-neutral internal interface; the application must never call Wallex directly or fall back to a direct endpoint.
- Source provenance, UTC retrieval times, schema/data-quality validation, Decimal-safe numeric parsing, freshness checks, and fail-closed eligibility.
- Sanitized fixtures and offline deterministic tests by default.

## Out of scope

No private account data, account credentials, state-changing operations, order execution, money movement, margin/leverage, derivatives, or strategy selection. No production requests or live smoke tests are authorized by this proposal. No model-visible secrets or private account data may be stored in the repository.

## Gates before implementation

1. Review and accept the constitution and AGENTS.md amendments.
2. Review Feature 005 specification, plan, and security/data-flow assessment.
3. Verify exact Smart98 tool names, schemas, transport/auth boundary, and read-only semantics from authoritative evidence.
4. Reuse the existing canonical disabled-pair registry and eligibility/risk gates; do not introduce a competing allowlist.
5. Validate timestamps, response completeness, symbol mapping, Decimal handling, staleness, and failures with mocked fixtures.
6. Keep tests and validators offline and deterministic; fail closed when evidence or configuration is unknown.
7. Preserve the existing PR #1; do not merge or force-push as part of this proposal.

## Decision status

- Governance amendment accepted: **NO — pending review**
- Feature 005 implementation authorized: **NO — pending review**
- Network/runtime testing authorized: **NO**
- Any private or state-changing capability authorized: **NO**

The offline-only baseline remains in force until a reviewed decision explicitly changes these statuses.