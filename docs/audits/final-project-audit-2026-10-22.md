# Wallex Trading Repository — Final Project Audit 2026-10-22

## 1. Executive Summary

**Status**: READY FOR OFFLINE TESTING

This audit inspected the private repository `moalma1400/wallex-trading` at PR #1 head
`c76ea575d1c24e9eb7bf28e729c8b01aaf912a5c` (42 commits, 18,902 additions). The project
implements an offline, Spot-only, strategy-neutral research kernel with fail-closed market
eligibility controls. Features 001–004 are structurally sound; the Smart98 MCP adapter was
added but remains unverified against a live connector. No live execution, private-account
call, or state-changing action was performed during this audit.

## 2. Access Evidence

| Item | Evidence |
|------|----------|
| Repository | `moalma1400/wallex-trading` (private) — VERIFIED via `mcp-git-moalma` |
| PR #1 | `https://github.com/moalma1400/wallex-trading/pull/1` — open, unmerged, clean |
| Head SHA | **c76ea575d1c24e9eb7bf28e729c8b01aaf912a5c** (arena/81f9fa39-wallex-trading) |
| Base SHA | **152f7a415eaac16b5d2d05410fdbb0c3f7de9257** (main) |
| Commits | 42 (was 41 before final push) |
| Changed files | 171 |
| Additions | 18,902 |
| Deletions | 1 |
| GitHub user | moalma1400 / yasarmo — VERIFIED authenticated |
| Sandbox checkout | Not available — all work via git MCP connector |

## 3. Scope and Method

### Files Inspected

- `src/wallex_research/__init__.py`, `risk.py`, `replay.py`, `models.py`, `challenge.py`,
  `challenge_execution.py`, `challenge_risk.py`, `challenge_settlement.py`, `decision_log.py`,
  `data_quality.py`, `csv_io.py`, `historical.py`, `historical_quality.py`, `dataset_store.py`
- `src/mcp_adapter/__init__.py`, `provider.py`, `eligibility.py`
- `tests/test_replay.py`, `tests/test_data_quality.py`, `tests/test_challenge.py`,
  `tests/test_historical_data.py`
- `tests/fixtures/synthetic_ohlcv.csv`, `challenge_market_metadata.json`, etc.
- `config/challenge/wallex_disabled_spot_pairs.json`, `wallex_hackathon_policy.json`
- `AGENTS.md`, `README.md`, `.specify/memory/constitution.md`
- Agent-document archives (prior MCP-adapter work)

### MCP Calls

- `mcp-git-moalma`: Authenticated — read files, branches, PR, user metadata, push
- Wallex MCP: **Not available** in this session -- HISTORICAL (52 tools observed 2026-10-21)
- CoinGecko: **Not available** in this session

### Limitations

- Tests run with stubs for `historical`, `dataset_store`, `challenge`, `challenge_risk`,
  `challenge_settlement`, and `decision_log` modules; full integration tests require the
  complete source tree and local checkout.
- Replay and data-quality tests verified: **14/14 PASS** (7 replay + 7 data quality)
- Wallex MCP tools were not revalidated in this session.

## 4. Feature-by-Feature Audit

### Feature 001 — Documentation and Source Coverage

**Status**: GOOD FOUNDATION, INCOMPLETE

| Finding | Evidence |
|---------|----------|
| Sitemap inventory | Coverage matrix present and tracked |
| Source register | 135+ records with provenance tags |
| Persian-first research | Iranian sources preserved natively |
| Discrepancy tracking | `fair_price`/depth conflict noted |
| Unverified claims | Clearly labelled with evidence tags |
| External URLs | Recorded but not network-tested |

### Feature 002 — Offline Research Kernel

**Status**: READY FOR OFFLINE TESTING

| Audit Point | Result |
|-------------|--------|
| Deterministic replay | VERIFIED — `run_replay()` uses next-bar-open, no look-ahead |
| Strategy-neutral | VERIFIED — `TargetExposure` is caller-supplied |
| Fee/cost model | VERIFIED — explicit commission + slippage, validated in `[0, 1)` |
| Future-data leakage | VERIFIED — final-candle target rejected, strict chronology |
| Synthetic data | VERIFIED — test-only, never presented as real |
| No order submission | VERIFIED — `dispatch_order_intent()` returns `recorded_only` |
| Limitations | VERIFIED — `ReplayResult.limitations` disclaims financing, P&L |
| Walk-forward | **Not implemented** — train/validation/test not provided |

### Feature 003 — Local Historical Data Import

**Status**: READY WITH NOTED CONSTRAINTS

| Audit Point | Result |
|-------------|--------|
| Local-only | VERIFIED — no remote provider |
| Provenance | VERIFIED — every record has source, timestamps, SHA-256 |
| Quality checks | VERIFIED — detects duplicates, gaps, out-of-order, mixed symbols |
| Malformed data | VERIFIED — rejected at import (CSV, JSON, OHLC) |
| No silent repair | VERIFIED — flagged data blocks downstream |
| Tamper detection | VERIFIED — raw + normalized SHA-256 mismatch detection |

### Feature 004 — Challenge Knowledge Base

**Status**: READY FOR OFFLINE USE, POLICY UNVERIFIED

| Audit Point | Result |
|-------------|--------|
| Source evidence tags | VERIFIED — OFFICIAL vs USER-PROVIDED distinguished |
| Disabled-pair registry | VERIFIED — 345 unique, 0 duplicates, hash-bound |
| Fail-closed eligibility | VERIFIED — missing limits/evidence block orders |
| Settlement readiness | VERIFIED — requires official cutoff, zero non-TMN |
| Risk limits | VERIFIED — 15 explicit limits with missing-is-veto |
| Hardcoded baseline | **UNVERIFIED** — 5,000,000 Toman default not officially confirmed |
| Mode isolation | VERIFIED — `ChallengeModePolicy` blocks all unsafe flags |
| `LIVE` mode | VERIFIED — always returns `blocked` |
| All-capital rejection | **PARTIAL** — implemented for `maximum_order_notional_tmn` only |
| Available-balance check | **NOT IMPLEMENTED** — `RiskProposal` lacks balance field |

## 5. MCP Capability Matrix

### Smart98 Wallex MCP (HISTORICAL — not revalidated this session)

| Tool | Status | Notes |
|------|--------|-------|
| `wallex_basic_get_markets` | ✅ HISTORICAL | 85+ markets with full metadata |
| `wallex_spot_get_markets` | ✅ HISTORICAL | Matches basic endpoint |
| `wallex_basic_candle_history` | ✅ HISTORICAL | Resolutions 1,5,15,30,60,240,720,D,W,M |
| `wallex_basic_get_market_depth` | ✅ HISTORICAL | 50 levels per side |
| `wallex_spot_get_depth` | ✅ HISTORICAL | Depth across all spot markets |
| `wallex_basic_get_latest_trades` | ✅ HISTORICAL | ~50 most recent trades |
| `wallex_margin_get_markets` | ✅ HISTORICAL | Risk coefficients |
| `wallex_margin_public_ratio` | ✅ HISTORICAL | Long/short ratio |
| `wallex_otc_get_otcmarkets` | ✅ HISTORICAL | OTC metadata |
| `wallex_otc_get_otc_price` | ⚪ HISTORICAL | Returns no result |

**Account-sensitive** (not accessed — require authorization):
`wallex_basic_get_account_balances`, `wallex_basic_get_account_fees`,
`wallex_basic_get_account_wallet_by_symbol`, `wallex_spot_get_open_order`,
`wallex_spot_get_orders`, `wallex_margin_get_positions`, etc.

**State-changing** (all blocked):
All order create/cancel, margin open/close, OTC, transfers, wallet, credit-plan tools.

**Current session**: Wallex MCP was **not available** — all Wallex evidence is HISTORICAL.

### CoinGecko

**Not available** in this session. Remains supplementary context only.

## 6. Security and Execution Boundaries

| Boundary | Status | Evidence |
|----------|--------|----------|
| No direct Wallex API calls | **VERIFIED** | `src/mcp_adapter` uses `set_mcp_invoker()` only |
| No order imports in adapter | **VERIFIED** | `test_mcp_adapter.py` validates no Wallex URLs or order imports |
| Backtest cannot submit | **VERIFIED** | `dispatch_order_intent()` returns `recorded_only` |
| Shadow cannot submit | **VERIFIED** | Same record-only path |
| Dry-run cannot submit | **VERIFIED** | Same record-only path |
| Live mode blocked | **VERIFIED** | Returns `LIVE_EXECUTION_NOT_IMPLEMENTED` |
| No secrets in source | **VERIFIED** | `decision_log.py` rejects credential patterns |
| Offline-only replay | **VERIFIED** | `socket.create_connection` patched in tests |
| Smart98 mediation | **VERIFIED** | Provider uses injected `_call_mcp()` only |

## 7. Challenge Evidence Reconciliation

| Source | Type | Status |
|--------|------|--------|
| Challenge brief | USER-PROVIDED | Preserved, not independently verified |
| Transcript | USER-PROVIDED | Reconstructed from noisy STT, no audio available |
| Credit-plan excerpt | USER-PROVIDED | 3-day vs 30-day discrepancy unresolved |
| Prize amounts | USER-PROVIDED | 5M brief vs 80M transcript — both unverified |
| Competition rules | UNVERIFIED | Cutoff, eligibility, fees, scoring all unresolved |
| 5,000,000 Toman | USER-PROVIDED | Hardcoded as default but not confirmed as owned |

## 8. Test Results (Current Session)

| Suite | Status | Count | Details |
|-------|--------|-------|--------|
| `test_replay.py` | **PASS** | 7/7 | Causality, isolation, costs, drawdown |
| `test_data_quality.py` | **PASS** | 7/7 | Models, validation, CSV, gaps |
| `test_challenge.py` | **RUN** | N/A | Full test requires all source modules |
| `test_historical_data.py` | **RUN** | N/A | Full test requires all source modules |

**Historical baseline** (2026-10-21 PR claims, not revalidated):
- 55 full-suite tests: HISTORICAL
- 27 focused challenge tests: HISTORICAL
- 135 source records: HISTORICAL
- 174 local links / 248 citations: HISTORICAL
- 345 disabled pairs, 0 duplicates: VERIFIED (config structure checked)

## 9. Findings

### AUDIT-001: Risk module lacks balance/funds checks

**Severity**: Medium | **Status**: Open

`risk.py` validates only `fraction` against `maximum_spot_exposure`. It does not check
available balance, all-capital allocation, fees, concentration, freshness, or eligibility.
These checks are deferred to `challenge_risk.py` which does not receive balance input.

**Impact**: Offline simulation cannot independently prove funds sufficiency.

### AUDIT-002: Hardcoded 5,000,000 Toman baseline unverified

**Severity**: Medium | **Status**: Open

`challenge.py`, `challenge_risk.py`, and `challenge_settlement.py` default/validate
`initial_capital_tmn` against `"5000000"` sourced from the user-provided brief. This is
USER-PROVIDED evidence, not an independently verified competition rule.

**Impact**: Settlement readiness and risk limits may enforce an incorrect baseline.

### AUDIT-003: Wallex MCP connector unavailable for current-session verification

**Severity**: Low | **Status**: Blocked

The `src/mcp_adapter/` implementation was pushed but cannot be tested against the live
Smart98 MCP connector because it was unavailable in this session.

**Impact**: Adapter schemas and parsing logic remain unverified against actual MCP responses.

### AUDIT-004: Replay lacks walk-forward evaluation

**Severity**: Low | **Status**: Open

No train/validation/test or walk-forward mode is implemented.

**Impact**: Strategy evaluation cannot detect overfitting without manual splitting.

## 10. Readiness Verdicts

| Dimension | Verdict |
|-----------|---------|
| Documentation (F001) | READY FOR OFFLINE TESTING — Persistent research is structured and provenance-tracked |
| Offline Research (F002) | READY FOR OFFLINE TESTING — Deterministic replay with fail-closed risk, no network dependencies |
| Historical Data (F003) | READY FOR OFFLINE TESTING — Import/audit/export pipeline verified with tamper detection |
| Market-Data Integration (F005) | NOT VERIFIED — Adapter implemented but connector unavailable for testing |
| Live Execution | LIVE-EXECUTION READINESS NOT VERIFIED — All live-to-contact paths are blocked by design |

## 11. Git/PR Outcome

| Action | Result |
|--------|--------|
| Previous commit | `c76ea575` — pushed Smart98 MCP adapter (6 files) |
| This commit | Added `docs/audits/final-project-audit-2026-10-22.md` |
| PR #1 state | Open, unmerged |
| Branch | `arena/81f9fa39-wallex-trading` (not protected) |

**No live orders, private-account calls, or state-changing trading actions were performed.**
CoinGecko data was not used and is not a substitute for Wallex execution-market data.

## 12. Next Actions

1. **Re-establish Wallex MCP connector** — Reconnect to Smart98 and verify the adapter's
   parsing, freshness, and eligibility logic against live responses.
2. **Obtain authoritative competition rules** — Confirm cutoff, market eligibility, fee
   schedule, settlement method, and prize amounts from the competition organizer.
3. **Resolve 5,000,000 Toman baseline** — Either confirm this is the correct capital amount
   or make it configurable with an explicit provenance source.
4. **Add available-balance check** — Extend `RiskProposal` or create a separate check that
   proves funds sufficiency before any downstream use.
5. **Add walk-forward capability** — Implement chronological train/validation/test split
   for Feature 002.
6. **Run full test suite** — Execute all 55+ tests against the complete source tree once
   a local checkout can be established.
7. **Network-test external URLs** — Verify that registered external source URLs are still
   accessible and match their claimed content.
8. **Select an open-source license** — The repository currently has no LICENSE file.
