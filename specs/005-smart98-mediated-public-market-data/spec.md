Feature Specification: Smart98-Mediated Public Spot Market Data

**Feature**: 005-smart98-mediated-public-market-data
**Status**: Draft for governance review; implementation not authorized
**Date**: 2026-10-22

## Context

The owner approved preparing a formal scope/governance proposal. The current constitution v1.1.0 and AGENTS.md remain authoritative and require offline-only work, so this feature is not permission to implement an adapter or perform network requests. It proposes a narrowly bounded future capability: public, read-only Spot market data through Smart98 only.

## User story

As an offline researcher, I want a provider-neutral contract for public Spot market observations, so that any future approved Smart98-mediated feed can be validated and audited without coupling strategy/replay logic to MCP tool names or enabling account actions.

## Scope proposed for later approval

- Public market metadata, candles, public order-book snapshots, recent public trades, and ticker observations only when actual tool schemas and read-only semantics are verified.
- Internal provider-neutral types/interfaces with provenance and retrieval timestamps.
- Strict schema/data-quality checks, UTC timestamps, Decimal-safe numeric parsing, freshness and completeness controls, fail-closed eligibility.
- Mock-only tests and offline deterministic validators.
- Optional adapter configuration disabled by default; unknown configuration must fail closed.

## Exclusions

No direct Wallex application/API calls; no private account reads, credentials, account/order history, order placement/amendment/cancellation, transfers, deposits, withdrawals, wallet operations, margin, leverage, borrowing, shorting, derivatives, OTC execution, or any other state change. No live smoke test is authorized. No strategy, pair, timeframe, fees, capital, or risk preferences are selected.

## Acceptance criteria (only after governance approval)

1. Accepted amendments explicitly permit only the described public read-only exception and retain all other prohibitions.
2. Smart98-mediated transport, authentication boundary, tool schemas, permissions, and source/version are supported by authoritative evidence; no assumptions are coded as facts.
3. Public tool calls are classified read-only based on verified contract, not name alone.
4. The existing canonical disabled-pair registry and eligibility/risk checks are reused; no competing allowlist is added.
5. Data records preserve source/tool/version, retrieval time, observation time when supplied, symbol, interval, completeness, and validation status.
6. Invalid numeric values, timestamp units, inconsistent arrays, duplicate/out-of-order candles, stale/partial data, unsupported markets, and contradictory metadata fail closed with stable reasons.
7. Decimal values are constructed from original decimal strings where possible; binary float conversion is not used as the source of truth.
8. Unit tests, validators, CI, replay and backtests remain offline and deterministic.
9. No credentials or private account data enter source, fixtures, logs, model context, or artifacts.
10. Existing PR #1 is updated in place only after review; no second PR, force-push, or merge.

## Open questions

- What approved, versioned Smart98 contract documents the mediation path and tool schemas?
- Which actual public tools and fields are available, and what are timeout, retry, pagination, and truncation semantics?
- How are market-data retrieval time and source provenance represented?
- What evidence is required for current jurisdiction/compliance approval before any real exchange use?

## Governance status

The spec is a proposal. Current offline-only requirements remain binding. No adapter implementation, Smart98 configuration change, production request, or live integration is authorized by this artifact.