# Proposed policy diff for Feature 005

**Review artifact only. Do not apply as effective policy until explicitly accepted.**

## Constitution v1.1.0 — proposed replacement for Core Principle VIII

Current heading: `### VIII. Current Phase Boundary`

Proposed text:

> The current phase permits local/offline, strategy-neutral research tools using synthetic or user-supplied files. A separately approved Feature 005 may add a fully automated, auditable challenge agent after this constitution amendment, the feature acceptance gates, and explicit challenge-account authorization are reviewed and accepted. All Wallex market-data and trading-tool access intended for the agent must pass through a verified Smart98-mediated interface; the trading application must never connect directly to Wallex or use direct access as a fallback. Only verified, explicitly authorized Spot order lifecycle actions for the dedicated challenge account may be automated. Withdrawals, transfers, deposits, wallet operations, margin, leverage, borrowing, shorting, derivatives, OTC execution, and other out-of-scope operations remain prohibited. The agent must apply deterministic risk checks before every order, maintain auditable decision/order logs, and fail closed on unknown data, permissions, markets or order state. Any adapter must be opt-in, disabled by default, fail closed on unknown provider/schema/source/freshness/eligibility, and reuse the canonical disabled-market registry and deterministic risk gates. Tests, validators, replay, backtests, and CI must remain offline and deterministic. This exception does not authorize production smoke tests or establish legal/compliance approval.

## Constitution — proposed addition to Development and Research Constraints

> - A public read-only market-data adapter is permitted only under an explicitly accepted Feature 005 and only through a verified Smart98-mediated contract. The presence of a tool does not prove authorization or read-only behavior. No direct Wallex connection or fallback is allowed. Private/account-sensitive and state-changing capabilities remain prohibited.

## AGENTS.md — proposed replacement for the sentence beginning “The current implementation phase permits only local/offline…”

Proposed text:

> The current implementation phase permits local/offline, strategy-neutral research tools using synthetic or user-supplied files. Only if Feature 005 and the corresponding governance amendment are explicitly accepted may a narrowly scoped public, read-only Spot market-data adapter be implemented, and then only through a verified Smart98-mediated interface. Never connect the trading application directly to Wallex or use direct access as fallback. Do not implement private account reads, credentials in the application/model context, order submission/amendment/cancellation, transfers, deposits, withdrawals, wallet operations, margin, leverage, borrowing, shorting, derivatives, or any other state-changing capability. Keep adapters opt-in and fail-closed; reuse the canonical disabled-pair registry and deterministic risk gates. Tests and validators must not use the network. No production smoke test is authorized by this exception.

## Proposed explicit statement: hackathon is not bug bounty

Add the following to the constitution amendment rationale and to `AGENTS.md` after the amendment is accepted:

> This repository's target is a time-bounded autonomous trading hackathon, not a bug-bounty or security-testing project. Do not import bug-bounty-specific restrictions that prevent the intended trading agent from operating. Within official challenge rules and verified dedicated challenge-account permissions, the agent may use suitable Skills, MCP servers, tools, AI models, Agentic AI frameworks and market-analysis utilities to perform the complete evaluated workflow autonomously: market-data retrieval, decision-making, deterministic risk validation, permitted order submission, order/fill management, and auditable logging. Manual trades do not count as evaluated algorithmic performance. This does not authorize prohibited account actions, out-of-scope markets, direct Wallex fallback, manipulation, self-trading, wash trading, or bypassing risk controls. Verify real tool schemas and permissions; do not invent them.

This addition is proposed only. It does not become effective until reviewed and accepted, and it does not independently activate a live adapter.

## Other policy references requiring review

- README.md: update the phase description only after the amendment is accepted.
- Feature 002/003/004 specs: preserve historical offline scope; add a clearly linked note that Feature 005 is separate and conditional, rather than silently rewriting their acceptance criteria.
- docs/api/challenge-architecture.md: maintain separate statuses for proposed architecture versus implemented/verified interface.
- specs/ROADMAP.md: Feature 005 is currently labelled draft/blocked pending governance review.

## Review checklist

- [ ] Owner explicitly accepts or rejects the exact wording above.
- [ ] Any needed compliance/security reviewers have reviewed the scope.
- [ ] Constitution version and amendment record are updated only after acceptance.
- [ ] AGENTS.md is changed only after acceptance.
- [ ] Feature 005 spec/plan/tasks are approved before implementation.
- [ ] Exact Smart98 mediation contract, market-data schemas, challenge-account permissions, and order lifecycle schemas are independently evidenced.
- [ ] Existing PR #1 remains open and unmerged; no second PR is created.
