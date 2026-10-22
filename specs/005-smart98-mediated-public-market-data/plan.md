# Implementation Plan — Feature 005 (Draft)

**Status: Approved for bounded Smart98-mediated public read-only Spot market-data adapter; live execution remains separately gated**

## Summary

Propose a fully automated, auditable challenge agent whose market data, decisions, risk gate, order submission and order lifecycle are mediated through verified Smart98 tools. This requires accepted governance changes, verified tool contracts, and explicit challenge-account authorization. Until those gates pass, only documentation and offline mock tests are permitted.

## Preconditions

- Constitution v1.2.0 and AGENTS.md amendments are recorded; implementation scope is limited to verified public read-only Spot data.
- Exact Smart98-mediated interface, authentication/secret boundary, tool catalog, schemas, and version are evidenced.
- Security, privacy, risk, and jurisdiction/compliance reviews are recorded.
- Feature 005 scope and tasks are accepted.

## Design principles

- Keep provider-specific tool identifiers at the adapter boundary; core domain code uses provider-neutral types.
- Reuse existing candle/data-quality models and canonical disabled-pair registry.
- Never create a second pair allowlist or infer eligibility from absence in exclusions.
- Separate public data, challenge-account reads, and state-changing order tools by explicit verified permissions. Permit only challenge-authorized Spot order lifecycle actions after approval; keep withdrawals/transfers/deposits and non-Spot/leveraged products prohibited.
- Fail closed on unknown provider, missing source evidence, stale data, invalid schemas, incomplete results, or contradictory eligibility.
- Use Decimal from source decimal strings; preserve raw source fields only where safe and useful.
- Unit tests and validators must not access the network.

## Proposed sequence

1. Confirm the amended constitution/AGENTS scope and current PR head.
2. Inspect current data models, source register, pair registry, replay/shadow contracts, validators, and the recovered Smart98 implementation/fixture documents.
3. Verify the actual Smart98 tool contract and classify public read-only data tools from authoritative schemas or explicitly recorded observed contracts.
4. Specify normalized types and error/freshness/completeness contracts without guessing unknown thresholds.
5. Implement an opt-in Smart98-only public market-data adapter; do not implement order submission in this phase and never add a direct Wallex fallback.
6. Add sanitized offline fixtures and tests for malformed/partial/stale/out-of-order data, Decimal precision, provenance, errors and fail-closed eligibility; tests remain offline.
7. Run all offline test suites, source/document validators, pair-registry check, compilation, credential scans, network-client scans and diff checks.
8. Update evidence registers, capability matrix, architecture, research log, unresolved questions, and implementation report.
9. Commit and update existing PR #1 after checks pass; verify remote head and PR metadata.

## Not authorized in this plan

No new MCP may be installed or configured by the agent; the owner will add any selected MCP manually. No direct Wallex request, private-account read, order submission, or live execution is part of this adapter task. Backtest/shadow/CI tests remain offline. After a separate explicit live activation gate is satisfied in the future, only verified permitted challenge-account Spot orders may be automated; no withdrawals, transfers, deposits, margin, leverage, derivatives or manual evaluated trades. No merge or force-push.