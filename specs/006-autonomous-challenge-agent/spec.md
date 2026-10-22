# Feature 006 — Autonomous Challenge Agent Readiness

**Status:** Implementation slice proposal; live execution is NOT activated.
**Branch:** `feat/autonomous-challenge-agent-readiness`

## Objective
Prepare a competition-oriented agent that can autonomously perform the full algorithmic cycle after one explicit activation: obtain allowed data through verified Smart98 tools, evaluate a configured strategy, apply deterministic risk controls, submit only permitted Spot orders through a verified Smart98 order tool, reconcile order/fill state, and record an auditable event trail. No per-order human approval is required once the activation gates pass.

“Fully autonomous” does not mean unlimited risk, unrestricted exchange capabilities, bypassing challenge rules, or assuming unknown APIs. The agent must stop rather than improvise when inputs, permissions, schemas, market status, order state, or settlement rules are uncertain.

## Non-goals and prohibited actions
- No direct Wallex REST/WebSocket connection or direct fallback from the trading application.
- No withdrawals, transfers, deposits, wallet/account setting changes, margin, leverage, borrowing, shorting, derivatives, OTC execution, self-trading, wash trading, market manipulation, or unverified operations.
- No credential in model prompts, logs, artifacts, source control, or user-visible output.
- No strategy, symbols, timeframes, fee rates, capital, thresholds, or risk appetite silently invented.
- No claim of legality, eligibility, profitability, or score without evidence.

## Runtime architecture
1. **Smart98 tool registry** — versioned allowlist of exact tool IDs, schemas, source/version, permissions, and side-effect classification.
2. **Market data normalizer** — Decimal-safe fields, UTC timestamps, source provenance, freshness and completeness checks; reject stale, partial, contradictory or malformed observations.
3. **Strategy interface** — pluggable, versioned algorithm; inputs, outputs, model/prompt version and evidence captured. AI can propose a decision but cannot override deterministic policy.
4. **Eligibility gate** — official challenge window, canonical allowed Spot markets, challenge-account identity alias, current orderability, quote/settlement requirements and permissions.
5. **Risk engine** — deterministic hard limits, available-funds check, order-size/notional cap, per-market and aggregate exposure, daily loss/drawdown, order-rate and concentration controls. Every numeric threshold must be supplied by verified rules or explicit owner configuration; unset means deny.
6. **Order state machine** — verified idempotency/client ID, submit acknowledgement, open/partial/filled/cancelled/rejected/unknown handling, timeout ambiguity, no blind retries, reconciliation before further orders. Cancellation only if explicitly allowed.
7. **Audit ledger** — append-only event chain with decision/order/fill IDs, source/tool/schema versions, timestamps, strategy/config hashes, risk results and reconciliation evidence. Redact secrets and unnecessary personal data.
8. **Kill switch** — global disable, loss/drawdown stop, stale-data stop, reconciliation stop, schema drift stop, repeated-error stop and competition-window stop.
9. **Settlement verifier** — exact official cutoff, reconciled fills/fees/balances, supported conversion route and required final asset; unknowns block readiness.

## One-time activation gate
Live order execution is disabled unless every item below has verified evidence and explicit owner activation:
- Current official challenge rules/window and permitted market list.
- Current eligibility/compliance review, including account and jurisdiction constraints.
- Dedicated challenge account and least-privilege permissions verified without exposing credentials.
- Actual Smart98 mediation contract, authentication boundary, exact tool IDs and input/output schemas verified.
- Every proposed order tool classified as state-changing and explicitly allowed by challenge rules.
- Exact market/order precision, minimum/maximum, quote asset, fee, time-in-force and client-order idempotency semantics evidenced.
- All required risk thresholds configured, validated and covered by tests.
- Timeout ambiguity, partial fills, duplicate prevention, reconciliation and cancel policy tested with sanitized fixtures.
- Audit ledger, kill switch, monitoring and operator recovery procedure tested.
- Offline backtest and shadow results reproduced; no lookahead leakage; fees/slippage assumptions documented.
- Explicit activation record names the code commit, config hash, challenge window, allowed market registry hash, tool-contract version and responsible owner.
- Activation is scoped to the dedicated challenge account and ends automatically at the verified challenge cutoff.

No individual order confirmation is required after this gate is explicitly activated. If a gate later becomes false or unknown, autonomous trading stops and new order submission is blocked.

## Acceptance criteria
- Default configuration cannot submit any order.
- Missing or contradictory activation evidence blocks live mode with stable reason codes.
- Backtest/shadow/dry-run cannot reach an order tool.
- Live mode can only use exact allowlisted Smart98 tools and never a direct Wallex endpoint.
- No model output can change hard limits or grant permissions.
- Tests prove no order submission on stale data, unknown balance, schema drift, timeout ambiguity, unreconciled state, blocked symbol, missing fee/risk limit, kill switch, or expired challenge window.
- Secret scanning and log redaction tests pass.
- Offline CI is deterministic and makes no network calls.
- Live integration tests remain disabled until the explicit activation record exists; do not use a real account to discover schemas.

## Current blockers (must not be fabricated)
- Smart98 runtime/transport/auth/tool contract and exact order tool schemas.
- Official competition rules/window, allowed market list, dedicated account permissions and settlement details.
- Explicit numeric risk parameters and chosen strategy.
- Current jurisdiction/compliance decision.
