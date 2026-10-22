# Wallex Trading Repository — Readiness Review (2026-10-22)

## Scope and evidence boundary

This refresh started from PR #1 remote head `70a1f146d9b8eec5c7e541c2fe48f84163c1f22f` on `arena/81f9fa39-wallex-trading`; PR #1 was verified OPEN and unmerged before edits. The checkout had been fast-forwarded to that head. This review used repository code, fixtures, and offline validators/tests only. It made no Smart98 connector discovery, Smart98/Wallex/other market-data call, private-account access, or state-changing action.

The prior version of this report recorded read-only Smart98/Wallex observations as “current session” evidence at an earlier commit. Those are historical repository claims for this refresh, not runtime checks repeated here. The checked-in MCP fixtures are synthetic test inputs, not authenticated source records. No challenge brief or credit-plan example was treated as proof of capital, terms, permissions, or authorization.

## Decision-path findings

| Area | Current finding |
|---|---|
| Strategy | No strategy/signal generator exists. `run_replay()` consumes caller-supplied `TargetExposure`; no strategy is selected or evaluated. |
| Data-to-decision wiring | Smart98 adapter parsing, adapter eligibility, challenge eligibility, challenge risk, decision logging, replay, and the record-only dispatcher are separate components. No production orchestrator connects a validated Smart98 observation through a strategy, eligibility/risk veto, audit record, and replay/dispatch. |
| Risk callers | `validate_available_balance()` and `validate_capital_evidence()` are helpers. `evaluate_challenge_risk()` is not called by the record-only dispatcher. `run_replay()` does call `validate_target_exposure()` on supplied offline targets. |
| Execution | `dispatch_order_intent()` records offline intents only; LIVE returns `LIVE_EXECUTION_NOT_IMPLEMENTED`. No order adapter or live submission path exists in this feature. |
| Source freshness | Local MCP receipt time is not treated as source-event time. The repository fixtures do not prove source timestamps, live tool schemas, permissions, or current runtime availability; missing source time remains unknown and is blocked by eligibility/risk gates. |

## Confirmed defects fixed in this refresh

- Removed an extra opening triple quote in `src/wallex_research/__init__.py` that caused package import and test collection to fail.
- Made available-funds checks require explicit known/verified flags and a numeric amount; a caller flag can no longer make `None` pass. Capital evidence now requires a positive amount and traceable source identifier.
- Made `evaluate_challenge_risk()` block an unresolved baseline and missing, unverified, unprovenanced, or insufficient available balance. Non-synthetic evidence requires an explicit `OFFICIAL_SOURCE_VERIFIED` status and source ID, HTTPS URL, and SHA-256 reference. Synthetic evidence clears these local test gates only with an explicit fixture opt-in. Proposals now declare a side; sells block until base-asset balance/fee validation is implemented.
- Made settlement readiness block an unverified 5,000,000-TMN baseline; a warning alone no longer produces `ready=True`. Synthetic cutoff/valuation fixtures do not clear this capital-baseline blocker, even under the explicit fixture flag.
- Fixed the adapter market gate's fail-open behavior: an absent competition-specific allow-list, unknown Spot/market-type state, missing source-event timestamp, stale/future source time, or `isRisky` flag does not produce `ELIGIBLE`.
- Removed silent candle sorting/deduplication and warning-only gap handling. Empty, malformed, invalid-OHLCV, duplicate, out-of-order, mixed-interval, and gapped candle data now fails closed. Ticker parsing no longer fabricates bid/ask from last price; order-book sides are validated for positive levels, order, and crossed books.
- Corrected existing review Skills to retain the source-time boundary, fail-closed requirements, caller tracing, and strategy-neutral replay scope.

## Offline validation

Executed after the code changes (using synthetic/local inputs only):

- `PYTHONPATH=src .venv/bin/python -m pytest -q` — **142 passed, 19 subtests passed**.
- `python3 scripts/validate_sources.py` — **135 records; 135 unique IDs and URLs**; research status counts: 6 blocked, 5 in progress, 51 not started, 73 reviewed.
- `python3 scripts/validate_doc_links.py` — **178 local Markdown links resolved; 248 source citations matched registered IDs and exact URLs**. Network targets were not tested.
- `PYTHONPATH=src python3 -m compileall -q src tests` — passed.
- `git diff --check` — passed after removing one trailing-whitespace issue.

No strategy backtest or performance result is reported: the code has no strategy generator, and the local fixture data is synthetic and insufficient to establish strategy performance. Existing replay tests validate arithmetic and causality for caller-supplied signals only.

## Separate readiness verdicts

| Readiness dimension | Verdict |
|---|---|
| Offline research engine | **Available for offline, caller-supplied data/decisions and explicit assumptions; strategy readiness not established.** |
| Market-data integration | **Fixture-tested adapter implementation only. Current Smart98 runtime/tool contract and source-time evidence were not independently reverified; not decision-grade on this evidence.** |
| Shadow evaluation | **NOT VERIFIED / NOT RUN.** No implemented strategy or end-to-end data→decision→risk→audit pipeline is present. |
| Live execution | **LIVE-EXECUTION READINESS NOT VERIFIED.** Live remains blocked; authoritative challenge rules, verified capital/account permissions, explicit authorization, approved order-tool contract, and deterministic order/reconciliation controls are not independently established. |

## Repository follow-ups

Feature 005 tasks T003–T006 remain open where the required authoritative contract, security/compliance evidence, and decision-grade data semantics are not established. Do not infer their completion from fixture tests or prior report entries. PR #1 remains the only target; this review does not merge it.
