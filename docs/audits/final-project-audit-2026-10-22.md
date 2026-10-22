# Wallex Trading Repository — Readiness Review (2026-10-22)

## Scope and evidence boundary

This refresh started from the existing PR #1 head `5d114883fe01a5bb09340cfb75adc560dfa061d4` on `arena/81f9fa39-wallex-trading`. Review and validation used repository code, tests, fixtures, and local validators only. No MCP discovery/connection, Smart98 or Wallex market-data call, private-account access, or state-changing action was performed. No direct REST fallback was used. The checked-in MCP and market-data fixtures are synthetic test inputs, not live observations or provenance evidence.

The 5,000,000-TMN value appearing in the challenge policy and helper defaults is not verified capital. Challenge capital, account balance, credit liability, fees, and permissions remain unresolved. The challenge material is user-provided and is not independently established as official.

## Caller-path and risk-control findings

| Area | Repository finding |
|---|---|
| Replay caller | `run_replay()` consumes caller-supplied `TargetExposure`; there is no strategy/signal generator. It checks the configured Spot maximum and now also calls the shared `validate_not_all_capital()` policy. |
| Challenge-risk caller | `evaluate_challenge_risk()` is a public gate with no production caller found. It now applies the same inclusive 99% all-capital threshold to `total_deployed_after_tmn / initial_capital_tmn`, but only after capital provenance/value validation succeeds. |
| Boundary | `ALL_CAPITAL_THRESHOLD = Decimal("0.99")`; the established `>=` semantics are retained. Below-boundary exposure is not rejected by this rule; exactly 0.99 and above are rejected. Replay does not silently clamp. |
| Unverified capital | Capital-relative limit comparisons and exposure-ratio decisions are skipped unless evidence is valid. An unresolved/default 5,000,000-TMN value cannot decide policy. The unresolved baseline and other missing evidence still fail closed. |
| Execution | `dispatch_order_intent()` is record-only for BACKTEST/SHADOW/DRY_RUN and blocks LIVE with `LIVE_EXECUTION_NOT_IMPLEMENTED`. No order submission adapter or live path is implemented. |

Caller-level regressions cover below, exactly at, and above the 0.99 boundary in both replay and challenge risk; they also check valid below-boundary behavior, synthetic-evidence opt-in, and that unresolved default capital does not trigger capital-relative policy comparisons. The boundary fixture capital is explicitly synthetic and test-only.

## Data, strategy, and simulation review

- No production historical dataset or local market-data store is tracked in the repository. Available OHLCV and market examples are synthetic fixtures; no historical performance run is justified by them.
- Feature 003 imports only caller-provided local CSV/JSON. It preserves raw bytes with hashes, requires explicit provenance/timezone/context, audits against a caller-supplied policy, and gates replay export. It does not fetch market data.
- `run_replay()` uses caller-supplied exposure decisions and executes a close-time decision at the next candle's open. This avoids same-bar lookahead for that interface, but does not establish the causality or quality of any absent strategy. Its deterministic fill model uses caller-configured generic commission and slippage assumptions, cash affordability, and candle prices. There is no separately modeled spread, order-book execution, liquidity/market-impact model, or official fee inference. Results are arithmetic simulation outputs only, not profitability evidence.
- Replay limitations explicitly exclude credit-plan accrual/liquidation, account permissions, challenge settlement, principal/repayment liabilities, and final payout reconciliation. Manual activity is not algorithmic performance.

## Smart98 boundary

The repository adapter defines an injected invoker seam and parser/provider methods for `wallex_basic_get_markets`, `wallex_basic_candle_history`, `wallex_basic_get_market_depth`, and `wallex_basic_get_latest_trades`. Local tests use synthetic fixtures. The adapter is not connected to a live MCP client in this repository, and no production data-to-strategy-to-risk-to-audit orchestrator was found. Parsing tests establish behavior on fixtures, not actual Smart98 schemas, source-time semantics, permissions, freshness, availability, or current tool responses.

`docs/smart98_mcp_capability_matrix.md` contains a dated historical status snapshot. Its past check marks are not evidence of current tool availability or a test performed in this review. Do not describe Smart98 as verified end-to-end or use adapter output for decisions until the evidence below is supplied.

**Read-only public evidence request (no private or state-changing tools):** For a user-selected candidate Spot symbol and explicit UTC historical interval, provide the raw Smart98 MCP request and response (or exact error) for `wallex_basic_get_markets` (no arguments), `wallex_basic_candle_history` (`symbol`, `resolution`, `from`, `to` as sent), `wallex_basic_get_market_depth` (`symbol`), and `wallex_basic_get_latest_trades` (`symbol`). For each invocation include: (1) tool name and exact input; (2) UTC observation time at the caller; (3) market/symbol; (4) raw source timestamp(s), timezone/unit, and documented meaning—or an explicit statement that none is present; (5) exact input/output schema or version and unmodified result payload; (6) documented freshness/retention semantics and how they were established; and (7) transport/tool errors, truncation, pagination, or permission denials. Redact credentials and private/account data. Do not call private or state-changing tools. Without this evidence, keep market integration unverified.

## Offline validation

All checks below completed after this revision's code and documentation changes:

- `PYTHONPATH=src .venv/bin/python -m pytest -q` — **145 passed, 24 subtests passed**.
- `python3 scripts/validate_sources.py` — **135 records; 135 unique IDs and URLs**; status counts: 6 blocked, 5 in progress, 51 not started, 73 reviewed.
- `python3 scripts/validate_doc_links.py` — **179 local Markdown links resolved; 248 source citations matched registered IDs and exact URLs**. Network links were not tested.
- `PYTHONPATH=src python3 -m compileall -q src tests` — passed.
- `git diff --check` — passed.

No strategy backtest, profitability, current-market, live-data, or shadow result is reported. Backtest, shadow, and dry-run behavior cannot establish live readiness.

## Separate readiness verdicts

| Readiness dimension | Verdict |
|---|---|
| Offline validation | **Repository checks only.** The offline kernel validates caller-supplied data/decisions under explicit assumptions; a strategy and historical performance are not established. |
| Shadow eligibility | **NOT VERIFIED / NOT RUN.** There is no implemented strategy or complete validated data → decision → risk → audit pipeline, and no current Smart98 evidence. |
| Live execution | **LIVE-EXECUTION READINESS NOT VERIFIED.** LIVE remains blocked. Official challenge rules, verified capital/balance and liabilities, account permissions, explicit authorization, an approved order-tool contract, and deterministic execution/reconciliation controls are not independently evidenced. |

## Follow-ups

Feature 005 work requiring an authoritative Smart98 contract, source-time/freshness semantics, security/compliance evidence, and decision-grade data remains open. Preserve Spot-only scope, the raw disabled-market registry, fail-closed eligibility, and the separation of challenge allocation from owned or withdrawable assets. PR #1 remains the target; this review does not merge it.
