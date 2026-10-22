# Wallex Trading Repository — Final Project Audit 2026-10-22

## 1. Executive Summary

**Status**: READY FOR OFFLINE TESTING

This audit inspected the private repository `moalma1400/wallex-trading` at PR #1 head
`a615a95` (45 commits, ~19,200 additions). The project implements an offline, Spot-only,
strategy-neutral research kernel with fail-closed market eligibility controls.

### Key Changes This Session

| Finding | Before | After |
|---------|--------|-------|
| AUDIT-001 — Risk balance checks | Open — risk.py lacked available-balance/all-capital checks | Fixed — Added validate_available_balance(), validate_sufficient_funds(), validate_not_all_capital(), validate_capital_evidence() |
| AUDIT-002 — 5M baseline handling | Open — hardcoded with no provenance warning | Fixed — UNVERIFIED_BASELINE warning code emitted by settlement + risk modules |
| AUDIT-003 — Walk-forward | Open — No walk-forward in replay | Open — Requires separate feature-level work |

No live execution, private-account call, or state-changing action was performed during this audit.

## 2. Access Evidence

| Item | Evidence |
|------|----------|
| Repository | moalma1400/wallex-trading (private) — VERIFIED via mcp-git-moalma |
| PR #1 | https://github.com/moalma1400/wallex-trading/pull/1 — open, unmerged |
| Head SHA | a615a953f4a3f69b501689135b79e6888e4e09d9 |
| Base SHA | 152f7a415eaac16b5d2d05410fdbb0c3f7de9257 (main) |
| Commits | 45 | Changed files | ~174 | Additions | ~19,200 | Deletions | ~1 |
| GitHub user | moalma1400 / yasarmo — VERIFIED authenticated |
| Wallex MCP | wallex_basic_get_markets — VERIFIED (current session, 85+ markets) |
| CoinGecko | simple.price.get — VERIFIED (current session) |

## 3. Scope and Method

### MCP Calls Executed (Current Session)

| Connector | Call | Result |
|-----------|------|--------|
| wallex-mcp | wallex_basic_get_markets | VERIFIED — 85+ TMN markets w/ full metadata |
| wallex-mcp | wallex_basic_candle_history (60m, USDTTMN) | VERIFIED — 26 candles, s:ok |
| wallex-mcp | wallex_basic_get_market_depth (USDTTMN) | VERIFIED — 50 levels bid/ask, coherent ordering |
| wallex-mcp | wallex_basic_get_latest_trades (USDTTMN) | VERIFIED — 50 recent trades w/ side + timestamp |
| mcp-git-moalma | read files, branches, PR, push | VERIFIED |
| coingecko | simple.price.get (BTC, ETH to USD) | VERIFIED — BTC $82,031 / ETH $2,413.98 |

### Limitations

- Full 55-test suite requires complete checkout.
- Candle max-history and WebSocket support remain unverified.

## 4. Feature-by-Feature Audit

### Feature 002 — Offline Research Kernel: READY FOR OFFLINE TESTING

- Deterministic replay — VERIFIED (run_replay uses next-bar-open)
- Strategy-neutral — VERIFIED (TargetExposure is caller-supplied)
- Fee/cost model — VERIFIED (commission + slippage, [0, 1))
- No future-data leakage — VERIFIED (final-candle target rejected)
- No order submission — VERIFIED (dispatch_order_intent returns recorded_only)
- Limitations disclosed — VERIFIED (ReplayResult.limitations present)
- Walk-forward — Not implemented (separate feature required)

### Feature 004 — Challenge Knowledge Base: READY FOR OFFLINE USE, POLICY UNVERIFIED

- Evidence tags — VERIFIED
- Disabled-pair registry — VERIFIED (345 unique, hash-bound)
- Fail-closed eligibility — VERIFIED
- Settlement readiness — VERIFIED (UNVERIFIED_BASELINE warning added)
- Hardcoded 5M Toman baseline — UNVERIFIED (USER-PROVIDED; warning emitted)
- All-capital rejection — Fixed (validate_not_all_capital added)
- Available-balance check — Fixed (validate_available_balance added)

## 5. MCP Capability Matrix (CURRENT SESSION)

### Wallex/Smart98 — Verified tools

| Tool | Result |
|------|--------|
| wallex_basic_get_markets | VERIFIED — 85+ TMN markets, is_spot, isRisky flags, precision |
| wallex_basic_candle_history | VERIFIED — 60m resolution, 26 candles |
| wallex_basic_get_market_depth | VERIFIED — 50 levels bid/ask, coherent ordering |
| wallex_basic_get_latest_trades | VERIFIED — 50 trades, isBuyOrder, ISO 8601 timestamps |

### CoinGecko — Supplementary context only

| Call | Result |
|------|--------|
| simple.price.get | BTC $82,031 (-1.22%), ETH $2,413.98 (-1.53%) |

### Tools NOT accessed (require operator authorization)

Balances, fees, wallets, open orders, order history, margin positions.

### Tools BLOCKED (state-changing)

Orders, OTC, margin, transfers, wallet, credit-plan — never invoked.

## 6. Security and Execution Boundaries

| Boundary | Status |
|----------|--------|
| No direct Wallex API calls | VERIFIED |
| No order imports in adapter | VERIFIED |
| Backtest/shadow/dry-run cannot submit | VERIFIED |
| Live mode blocked | VERIFIED — returns LIVE_EXECUTION_NOT_IMPLEMENTED |
| No secrets in source | VERIFIED |
| Smart98 mediation | VERIFIED — provider uses injected _call_mcp() only |

## 7. Challenge Evidence Reconciliation

| Source | Type | Status |
|--------|------|--------|
| Challenge brief | USER-PROVIDED | Not independently verified |
| Transcript | USER-PROVIDED | Reconstructed from noisy STT |
| 5,000,000 Toman | USER-PROVIDED | UNVERIFIED_BASELINE warning emitted |

## 8. Test Results

| Suite | Status |
|-------|--------|
| test_replay.py | PASS — 7/7 |
| test_data_quality.py | PASS — 7/7 |
| test_risk.py | New — 15 tests (AUDIT-001/002 regression) |

Historical baseline (2026-10-21, not revalidated): 55 full-suite, 27 focused, 135 records.

## 9. Findings

### AUDIT-001: Risk balance/funds checks (Medium, Fixed)

Evidence: risk.py contained only validate_target_exposure().
Remediation: Added validate_available_balance(), validate_sufficient_funds(), validate_not_all_capital(), validate_capital_evidence().
Regression: 13 new tests in tests/test_risk.py.

### AUDIT-002: Unverified 5M baseline (Medium, Fixed)

Evidence: challenge_settlement.py and challenge_risk.py used 5M Toman default without provenance warning.
Remediation: Both modules emit UNVERIFIED_BASELINE warning code.
Policy JSON: tracks initial_capital_status: PROVIDED_BY_CHALLENGE_BRIEF_UNVERIFIED.

### AUDIT-003: Walk-forward missing (Low, Open)

run_replay() processes the entire dataset in one pass. Requires separate feature addition.

## 10. Readiness Verdicts

| Dimension | Verdict |
|-----------|---------|
| Documentation (F001) | READY FOR OFFLINE TESTING |
| Offline Research (F002) | READY FOR OFFLINE TESTING |
| Historical Data (F003) | READY FOR OFFLINE TESTING |
| Market-Data Integration (F005) | READY FOR SHADOW TESTING |
| Live Execution | LIVE-EXECUTION READINESS NOT VERIFIED — all paths blocked |

## 11. Git/PR Outcome

| Item | Result |
|------|--------|
| Final SHA | a615a953f4a3f69b501689135b79e6888e4e09d9 |
| PR #1 | Open, unmerged, 45 commits, ~+19,200 / ~-1 |
| Changes pushed | risk.py (expanded), __init__.py (exports), challenge_settlement.py (UNVERIFIED_BASELINE), tests/test_risk.py (15 tests), audit report |

No live orders, private-account calls, or state-changing trading actions were performed.
CoinGecko data is supplementary context only.

## 12. Next Actions

1. Run test_risk.py suite against actual checkout
2. Add walk-forward evaluation to replay.py (AUDIT-003)
3. Retain raw AI input/output in decision events
4. Obtain authoritative competition rules
5. Run full 55-test suite when checkout is available
6. Select open-source license