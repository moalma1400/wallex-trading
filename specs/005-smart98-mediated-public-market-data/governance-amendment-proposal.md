# Governance amendment proposal: autonomous Smart98-mediated Wallex challenge agent

**Status: PROPOSED FOR REVIEW — NOT EFFECTIVE**
**Date:** 2026-10-22

The repository owner has clarified that the intended hackathon product must autonomously perform the evaluated trading workflow. Manual trades do not count as valid algorithmic performance under the requirements supplied by the owner. This proposal records that target but does not itself authorize implementation, network requests, account access, or live orders.

## Current governing baseline

The current constitution (v1.1.0), AGENTS.md, and Features 001–004 require offline-only implementation and prohibit Smart98/Wallex network adapters. Those rules remain binding until an explicit amendment is reviewed and accepted through repository governance. The owner-provided challenge text is requirements evidence, not independent proof of the actual Smart98 tool contract, account permissions, or any legal/compliance conclusion.

## Proposed scope, if separately accepted

- A fully automated, auditable agent for the dedicated hackathon challenge account.
- Public market data and permitted market metadata through verified Smart98-mediated tools.
- Algorithmic signal generation, buy/sell decisions, deterministic risk checks, and order submission through verified, explicitly authorized Smart98-mediated Spot trading tools.
- Order lifecycle management based on verified contracts: acknowledgements, status, partial/full fills, timeouts, safe retry/idempotency, reconciliation, and cancellation only where expressly permitted.
- Decision/order audit logs with rationale, input/source timestamps, algorithm/model version, risk result, tool result, order/fill identifiers, fees, and realized outcomes; no credentials or unnecessary personal data.
- Backtesting and shadow testing isolated from live order submission.
- No direct Wallex application/API access or fallback; Smart98 is the required mediation layer.

## Explicit exclusions

This proposal does not authorize withdrawals, transfers, deposits, wallet operations, margin, leverage, borrowing, shorting, derivatives, OTC execution, or actions outside the verified permitted Spot markets and challenge account permissions. It does not authorize manual trades as evaluated performance. It does not authorize collecting or storing team members' phone numbers, national IDs, birth dates, credentials, or private account data in the trading repository or agent logs. It does not select a strategy, pair, timeframe, fee assumption, capital, or risk tolerance beyond independently verified challenge rules and explicit owner inputs.

## Required acceptance gates before implementation

1. Review and accept the constitution and AGENTS.md amendments, keeping unrelated prohibitions explicit.
2. Accept the Feature 005 spec, plan, tasks, and security/data-flow review.
3. Verify and version the actual Smart98 mediation contract: transport, authentication/secret boundary, tool catalog, schemas, permissions, errors/timeouts, and order lifecycle semantics. Do not infer behavior from tool names.
4. Verify the dedicated challenge-account permissions and exact allowed market list. Reuse the canonical disabled-pair registry; absence from exclusions is not authorization.
5. Define deterministic risk limits and order constraints from official challenge rules or explicit owner input; the LLM must not override the risk gate.
6. Validate timeout ambiguity, retry idempotency, partial fills, order-state reconciliation, market-data freshness/completeness, decimal precision, and final realized-TMN settlement with sanitized fixtures.
7. Keep tests/validators/replay/backtests offline and deterministic. Any future live activation requires a separate explicit decision and a controlled authorization procedure; this proposal is not that activation.
8. Document current jurisdiction/compliance/security review requirements before actual exchange use. This proposal does not determine whether use is lawful or permitted.
9. Preserve PR #1; do not merge or force-push as part of the proposal.

## Decision status

- Governance amendment accepted: **NO — pending review**
- Feature 005 implementation authorized: **NO — pending review**
- Network/runtime testing authorized: **NO**
- Challenge-account trading authorized: **NO**
- Withdrawals/transfers/deposits and leveraged/derivative capabilities authorized: **NO**

Until these statuses change through an explicit reviewed decision, the existing offline-only baseline remains in force.
