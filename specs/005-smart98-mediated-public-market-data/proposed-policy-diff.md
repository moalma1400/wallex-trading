# Proposed policy diff for Feature 005

**Review artifact only. Do not apply as effective policy until explicitly accepted.**

## Constitution v1.1.0 — proposed replacement for Core Principle VIII

Current heading: `### VIII. Current Phase Boundary`

Proposed text:

> The current phase permits local/offline, strategy-neutral research tools using synthetic or user-supplied files. A separately approved Feature 005 may add only public, read-only Spot market-data retrieval through a verified Smart98-mediated interface, after this constitution amendment and the feature's acceptance gates are reviewed and accepted. The trading application must never connect directly to Wallex or use direct Wallex access as a fallback. No private account reads, account credentials in the application/model context, order placement/amendment/cancellation, transfers, deposits, withdrawals, wallet operations, margin, leverage, borrowing, shorting, derivatives, or other state-changing operations are permitted. Any adapter must be opt-in, disabled by default, fail closed on unknown provider/schema/source/freshness/eligibility, and reuse the canonical disabled-market registry and deterministic risk gates. Tests, validators, replay, backtests, and CI must remain offline and deterministic. This exception does not authorize production smoke tests or establish legal/compliance approval.

## Constitution — proposed addition to Development and Research Constraints

> - A public read-only market-data adapter is permitted only under an explicitly accepted Feature 005 and only through a verified Smart98-mediated contract. The presence of a tool does not prove authorization or read-only behavior. No direct Wallex connection or fallback is allowed. Private/account-sensitive and state-changing capabilities remain prohibited.

## AGENTS.md — proposed replacement for the sentence beginning “The current implementation phase permits only local/offline…”

Proposed text:

> The current implementation phase permits local/offline, strategy-neutral research tools using synthetic or user-supplied files. Only if Feature 005 and the corresponding governance amendment are explicitly accepted may a narrowly scoped public, read-only Spot market-data adapter be implemented, and then only through a verified Smart98-mediated interface. Never connect the trading application directly to Wallex or use direct access as fallback. Do not implement private account reads, credentials in the application/model context, order submission/amendment/cancellation, transfers, deposits, withdrawals, wallet operations, margin, leverage, borrowing, shorting, derivatives, or any other state-changing capability. Keep adapters opt-in and fail-closed; reuse the canonical disabled-pair registry and deterministic risk gates. Tests and validators must not use the network. No production smoke test is authorized by this exception.

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
- [ ] Exact Smart98 contract and read-only tool schemas are independently evidenced.
- [ ] Existing PR #1 remains open and unmerged; no second PR is created.
