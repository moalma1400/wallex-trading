# Implementation Plan — Feature 005 (Draft)

**Status: Draft for governance review only**

## Summary

Propose a narrowly scoped public read-only Spot market-data port and Smart98-mediated adapter, conditional on accepted governance changes and verified upstream contracts. Until then, only documentation and offline mock tests are permitted.

## Preconditions

- Constitution and AGENTS.md amendments are reviewed and accepted.
- Exact Smart98-mediated interface, authentication/secret boundary, tool catalog, schemas, and version are evidenced.
- Security, privacy, risk, and jurisdiction/compliance reviews are recorded.
- Feature 005 scope and tasks are accepted.

## Design principles

- Keep provider-specific tool identifiers at the adapter boundary; core domain code uses provider-neutral types.
- Reuse existing candle/data-quality models and canonical disabled-pair registry.
- Never create a second pair allowlist or infer eligibility from absence in exclusions.
- Keep account-sensitive reads and all write/state-changing operations inaccessible to the adapter.
- Fail closed on unknown provider, missing source evidence, stale data, invalid schemas, incomplete results, or contradictory eligibility.
- Use Decimal from source decimal strings; preserve raw source fields only where safe and useful.
- Unit tests and validators must not access the network.

## Proposed sequence

1. Governance review and amendment acceptance.
2. Inspect current data models, source register, pair registry, replay/shadow contracts, and validators.
3. Verify Smart98 tool contracts and classify read-only tools from authoritative schemas.
4. Specify normalized types and error/freshness/completeness contracts.
5. Implement a minimal opt-in adapter with no direct Wallex fallback.
6. Add sanitized fixtures and tests for malformed/partial/stale/out-of-order data and eligibility fail-closed behavior.
7. Run all offline test suites, source/document validators, pair-registry check, compilation, credential scans, and diff checks.
8. Update evidence registers, architecture, research log, unresolved questions, and implementation report.
9. Commit and update existing PR #1 after checks pass; verify remote head and PR metadata.

## Not authorized in this plan

No implementation or network/runtime testing before the preconditions are met. No private account access, order execution, transfers, margin, leverage, or other state changes. No merge or force-push.