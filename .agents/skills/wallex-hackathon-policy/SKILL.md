---
name: wallex-hackathon-policy
description: Maintain the user-supplied Wallex/Starcoach challenge knowledge base and offline-only fail-closed controls.
compatibility: No Wallex network access, account data, credentials, live adapter, or order submission; use repository tests and local evidence only.
metadata:
  owner: wallex-trading
  scope: challenge-knowledge-base
---

# Wallex challenge policy procedure

1. Start at `docs/knowledge-base/README.md`, `specs/004-wallex-hackathon-policy/`, and the source-register record `USER-WALLEX-HACKATHON-BRIEF`. Treat the attachment as user evidence, never as independently verified official terms.
2. Tag material terms `PROVIDED_BY_CHALLENGE_BRIEF`, `OFFICIAL_SOURCE_VERIFIED`, `INFERRED`, `UNRESOLVED`, or `REQUIRES_ORGANIZER_CONFIRMATION`. Only use official status with direct official source, exact URL, dated provenance and scope. Do not fill absent dates, cutoff, routes, fees, risk values, APIs, rubric or AI details.
3. Keep the raw disabled-pair evidence verbatim and hash-checked. Regenerate the single canonical machine list from raw input; report duplicate/malformed counts and block invalid registries. Do not reproduce a second editable pair list in docs/config.
4. Eligibility is Spot-only, pure and offline. Require explicit trusted active/orderable metadata, freshness, noncontradiction, challenge permission, strategy approval, risk approval, supported quote/settlement route and verified order constraints. “Not disabled” is never permission; unknown always denies.
5. Keep no margin, leverage, borrowing, shorts, derivatives, transfers, deposits, withdrawals or manual-performance attribution. Prohibit self/coordinated/wash trading, manipulation and artificial volume.
6. Missing risk configuration blocks. Internal values are not Wallex limits. TMN is the current internal quote allowlist; do not invent a USDT route. Offline backtest/shadow/dry-run must never call a submit adapter; live remains unimplemented.
7. Preserve Feature 002 causal next-bar-open semantics and explicit cost interfaces. Do not claim synthetic or historical replay proves profitability. No current-model historical backfill or post-hoc AI rationale.
8. Preserve versioned, deterministic event provenance and typed payloads. Never store credentials, member PII, private account/order data or exchange-origin events in fixtures/logs/CI.
9. Settlement requires official exact cutoff, reconciled balances, known fees/unrealized value, TMN-only ending state, and evidenced permitted conversion. Keep estimates separate from official valuation; stale/inferred conversions block.
10. Present detailed rubric only as proposed until organizers confirm. Keep judge/demo procedures offline and label synthetic output. If only a cleaned transcript is supplied without audio, preserve it as a distinct user transcript, label it unverified, and state audio review remains incomplete.
11. Before finishing, run challenge/full offline tests, source and document validators, `git diff --check`; inspect changed files for network/account/secret/PII paths. Report exact commands and branch/PR/worktree state.
