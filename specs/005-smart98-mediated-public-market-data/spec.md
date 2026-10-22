Feature Specification: Fully Automated Smart98-Mediated Wallex Challenge Agent

**Feature**: 005-smart98-mediated-public-market-data
**Status**: Approved for implementation of verified Smart98-mediated public read-only Spot market-data adapter and offline tests; autonomous order execution remains separately gated
**Date**: 2026-10-22

## Context

The owner explicitly directed that repository policy be corrected to match the trading-competition objective. Constitution v1.2.0 and AGENTS.md now authorize implementation of a narrowly bounded Smart98-mediated adapter for verified public, read-only Spot market data. This approval does not authorize live order execution or direct Wallex application calls. Any public-data validation through Smart98 requires the actual tool contract and access path to be verified first.

## Competition context and automation priority

This is a time-bounded trading hackathon, not a bug-bounty/security-testing engagement. The product goal is an autonomous agent capable of repeated market-data → decision → risk check → order execution → order/fill reconciliation cycles throughout the approximately two-day trading window described by the owner. The product must not be reduced to an offline-only research tool, signal recommender, or workflow that requires a human to approve every trade.

Within official challenge rules and verified dedicated-account permissions, the agent may use available Skills, MCP servers, tools, AI models, Agentic AI frameworks, and market-analysis utilities. The system should select tools based on verified capability and reliability, not impose a bug-bounty-specific prohibition merely because this is a financial platform. Tool availability alone does not prove a tool's exact schema, side effects, or permission scope; these must be verified before wiring them into execution.

Every evaluated trading decision and order must be algorithmic. A deterministic risk gate, allowed-market registry, order-state reconciliation, safe handling of timeouts/retries, and audit logs remain mandatory. The agent must not perform prohibited account actions, manual evaluated trades, self-trading, wash trading, or market manipulation. “Use any skill/MCP/tool” means use any suitable tool within the challenge's verified permissions and rules, not bypass those rules or risk controls.

This section records the approved product scope. The constitution and AGENTS.md have been amended to permit the bounded public read-only Smart98 adapter. Live account/order actions remain disabled until their separate activation gate is satisfied.

## User story

As a hackathon participant, I want an autonomous, auditable trading agent that obtains permitted market data, decides, applies deterministic risk checks, submits and manages permitted orders, and records every decision through Smart98-mediated tools, so that all evaluated trades are algorithmic rather than manually placed.

## Approved public-market-data scope and separately gated execution

For this Feature 005 implementation phase, approval is limited to:

- Public Spot market metadata, candles, order-book snapshots, recent public trades, and ticker observations **only through verified Smart98-mediated read-only tools**; the exact tool list and schemas remain unverified until T003 passes.
- Provider-neutral internal data handling with provenance, timestamps, Decimal-safe parsing, freshness/completeness validation, and fail-closed Spot eligibility; do not invent fields or thresholds.
- Offline backtest and isolated shadow testing with sanitized fixtures. Tests and CI remain offline.
- No private-account reads, order submission, cancellation, or other state-changing action in this phase.

Autonomous challenge-account execution is a later, separate activation boundary and is not authorized by the current implementation task. If separately accepted in the future, order lifecycle handling (acknowledgements, status, partial/full fills, timeouts/retries/idempotency, cancellation where permitted, and reconciliation) must use verified contracts, dedicated-account permissions, official rules/allowed markets, deterministic risk controls, audit records, relevant compliance review, and an explicit owner activation decision.

## Exclusions

No direct Wallex application/API calls or direct-access fallback. No withdrawal, transfer, deposit, wallet operation, margin, leverage, borrowing, shorting, derivatives, OTC execution, or any operation outside the challenge's verified permitted Spot markets and account permissions. No manual trading is accepted as evaluated algorithmic performance. No live execution is authorized in this implementation phase. No strategy, pair, timeframe, fees, capital, or risk preferences are silently selected; challenge-specific parameters must come from verified rules or explicit owner inputs.

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

## Technical judging criteria and evidence matrix

The owner-provided rubric describes 150 technical points across five criteria. Until independently confirmed by the organizer, retain its provenance as user-provided/proposed; nevertheless, use it as a core engineering acceptance matrix rather than documentation-only guidance.

| Criterion | Points (provided rubric; confirmation pending) | Required implementation evidence |
|---|---:|---|
| Strategy logic | 40 | Explainable entry/exit hypotheses, supporting and contradictory evidence, strategy tests, and reproducible decisions. |
| Genuine AI use | 35 | Model output materially influences decisions; record model/prompt versions and input/output; tests distinguish AI analysis from deterministic rules. |
| Risk and capital management | 30 | Deterministic pre-trade controls, configured order-size/exposure limits, fee-aware sizing, loss/drawdown gates, and fail-closed tests. |
| Reproducibility | 25 | Run guide, versioned code/config/data, traceable decision/order/fill/fee records, and repeatable tests. |
| Backtesting and shadow testing | 20 | Chronological evaluation, no lookahead leakage, explicit costs, relevant metrics, and proof shadow mode cannot submit real orders. |

Maintain a traceability matrix mapping each criterion to source files/Skills, specification/task IDs, automated tests, evidence artifacts, and status (PASS, PARTIAL, FAIL, or NOT TESTED). Never claim points earned or tests passed without recorded evidence. Preserve Feature 002's next-bar-open/cost contract. The AI model may inform strategy decisions but must never override deterministic risk or challenge-eligibility gates.

## Open questions

- What approved, versioned Smart98 contract documents the mediation path and tool schemas?
- Which Smart98-mediated market-data and challenge-account order tools/fields are actually available, and what are their permissions, timeout, retry/idempotency, partial-fill, cancellation, pagination and truncation semantics?
- How are market-data retrieval time and source provenance represented?
- What evidence is required for current jurisdiction/compliance approval before any real exchange use?

## Governance status

The scope amendment is recorded in constitution v1.2.0 and `AGENTS.md`. Implementation is authorized for verified public read-only Spot market data through Smart98, offline mocks/tests, and documentation. This does not authorize configuring new MCPs on the owner's behalf, direct Wallex calls, private account access, or live order execution. Live execution requires the separate activation gate above and must remain disabled during this implementation task.