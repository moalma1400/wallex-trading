Feature Specification: Fully Automated Smart98-Mediated Wallex Challenge Agent

**Feature**: 005-smart98-mediated-public-market-data (scope revision proposed)
**Status**: Draft for governance review; implementation not authorized
**Date**: 2026-10-22

## Context

The owner approved preparing a formal scope/governance proposal. The current constitution v1.1.0 and AGENTS.md remain authoritative and require offline-only work, so this feature is not permission to implement an adapter or perform network requests. It proposes a narrowly bounded future capability: public, read-only Spot market data through Smart98 only.

## Competition context and automation priority

This is a time-bounded trading hackathon, not a bug-bounty/security-testing engagement. The product goal is an autonomous agent capable of repeated market-data → decision → risk check → order execution → order/fill reconciliation cycles throughout the approximately two-day trading window described by the owner. The product must not be reduced to an offline-only research tool, signal recommender, or workflow that requires a human to approve every trade.

Within official challenge rules and verified dedicated-account permissions, the agent may use available Skills, MCP servers, tools, AI models, Agentic AI frameworks, and market-analysis utilities. The system should select tools based on verified capability and reliability, not impose a bug-bounty-specific prohibition merely because this is a financial platform. Tool availability alone does not prove a tool's exact schema, side effects, or permission scope; these must be verified before wiring them into execution.

Every evaluated trading decision and order must be algorithmic. A deterministic risk gate, allowed-market registry, order-state reconciliation, safe handling of timeouts/retries, and audit logs remain mandatory. The agent must not perform prohibited account actions, manual evaluated trades, self-trading, wash trading, or market manipulation. “Use any skill/MCP/tool” means use any suitable tool within the challenge's verified permissions and rules, not bypass those rules or risk controls.

This section records the intended product scope. It does not itself amend the current constitution or authorize live network/account actions; the governance proposal must be reviewed and accepted before implementation.

## User story

As a hackathon participant, I want an autonomous, auditable trading agent that obtains permitted market data, decides, applies deterministic risk checks, submits and manages permitted orders, and records every decision through Smart98-mediated tools, so that all evaluated trades are algorithmic rather than manually placed.

## Scope proposed for later governance approval

- Public market metadata, candles, order-book snapshots, recent public trades and ticker observations through verified Smart98-mediated tools.
- Autonomous decision-making and trade execution through verified, explicitly authorized Smart98-mediated order tools for the challenge account only.
- Order lifecycle management: acknowledgements, status polling, fills/partial fills, cancellation only when explicitly permitted, idempotency and reconciliation according to verified contracts.
- Provider-neutral interfaces with provenance, timestamps, Decimal-safe parsing, freshness/completeness validation and fail-closed eligibility.
- Deterministic risk gate outside the LLM; the model cannot bypass capital, market, order-size, drawdown, or challenge-policy controls.
- Audit record for every decision and order lifecycle event, without credentials or unnecessary personal data.
- Offline backtest and isolated shadow testing; fixtures by default. Any live account action requires the approved governance and authorization gates below.

## Exclusions

No direct Wallex application/API calls or direct-access fallback. No withdrawal, transfer, deposit, wallet operation, margin, leverage, borrowing, shorting, derivatives, OTC execution, or any operation outside the challenge's verified permitted Spot markets and account permissions. No manual trading is accepted as evaluated algorithmic performance. No live execution is authorized by this draft. No strategy, pair, timeframe, fees, capital, or risk preferences are silently selected; challenge-specific parameters must come from verified rules or explicit owner inputs.

## Acceptance criteria (only after governance and account/tool authorization)

1. Accepted amendments explicitly permit only the described public read-only exception and retain all other prohibitions.
2. Smart98-mediated transport, authentication boundary, tool schemas, permissions, and source/version are supported by authoritative evidence; no assumptions are coded as facts.
3. Every tool is classified by verified schema and permissions; public data and state-changing order tools are separated explicitly.
4. Order execution is exclusively algorithmic through the verified Smart98-mediated interface; the trading app never connects directly to Wallex.
5. Deterministic risk checks precede every order and cannot be overridden by the LLM; market eligibility reuses the canonical disabled-pair registry and fail-closed gates.
6. Data records preserve source/tool/version, retrieval time, observation time when supplied, symbol, interval, completeness and validation status.
7. Invalid numeric values, timestamps, inconsistent arrays, duplicate/out-of-order candles, stale/partial data, unsupported markets and contradictory metadata fail closed.
8. Order handling covers uncertain timeouts and retries without duplicate orders, partial fills, cancellations where authorized, and reconciliation against verified order/fill records.
9. Each decision/order has an auditable reason trail and exact algorithm version; no credentials or unnecessary personal data enter logs or artifacts.
10. Backtests and shadow tests cannot invoke the live submitter; tests and CI stay offline/deterministic.
11. Live execution stays disabled until governance, exact tool contract, challenge-account permissions, compliance review and an explicit separate activation decision are recorded.
12. Existing PR #1 is updated in place only after review; no second PR, force-push, or merge.

## Open questions

- What approved, versioned Smart98 contract documents the mediation path and tool schemas?
- Which Smart98-mediated market-data and challenge-account order tools/fields are actually available, and what are their permissions, timeout, retry/idempotency, partial-fill, cancellation, pagination and truncation semantics?
- How are market-data retrieval time and source provenance represented?
- What evidence is required for current jurisdiction/compliance approval before any real exchange use?

## Governance status

The spec is a proposal. Current offline-only requirements remain binding until formally amended. No adapter implementation, Smart98 configuration change, production request, or live integration is authorized by this artifact.