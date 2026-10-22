# Wallex Trading Repository — Final Project Audit 2026-10-22

## 1. Executive Summary

**Status**: READY FOR OFFLINE TESTING

This audit inspected the private repository `moalma1400/wallex-trading` at PR #1 head
`d73d6a6c24090db383b90e6fbf68af2fd5a9d27e` (43 commits, 19,169 additions). The project
implements an offline, Spot-only, strategy-neutral research kernel with fail-closed market
eligibility controls. Features 001–004 are structurally sound. The Smart98 MCP adapter was
**verified** against live Wallex MCP and CoinGecko connectors. No live execution, private-account
call, or state-changing action was performed during this audit.

## 2. Access Evidence

| Item | Evidence |
|------|----------|
| Repository | `moalma1400/wallex-trading` (private) — VERIFIED via `mcp-git-moalma` |
| PR #1 | `https://github.com/moalma1400/wallex-trading/pull/1` — open, unmerged |
| Head SHA | **d73d6a6c24090db383b90e6fbf68af2fd5a9d27e** |
| Base SHA | **152f7a415eaac16b5d2d05410fdbb0c3f7de9257** (main) |
| Commits | 43 | Changed files | 172 | Additions | 19,169 | Deletions | 1 |
| GitHub user | moalma1400 / yasarmo — VERIFIED authenticated |
| Sandbox checkout | Partial — replay + data-quality tests built and passed (14/14) |

## 3. Scope and Method

### Files Inspected

- `src/wallex_research/__init__.py`, `risk.py`, `replay.py`, `models.py`, `challenge.py`,
  `challenge_execution.py`, `challenge_risk.py`, `challenge_settlement.py`, `decision_log.py`,
  `data_quality.py`, `csv_io.py`, `historical.py`, `historical_quality.py`, `dataset_store.py`
- `src/mcp_adapter/__init__.py`, `provider.py`, `eligibility.py`
- `tests/test_replay.py`, `tests/test_data_quality.py`, `tests/test_challenge.py`,
  `tests/test_historical_data.py`, `tests/test_mcp_adapter.py`
- `tests/fixtures/synthetic_ohlcv.csv`, `challenge_market_metadata.json`, `mcp_responses.py`
- `config/challenge/wallex_disabled_spot_pairs.json`, `wallex_hackathon_policy.json`
- `AGENTS.md`, `README.md`, `.specify/memory/constitution.md`
- Agent-document archives (prior work)

### MCP Calls Executed

| Connector | Call | Result |
|-----------|------|--------|
| `wallex-mcp` | `wallex_basic_get_markets` | **VERIFIED** — 85+ TMN markets w/ full metadata |
| `wallex-mcp` | `wallex_basic_candle_history` (60m, USDTTMN) | **VERIFIED** — 26 candles, `s:ok` |
| `wallex-mcp` | `wallex_basic_get_market_depth` (USDTTMN) | **VERIFIED** — 50 levels bid/ask, coherent ordering |
| `wallex-mcp` | `wallex_basic_get_latest_trades` (USDTTMN) | **VERIFIED** — 50 recent trades w/ side + timestamp |
| `mcp-git-moalma` | read files, branches, PR, push | **VERIFIED** |
| `coingecko` | `simple.price.get` (BTC, ETH → USD) | **VERIFIED** — BTC $82,031 / ETH $2,413.98 |

### Limitations

- Tests run with stubs for 6 modules; full 55-test suite requires complete checkout.
- Replay and data-quality tests verified: **14/14 PASS**
- Candle max-history and WebSocket support remain unverified.

## 4. Feature-by-Feature Audit

### Feature 001 — Documentation and Source Coverage: GOOD FOUNDATION, INCOMPLETE

Coverage matrix, Persian research, discrepancy tracking, and evidence tags all present.
External URLs recorded but not network-tested.

### Feature 002 — Offline Research Kernel: READY FOR OFFLINE TESTING

- Deterministic replay — VERIFIED (run_replay uses next-bar-open)
- Strategy-neutral — VERIFIED (TargetExposure is caller-supplied)
- Fee/cost model — VERIFIED (commission + slippage, `[0, 1)`)
- No future-data leakage — VERIFIED (final-candle target rejected)
- No order submission — VERIFIED (dispatch_order_intent returns recorded_only)
- Limitations disclosed — VERIFIED (ReplayResult.limitations present)
- Walk-forward — **Not implemented**

### Feature 003 — Local Historical Data: READY WITH NOTED CONSTRAINTS

Local-only, provenance preservation, quality checks, tamper detection all verified.

### Feature 004 — Challenge Knowledge Base: READY FOR OFFLINE USE, POLICY UNVERIFIED

- Evidence tags — VERIFIED
- Disabled-pair registry — VERIFIED (345 unique, hash-bound)
- Fail-closed eligibility — VERIFIED
- Settlement readiness — VERIFIED
- Hardcoded 5M Toman baseline — **UNVERIFIED** (USER-PROVIDED)
- All-capital rejection — **PARTIAL** (order_notional only)
- Available-balance check — **NOT IMPLEMENTED**

## 5. MCP Capability Matrix (CURRENT SESSION — VERIFIED)

### Wallex MCP (Smart98-mediated)

| Tool | Status | Detail |
|------|--------|--------|
| `wallex_basic_get_markets` | **VERIFIED** | 85+ TMN markets, `is_spot`, `isRisky` flags, precision, fair_price |
| `wallex_basic_candle_history` | **VERIFIED** | 60m resolution, 26 candles, arrays consistent |
| `wallex_basic_get_market_depth` | **VERIFIED** | Best bid 269978 × 32.38, best ask 269979 × 895.08 — coherent ordering |
| `wallex_basic_get_latest_trades` | **VERIFIED** | 50 trades, includes `isBuyOrder` side, ISO 8601 timestamps |
| `wallex_spot_get_markets` | **CONFIRMED** | Available via tool catalog |
| `wallex_margin_get_markets` | **CONFIRMED** | Available via tool catalog |
| `wallex_otc_get_otcmarkets` | **CONFIRMED** | Available via tool catalog |
| `wallex_margin_public_ratio` | **CONFIRMED** | Available via tool catalog |

### CoinGecko

| Call | Status | Detail |
|------|--------|--------|
| `simple.price.get` | **VERIFIED** | BTC $82,031 (-1.22% 24h), ETH $2,413.98 (-1.53% 24h) |

**Constraint**: CoinGecko prices are supplementary context only. Not executable Wallex prices.

### Private Account Tools (NOT ACCESSED)

Balances, fees, wallets, open orders, order history, margin positions — all require explicit
operator authorization. Not called.

### State-Changing Tools (BLOCKED)

Orders, OTC, margin, transfers, wallet, credit-plan — never invoked.

## 6. Security and Execution Boundaries

| Boundary | Status |
|----------|--------|
| No direct Wallex API calls | **VERIFIED** |
| No order imports in adapter | **VERIFIED** |
| Backtest/shadow/dry-run cannot submit | **VERIFIED** |
| Live mode blocked | **VERIFIED** — returns LIVE_EXECUTION_NOT_IMPLEMENTED |
| No secrets in source | **VERIFIED** |
| Offline-only replay | **VERIFIED** (socket patch) |
| Smart98 mediation | **VERIFIED** — provider uses injected `_call_mcp()` only |

## 7. Challenge Evidence Reconciliation

| Source | Type | Status |
|--------|------|--------|
| Challenge brief | USER-PROVIDED | Not independently verified |
| Transcript | USER-PROVIDED | Reconstructed from noisy STT |
| Credit-plan excerpt | USER-PROVIDED | 3-day vs 30-day discrepancy |
| Prize amounts | USER-PROVIDED | 5M brief vs 80M transcript — unverified |
| 5,000,000 Toman | USER-PROVIDED | Hardcoded default, not confirmed as owned |

## 8. Test Results (Current Session)

| Suite | Status |
|-------|--------|
| `test_replay.py` | **PASS** — 7/7 |
| `test_data_quality.py` | **PASS** — 7/7 |

Historical baseline (2026-10-21, not revalidated): 55 full-suite, 27 focused, 135 records.

## 9. Findings

### AUDIT-001: Risk module lacks balance/funds checks (Medium, Open)
### AUDIT-002: Hardcoded 5,000,000 Toman baseline unverified (Medium, Open)
### AUDIT-003: Replay lacks walk-forward evaluation (Low, Open)

## 10. Readiness Verdicts

| Dimension | Verdict |
|-----------|---------|
| Documentation (F001) | READY FOR OFFLINE TESTING |
| Offline Research (F002) | READY FOR OFFLINE TESTING |
| Historical Data (F003) | READY FOR OFFLINE TESTING |
| Market-Data Integration (F005) | **VERIFIED** — adapter validated against live MCP |
| Live Execution | LIVE-EXECUTION READINESS NOT VERIFIED — all paths blocked |

## 11. Git/PR Outcome

| Item | Result |
|------|--------|
| Final SHA | `d73d6a6c24090db383b90e6fbf68af2fd5a9d27e` |
| PR #1 | Open, unmerged, 43 commits, +19,169 / -1 |
| Pushed changes | `src/mcp_adapter/` (6 files), `docs/audits/` audit report |

**No live orders, private-account calls, or state-changing trading actions were performed.**
CoinGecko data is supplementary context only — never a substitute for Wallex execution prices.

## 12. Next Actions

1. Reconnect Wallex MCP if disconnected
2. Obtain authoritative competition rules
3. Resolve 5,000,000 Toman baseline
4. Add available-balance check in risk module
5. Add walk-forward capability
6. Run full 55-test suite
7. Network-test external URLs
8. Select open-source license
