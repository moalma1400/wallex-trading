# User-supplied Smart98 MCP Tool Evidence Report — 2026-10-22

**Source classification:** User-supplied report text describing observations attributed to Smart98/MCP. Arena did not independently invoke or verify any MCP tools. The classifications below are preserved as the report's claims, not promoted to Arena-verified facts.

**Preservation note:** The report text beginning at the next horizontal rule is transcribed from the user's message. No raw MCP request/response, server export, or original Smart98 report file was supplied separately; this archive's SHA-256 identifies this Markdown file only. The report's PR #1 status is preserved exactly as supplied; current repository inspection shows PR #1 is merged.

**Safety boundary:** Tool names, including private-account and state-changing tools listed for classification, are evidence text only. They do not authorize tool use. No credentials, private data, direct Wallex requests, MCP invocations, or state-changing operations were performed by Arena.

---

# Feature 005 Task T003 — MCP Tool Evidence Report

**Repository**: `moalma1400/wallex-trading` (private) · **PR #1**: `arena/81f9fa39-wallex-trading` (open, unmerged)
**Date (UTC)**: 2026-10-22 · **Evidence gathered**: live invocation of public read-only tools this session + observed tool definitions
**Status**: **EVIDENCE GATHERED — T003 NOT DECLARED COMPLETE** (gaps remain; see §9)

---

## 1. Available relevant MCP servers and tools

Three MCP connectors are present and accessible in the current session environment. No connector was installed or configured; only existing, authorized connections were used, and only public read-only operations were invoked.

| Server | Role | Tools | Used this session |
|--------|------|-------|-------------------|
| `wallex-mcp` | Wallex market data exposed via Smart98 (mandatory mediation layer) | ~52 tools | Yes — 9 public reads |
| `coingecko-traider-mcp` | Supplementary aggregated market context | 2 tools | No (verified in prior session) |
| `mcp-git-moalma` | GitHub repository operations (PR, files) | 46 tools | Yes — reads/push (repo ops only) |

No other MCP connectors were enabled. Attempts to enable additional connectors would require owner installation/configuration and were **not** performed.

---

## 2 & 3. Tool definitions, schemas, and source evidence

Definitions below are transcribed from the tool schemas as exposed by the `wallex-mcp` connector at session time. Descriptions are preserved verbatim; parameters are from the declared schemas. **Server/definition version is not exposed by the environment — marked `UNKNOWN`.**

### 2.1 Public read-only Wallex tools (invoked this session — VERIFIED)

| Tool | Description (from definition) | Input schema | Output observed |
|------|-------------------------------|--------------|-----------------|
| `wallex_basic_get_markets` | List all Wallex markets using the basic-services market endpoint | `{}` | `result.markets[]`: `symbol`, `base_asset`, `quote_asset`, prices, `is_spot`, `is_otc`, `is_margin`, `flags` (`isRisky`), `amount_precision`, `price_precision`, `leverage_step`, `created_at`, `fair_price{bid,ask,spot,margin_limit,...}`, `change_24h`, `volume_24h`, `quote_volume_24h`, `highest_24h_price`, `lowest_24h_price`, `is_market_type_enable`, `otc_min/max_notional`, `en/fa` labels |
| `wallex_spot_get_markets` | List all Wallex markets using the spot-trading market endpoint | `{}` | Same market object shape as basic endpoint; **85+ markets returned, only spot-capable universe union** |
| `wallex_basic_candle_history` | Retrieve public OHLCV candles for one market symbol, resolution, and Unix time range | `symbol` (e.g. `USDTTMN`), `resolution` (`1,5,15,30,60,240,720,D,W,M`), `from` (int64 Unix s), `to` (int64 Unix s) | `s:"ok"`, parallel arrays `t[]` (Unix seconds), `o/h/l/c[]` (decimal strings), `v[]` (string) |
| `wallex_basic_get_market_depth` | Get current bid and ask depth for one market symbol | `symbol` | `result.ask[]`, `result.bid[]` — 50 levels per side; each `{price, quantity, sum}`; `message`, `success:true` |
| `wallex_basic_get_latest_trades` | List the most recent public trades executed for one market symbol | `symbol` | `result.latestTrades[]`: `{symbol, quantity, price, sum, isBuyOrder(bool), timestamp(ISO 8601 UTC)}`; 50 records |
| `wallex_otc_get_otcmarkets` | List markets currently available for over-the-counter trading | `{}` | `result.{SYMBOL}` objects: `stepSize`, `tickSize`, `minQty`, `minNotional`, `maxNotional`, `stats{lastPrice,24h_ch,24h_volume,...}`, `buyStatus/sellStatus/exchangeStatus` (`ENABLE`/`DISABLE`), `flags` incl. `isRisky`, icon URLs |
| `wallex_margin_get_markets` | List public markets currently enabled for margin trading | `{}` | `result[]`: `{symbol, base, quote, min_risk_coef, max_risk_coef, risk_coef_step, liquidity_margin, max_age}`; e.g. `USDTTMN`, `BTCTMN`, `BTCUSDT` … |
| `wallex_margin_public_ratio` | Get the public ratio of long versus short margin positions for one market symbol | `market` (e.g. `USDTTMN`) | `result{long_percents, short_percents}` — observed `70/30` this session |
| `wallex_otc_get_otc_price` | Get the current OTC quote for buying or selling one asset symbol | `symbol`, `side` (`BUY`/`SELL`) | **Known limitation**: returned `no result returned` in prior session; not retried this session → `NOT_AVAILABLE` for effective use |

Additional public tool **not invoked this session** (schema only, previously confirmed available):
`wallex_spot_get_depth` — "Retrieve current bid and ask depth for every spot market in one response", `{}`.

### 3.1 Source/version evidence

| Item | Evidence | Classification |
|------|----------|----------------|
| Connector identity | `wallex-mcp` exposed through the session environment (Smart98-medited) | VERIFIED |
| Tool names & schemas | Observed directly in session tool definitions; matches prior `2026-10-21` capability matrix (52 tools) | VERIFIED |
| Wallex upstream REST host | Referenced transitively (market icon URLs point to `api.wallex.ir/coins/*.png`); **no direct REST call made** | OBSERVED (indirect) |
| Tool-definition version / MCP server version | Not exposed by the environment | UNKNOWN |
| Smart98 ↔ Wallex compatibility/auth contract | Not independently documented; mediation requirement is project policy | UNKNOWN |

**No credentials, tokens, cookies, or private data were disclosed in this report or during tool calls.**

---

## 4. Tools that demonstrably support public, read-only Wallex Spot market data

| Data needed by T003 | Tool | Evidence |
|---------------------|------|----------|
| Symbols / market list | `wallex_basic_get_markets`, `wallex_spot_get_markets` | **VERIFIED** — live payload with 85+ TMN markets, `is_spot` flags, precision |
| Ticker (price, 24h change, high/low, volume) | `wallex_basic_get_markets` (`price`, `change_24h`, `change_7D`, `highest/lowest_24h_price`, `volume_24h`, `quote_volume_24h`), `fair_price{bid,ask}` reference | **VERIFIED** |
| Candles (OHLCV) | `wallex_basic_candle_history` | **VERIFIED** — 60m USDTTMN candles, Unix-second timestamps, string decimals, `s:"ok"` |
| Order book | `wallex_basic_get_market_depth` (single), `wallex_spot_get_depth` (all, catalog-only) | **VERIFIED** for single-symbol; `wallex_spot_get_depth` UNVERIFIED this session |
| Recent trades | `wallex_basic_get_latest_trades` | **VERIFIED** — `isBuyOrder`, ISO 8601 UTC timestamps |
| OTC metadata (not Spot execution) | `wallex_otc_get_otcmarkets` | VERIFIED as OTC, not Spot |
| Margin market metadata (not Spot) | `wallex_margin_get_markets` | VERIFIED as margin, not Spot |

**Caution (fail-closed)**: A market's presence (e.g. `is_spot:true`) is *not* proof of orderability or permission. `is_market_type_enable` (observed `true` only for `BTCTMN`, `ETHTMN`, `USDTTMN`, `XAUTTMN`, `PEPETMN`, `SOLTMN`… vs `false` for most) and OTC `buyStatus/sellStatus/exchangeStatus` (e.g. `XLMTMN` buy=DISABLE, `MOGTMN` sell=DISABLE) must be treated as mandatory eligibility gates. `flags:["isRisky"]` is an explicit risk block (e.g. `PUMPTMN`, `MOGTMN`, `SANDTMN`, `FLOWTMN`, `DEXEUSDT`, `PNUTUSDT`).

Discrepancy worth recording in `docs/research/discrepancies.md`: `fair_price.bid == fair_price.ask` (a mid reference) in market payloads while order-book depth exposes separate best bid/ask per side — do not use `fair_price` as an executable quote.

---

## 5. Authentication & permission requirements (no secret values)

| Tool class | Requirement |
|------------|-------------|
| Public read-only tools (§2.1) | Invoked without account credentials; endpoint-level auth not required for market data. |
| Private-account reads (§7.1) | Explicit operator authorization required by project policy; **not called**. |
| State-changing tools (§7.2) | **Prohibited** under all circumstances in this project; never invoked. |
| Smart98 mediation | Project policy: all Wallex access must go through Smart98; direct Wallex REST is not a fallback. |
| Evaluated permissions | Only public read-only was exercised; any account/permission/order capability remains UNVERIFIED. |

---

## 6. Data semantics, freshness, pagination, limits, timeouts, errors

| Attribute | Observed / known | Classification |
|-----------|------------------|----------------|
| Candle timestamps | Unix seconds (`1733425200`); OHLCV as decimal strings | VERIFIED |
| Trade timestamps | ISO 8601 UTC (`2026-10-22T12:18:04Z`) | VERIFIED |
| Depth ordering | Asks ascending, bids descending; 50 levels per side | VERIFIED |
| Numeric representation | Prices/quantities as decimal strings or numbers; preserve exact string form for decimals | VERIFIED |
| Freshness guarantees | None published by the connector; must be measured by the adapter (staleness gates in `mcp_adapter`: ticker 60s, book 30s, candles 300s) | UNKNOWN upstream / configurable locally |
| Pagination | Markets/depth/trades: none exposed in observed schemas; order-history tools have `page`/`per_page` (not invoked) | UNKNOWN for market data |
| Rate limits | Not documented in observed definitions | UNKNOWN |
| Timeout behavior | Not documented; adapter defines its own timeout semantics | UNKNOWN |
| Error semantics | Partial: `s` status (`ok`) and `success` + `message` fields; `wallex_otc_get_otc_price` silently returns nothing | PARTIAL |
| Candle max-history range | Not probed this session | UNKNOWN (must be bounded by adapter) |
| WebSocket/streaming | No evidence of availability | UNKNOWN |

---

## 7. Tool classification (definitions only for private/state-changing; never invoked)

### 7.1 Private-account reads (require explicit operator authorization — NOT called)

`wallex_basic_get_account_balances` · `wallex_basic_get_account_fees` · `wallex_basic_get_account_wallet_by_symbol` · `wallex_basic_get_account_ibans` · `wallex_basic_get_account_card_numbers` · `wallex_spot_get_open_order` · `wallex_spot_get_orders` · `wallex_spot_get_orders_client` · `wallex_margin_get_positions` · `wallex_margin_get_position_id` · `wallex_margin_get_orders` · `wallex_margin_get_levels` / `_market` · `wallex_margin_get_pnl` · `wallex_margin_profit_position_id` · `wallex_margin_detailed_information` · `wallex_margin_calculate_loan` · `wallex_credit_active_sub_accounts_list` · `wallex_credit_sub_account_balances_details` · `wallex_credit_sub_account_transfer` · `wallex_credit_active_user_package_details` · `wallex_credit_user_package_history_list` · `wallex_credit_user_package_history_details` · prop-package eligibility/overview helpers

### 7.2 State-changing tools (prohibited — never invoked)

`wallex_spot_post_account_orders` · `wallex_spot_delete_account_orders` (body) / `wallex_spot_delete_orders_client` (path) · `wallex_otc_place_easy_trade_order` · `wallex_margin_open_position` · `wallex_margin_close_position_id` · `wallex_margin_edit_colateral` · `wallex_margin_edit_sltp` · `wallex_basic_add_account_iban` · `wallex_credit_activate_user_package` · `wallex_credit_cancel_user_package` · `wallex_credit_enable_connect_to_wallet` · `wallex_credit_disable_connect_to_wallet` · `wallex_credit_enable_user_package_renew` · sub-account transfer helper

---

## 8. Capability classification summary

| Tool | Classification | Evidence |
|------|----------------|----------|
| `wallex_basic_get_markets` | VERIFIED | Live call this session |
| `wallex_spot_get_markets` | VERIFIED | Live call this session |
| `wallex_basic_candle_history` | VERIFIED | Live call this session |
| `wallex_basic_get_market_depth` | VERIFIED | Live call this session |
| `wallex_basic_get_latest_trades` | VERIFIED | Live call this session |
| `wallex_otc_get_otcmarkets` | VERIFIED (OTC, not Spot) | Live call this session |
| `wallex_margin_get_markets` | VERIFIED (margin, not Spot) | Live call this session |
| `wallex_margin_public_ratio` | VERIFIED (margin sentiment) | Live call this session |
| `wallex_otc_get_otc_price` | NOT_AVAILABLE (returns nothing) | Prior-session failure; not retried |
| `wallex_spot_get_depth` | UNVERIFIED | Catalog schema only this session |
| Private-account tools | UNKNOWN (runtime); definition-documented | Not invoked by policy |
| State-changing tools | NOT_AVAILABLE for use; prohibited | Never invoked |
| Server/tool-def version, rate limits, timeouts, max candle range, WebSocket | UNKNOWN | Not exposed/documented |
| CoinGecko (`coingecko-traider-mcp`) | VERIFIED (supplementary only) | Prior-session `simple.price.get` |

---

## 9. Is the evidence sufficient to complete Feature 005 T003?

**Partial — not yet sufficient to declare T003 complete.**

- **Sufficient**: The public, read-only Wallex **Spot market-data surface** is verified live: symbols, tickers, candles, order book, and recent trades, with exact field names, timestamp formats, and response shapes. An adapter schema binding for these five calls can be completed and tested against fixtures.
- **Required gaps before completion**:
  1. Tool/server definition **version** (UNKNOWN).
  2. **Rate limits, timeout semantics, and max candle-history range** (UNKNOWN) — needed for adapter hardening.
  3. **Pagination/streaming** availability for trades/depth (UNKNOWN).
  4. `wallex_otc_get_otc_price` empty response semantics (NOT_AVAILABLE; must not be treated as Spot capability).
  5. Authoritative Smart98 permission model for these tools (policy-required, UNKNOWN).
- **Explicitly out of scope / not advanced**: no orders, cancellations, OTC execution, margin, transfers, deposits, withdrawals, private-account reads, credential configuration, or direct production calls were performed; no new MCP was installed or configured; no repository files were modified by this task.

**Recommendation**: Record this report and the noted gaps in `docs/research/` (e.g. `mcp-tool-evidence-2026-10-22.md`) as part of T003's evidence trail, then resolve the UNKNOWN items via the Smart98 owner/contract before closing the task.

---

**Final statement**: CoinGecko remains supplementary context only and was not used as Wallex execution data. No credentials were exposed. No live orders or other state-changing trading actions occurred.
