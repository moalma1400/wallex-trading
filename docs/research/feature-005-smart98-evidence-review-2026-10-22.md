# Feature 005 — Smart98 evidence intake, security review, and architecture inventory

**Review date:** 2026-10-22

**Scope:** T003 evidence intake; T004 security, privacy, risk, and compliance review; T005 repository architecture inspection.

**Evidence boundary:** user-supplied sanitized report text, the earlier notice, and repository-held documentation/code only. No Smart98 or Wallex tool was invoked by Arena for this review; all tool observations/classifications below remain attributed to the supplied report.

## Executive status

- **T003 — OPEN / BLOCKED; user-supplied detailed report text now archived.** The user supplied the complete sanitized text titled “Feature 005 Task T003 — MCP Tool Evidence Report,” dated 2026-10-22. It reports nine public reads and provides summarized schemas/observations and its own `VERIFIED`, `UNVERIFIED`, `UNKNOWN`, `PARTIAL`, and `NOT_AVAILABLE` classifications. These are report claims, not Arena-verified facts. Arena did not independently invoke the tools. The separate archive is [`USER-SMART98-MCP-TOOL-EVIDENCE-REPORT-2026-10-22`](user-sources/smart98_mcp_tool_evidence_report_2026-10-22.md); the earlier notice remains a separate source [`USER-SMART98-MCP-REPORT-NOTICE-2026-10-22`](user-sources/smart98_mcp_report_notice_2026-10-22.md). T003 still lacks authoritative server/tool-definition version, Smart98 mediation/auth/permission contract, rate limits, timeout semantics, maximum candle range, pagination/streaming contract, complete raw evidence, and the required order-lifecycle tool contract.
- **T004 — REVIEW RECORDED; PERMISSION/COMPLIANCE GATES UNRESOLVED.** Credential, privacy, data-classification, eligibility, failure, price-reference, and compliance boundaries were reviewed below. A completed review is not a legal, account-permission, or trading-authorization approval.
- **T005 — ARCHITECTURE INVENTORY RECORDED.** Existing parser/provider and offline domain/data-quality/risk/replay components are documented below. No production adapter was written, enabled, or connected.
- **T006–T008 remain open.** No provider-neutral contract, adapter, fixtures, or new tests were implemented; T007 remains specifically deferred. T009's offline validation and T010's evidence/documentation updates are recorded below and in `tasks.md`.

## T003 — Supplied report claims and evidence boundary

The user supplied the complete sanitized report text inline; its full content is preserved at [`USER-SMART98-MCP-TOOL-EVIDENCE-REPORT-2026-10-22`](user-sources/smart98_mcp_tool_evidence_report_2026-10-22.md). The report describes nine public reads and observed tool definitions. Its tool classifications and observations are **attributed to that user-supplied report**. Arena did not independently invoke any connector or MCP tool, and no original Smart98 export, raw request/response transcript, or versioned schema artifact was supplied separately. The earlier [`report notice`](user-sources/smart98_mcp_report_notice_2026-10-22.md) is a separate, notice-only source with its own hash.

The report says a `wallex-mcp` connector with approximately 52 tools was accessible through Smart98 and also names `coingecko-traider-mcp` and `mcp-git-moalma`. These connector counts/access statements are report claims, not observations by Arena. The report records the following public/data surfaces:

| Class | Tool(s) and report-attributed observations | Classification in the supplied report | Review boundary |
|---|---|---|---|
| Public Spot market list / ticker fields | `wallex_basic_get_markets` and `wallex_spot_get_markets`; `{}` input; market objects include `symbol`, `base_asset`, `quote_asset`, price/volume/change fields, Spot/OTC/Margin flags, `flags.isRisky`, precision fields, `is_market_type_enable`, `fair_price`, and labels. The report says 85+ TMN/Spot-capable markets were returned. | `VERIFIED` (report's label) | User-reported observation only; market presence/`is_spot`/`is_market_type_enable` is not orderability, permission, or current allowlisting. No raw payload is available for Arena verification. |
| Candles | `wallex_basic_candle_history`; `symbol`, `resolution` (`1,5,15,30,60,240,720,D,W,M`), `from`/`to` as int64 Unix seconds; report says `s:"ok"`, parallel `t[]`, `o/h/l/c[]`, `v[]`, string decimals, and a 60-minute `USDTTMN` example. | `VERIFIED` (report's label) | Exact time-boundary, maximum history, pagination, completeness, and upstream schema/version are not established. The example timestamp/values in the supplied report are claims, not a verified fixture. |
| Single-symbol depth | `wallex_basic_get_market_depth`; `symbol` input; report says 50 asks and 50 bids with `{price, quantity, sum}`, asks ascending and bids descending. | `VERIFIED` (report's label) | User-reported only; response freshness, units, truncation, limits, and source version remain unresolved. |
| Recent public trades | `wallex_basic_get_latest_trades`; `symbol` input; report says 50 `latestTrades` entries with `symbol`, `quantity`, `price`, `sum`, `isBuyOrder`, and ISO-8601 UTC `timestamp`. | `VERIFIED` (report's label) | User-reported only; retention, pagination, stable IDs, and freshness remain unknown. |
| All-Spot depth | `wallex_spot_get_depth`; schema/description only, not invoked according to report. | `UNVERIFIED` (report's label) | Do not infer runtime support or use. |
| OTC metadata | `wallex_otc_get_otcmarkets`; report describes `stepSize`, `tickSize`, notional/quantity limits, stats, status flags, and risky flags. | `VERIFIED` as OTC (report's label), not Spot | Separate product surface; not Spot-market evidence or authorization. |
| Margin markets / public ratio | `wallex_margin_get_markets` and `wallex_margin_public_ratio`; report describes risk-coefficient fields and an observed `70/30` ratio. | `VERIFIED` as Margin (report's label), not Spot | Separate product surface; no Margin action authorized. |
| OTC price | `wallex_otc_get_otc_price`; report says it returned `no result returned` in a prior session and was not retried. | `NOT_AVAILABLE` for effective use (report's label) | This is a reported prior-session failure, not a Spot capability or Arena-observed response. |
| Private/account reads | Names are listed in §7.1 of the archived report as definition-documented; not called according to the report. | Runtime `UNKNOWN` (report's label); not invoked | Keep disabled. No permission or account entitlement follows from a definition or listing. |
| State-changing tools | Names are listed in §7.2 as prohibited and never invoked. | `NOT_AVAILABLE` for use / prohibited (report's label) | No order, cancellation, transfer, deposit, withdrawal, wallet, OTC, or Margin action is authorized or implemented. |

### Report-attributed semantics, limits, and unresolved fields

| Attribute | Supplied report's observation/classification | Current evidence interpretation |
|---|---|---|
| Candle timestamps | Unix seconds; example `1733425200`; OHLCV as strings — `VERIFIED` in report | Report claim only; source/tool version and raw response are not independently available. |
| Trade timestamps | ISO 8601 UTC; example `2026-10-22T12:18:04Z` — `VERIFIED` in report | Report claim only. |
| Depth ordering/count | Asks ascending, bids descending; 50 levels per side — `VERIFIED` in report | Report claim only; no history, pagination, or truncation contract. |
| Numeric representation | Prices/quantities as strings or numbers; preserve exact string for decimals — `VERIFIED` in report | Mixed wire representation is reported; do not normalize by guessing or infer exact per-field schema. |
| Freshness | No connector guarantee; the report attributes ticker 60s, book 30s, and candles 300s gates to `mcp_adapter` — `UNKNOWN` upstream / configurable locally in report | The checked-in `src/mcp_adapter/provider.py` exposes a generic `check_staleness` helper and requires a caller-supplied maximum age in `MarketEligibilityGate.evaluate`; no per-data-kind 60s/30s/300s defaults were found. Treat the report's local-threshold claim as unreconciled and do not present these numbers as current code or upstream policy. |
| Pagination | Markets/depth/trades show no pagination in observed schemas; order-history `page`/`per_page` is definition-only and not invoked — `UNKNOWN` for market data | Preserve as report claim; no conclusion that pagination is unavailable. |
| Rate limits / timeouts | Not documented in observed definitions — `UNKNOWN` | Gate remains open; no numeric values or retry semantics inferred. |
| Error behavior | `s`, `success`, `message` fields; OTC price can return nothing — `PARTIAL` | Report's classification; no complete error/timeout/partial-result contract. |
| Candle maximum range | Not probed — `UNKNOWN` | Required before any adapter contract can be considered complete. |
| WebSocket/streaming | No evidence in report — `UNKNOWN` | Do not convert to `NOT_AVAILABLE`. |
| Server/tool definition version | Not exposed — `UNKNOWN` | Authoritative source/version gate remains open. |
| Smart98↔Wallex compatibility/auth | Not independently documented — `UNKNOWN` | Reported public calls without credentials do not prove permission, mediation, secret isolation, or endpoint authentication contract. |

The report includes cautionary examples: `is_market_type_enable` was reportedly true only for some examples (`BTCTMN`, `ETHTMN`, `USDTTMN`, `XAUTTMN`, `PEPETMN`, `SOLTMN`…) and false for most; OTC status examples include `XLMTMN` buy `DISABLE` and `MOGTMN` sell `DISABLE`; `flags:["isRisky"]` examples include `PUMPTMN`, `MOGTMN`, `SANDTMN`, `FLOWTMN`, `DEXEUSDT`, and `PNUTUSDT`. These values are report-attributed, not a current allowlist. Continue to fail closed on risky, disabled, missing, stale, malformed, or contradictory market evidence, and do not infer challenge permission from any of these fields.

The report also says `fair_price.bid == fair_price.ask` in market payloads while depth exposes separate best bid/ask levels. This is recorded as **D-019, a user-reported observation**, not an independently verified contradiction. `fair_price` remains a reference value, not an executable bid/ask quote; never use it as an order price, fill, or spread. See [D-019](discrepancies.md) and the [price warning](../api/tickers-and-prices.md).

### Remaining T003 acceptance gaps

T003 remains **OPEN / BLOCKED**, despite the supplied report's per-tool `VERIFIED` labels, because the required authoritative contract and remaining fields are not established:

1. Server/tool-definition version, canonical source/release, and complete versioned schema evidence are `UNKNOWN`.
2. Smart98↔Wallex compatibility, auth/delegation, per-tool permission/side-effect proof, credential custody, and the secret/logging boundary remain `UNKNOWN`/`UNVERIFIED`. The report's statement that certain calls were made without account credentials is not independently verified by Arena.
3. Rate limits, timeout/retry/cancellation/error semantics, maximum candle range, market-data pagination/truncation/streaming, freshness guarantees, and exact candle-range/completeness rules remain `UNKNOWN` or `PARTIAL` as reported.
4. The pasted report summarizes tool definitions and observations, but supplies no separate original Smart98 export or full raw request/response transcript to audit schema fidelity, provenance, result completeness, and timestamps against.
5. The T003 requirement also covers challenge-account order-lifecycle tool contracts. Those tools were not invoked; their names/definitions do not establish schemas, permissions, idempotency, status/fill/cancel/reconciliation semantics, or account authorization.
6. The report's `wallex_otc_get_otc_price` `NOT_AVAILABLE` finding and `wallex_spot_get_depth` `UNVERIFIED` schema-only status must remain distinct from the five report-classified public Spot tools.

The report states that no private-account reads or state-changing actions were performed and recommends resolving unknowns with the Smart98 owner/contract. This review takes no action based on tool presence and does not authorize direct Wallex access, private reads, new MCP configuration, orders, or other state changes. The report's statement that PR #1 was “open, unmerged” is preserved in its source text as supplied; current GitHub metadata for this review shows PR #1 is already merged. That repository-state mismatch does not change or rewrite the report.

### Local adapter assumptions are not Smart98 evidence

The repository already contains code under `src/mcp_adapter/`; those code-level expectations are inventoried in T005 below. Some local identifiers overlap with the user-supplied report, but that overlap is not independent verification. The following identifiers and shapes are read from checked-in implementation and fixtures—not treated as Smart98 contracts:

- `wallex_basic_get_markets`: invoked without parameters; parser accepts an optional boolean `success`, an optional `result` object, and expects a non-empty `markets` array.
- `wallex_basic_candle_history`: local caller sends `symbol`, `resolution`, `from`, and `to`; code maps integer-looking resolution strings to intervals and expects UDF-like `s`, `t`, `o`, `h`, `l`, `c`, `v` arrays. The parser treats `t` as Unix seconds and values as exact decimal-compatible inputs. These are code assumptions only.
- `wallex_basic_get_market_depth`: local caller sends `symbol`; parser expects `ask` and `bid` arrays containing `price` and `quantity`.
- `wallex_basic_get_latest_trades`: local caller sends `symbol`; parser expects `latestTrades` with `symbol`, `price`, `quantity`, `isBuyOrder`, and ISO-8601 `timestamp`.

The checked-in tests patch the invoker and use `tests/fixtures/mcp_responses.py`; they demonstrate local parser behavior only. The separately supplied report claims live access, but Arena did not verify it or the actual Smart98 schemas. The code's candle range check accepts an event at `to` (`timestamp > end` is rejected), but upstream boundary semantics remain **UNKNOWN**. The source documentation itself records discrepancies/limits rather than runtime guarantees: [Basic candle guide](https://developers.wallex.ir/docs/basic-services-candles), [generated candle-history page](https://developers.wallex.ir/docs/generated/candle-history), and [Basic depth guide](https://developers.wallex.ir/docs/basic-services-depth).

## Mandatory `fair_price` warning

`fair_price` is a reference/fair-price observation, **not an executable bid/ask quote**. Do not use it to establish an executable buy or sell price, fill assumption, spread, or order limit. The registered Wallex page describes `public:all@fairPrice` as periodic snapshots with `ts` and `prices`, possible omissions, and no history/replay; that is documentation text, not an execution quote or runtime guarantee. [MOD-SOCKET-FAIR-PRICE](https://developers.wallex.ir/docs/socket-fair-price)

A specific local risk was found: `src/mcp_adapter/provider.py::parse_ticker_from_market` currently copies `fair_price.bid` and `fair_price.ask` into fields named `Ticker.bid` and `Ticker.ask`. That naming/mapping must **not** be interpreted as proof of executable quotes. It must be treated as a pre-use review/remediation item; no code behavior was changed in this documentation task.

## T004 — security, privacy, risk, and compliance review

### Credential and authorization boundaries

- Repository policy forbids requesting, creating, or using real Wallex credentials for this work. `SECURITY.md`, `.env.example`, `.gitignore`, and the constitution prohibit committing keys/tokens/cookies/account data; `.env.example` contains only a blank `WALLEX_API_KEY=` placeholder, and `.gitignore` excludes `.env`, secret directories, key files, and local data.
- Existing official documentation describes API-key account selection and Read/Trade/Withdrawal permissions, but that is documentation about key setup, not proof of the challenge account's permission or Smart98's secret isolation. Current endpoint-specific auth, key lifecycle, challenge permissions, Smart98 credential custody, model visibility, and logging/redaction remain **UNKNOWN**. [CREATE-KEY](https://developers.wallex.ir/docs/create-api-key) · [MOD-INTRO](https://developers.wallex.ir/docs) · [SPOT-INTRO](https://developers.wallex.ir/docs/spot-intro)
- Public market-data reads, private/account-sensitive reads, and writes must be classified separately. The adapter's current hard-coded read-method names do not prove that the remote tools are read-only or least-privileged. No private-account information was accessed; no live order, cancellation, transfer, deposit, withdrawal, or wallet action was taken.

### Public versus private, OTC, Margin, and state-changing surfaces

- Feature 005 covers only verified, public, read-only **Spot** market data through Smart98. Market metadata, candles, depth, and public trades must not be conflated with balances, private order history, account fees/wallets, Margin positions/P&L, OTC price/execution, or order-changing operations.
- Wallex documentation separately describes market/Spot market pages and state-changing order documentation. Documentation is not runtime availability or account authorization. The generated order-create page is a documented write operation, not an approved Smart98 tool or permission. [MARKETS](https://developers.wallex.ir/docs/basic-services-markets) · [SPOT-MARKETS](https://developers.wallex.ir/docs/spot-active-markets) · [MOD-GENERATED-POST-ACCOUNT-ORDERS](https://developers.wallex.ir/docs/generated/post-account-orders)
- OTC, Margin, private-account tools, and state-changing tools are not converted into Spot public-data capabilities by appearing in an old capability matrix or by existing in an MCP catalog. This task does not authorize probing them.

### Market eligibility and risk flags

- `config/challenge/wallex_disabled_spot_pairs_raw.txt` is user-provided evidence, not an official current allowlist. Its derived JSON contains 345 raw/unique entries with no recorded duplicates or malformed entries, but absence from the exclusions **never authorizes** a market. Keep current challenge allow-list, market state, orderability, permissions, and effective time unresolved until official organizer/account evidence is supplied.
- The reusable fail-closed path is in `src/wallex_research/challenge.py`: `DisabledPairRegistry.load` checks the raw-file hash/count/canonical derivation; `is_challenge_spot_market_allowed` rejects missing, non-official, stale/future, contradictory, disabled, unsupported, or incomplete market metadata and requires explicit strategy/risk approval. `validate_market_order_amounts` refuses unverified precision/minimum semantics. The checked-in policy is `execution_scope: offline_only`; cutoff and freshness are unset, and numeric risk limits are `null`/`UNRESOLVED`.
- `src/mcp_adapter/provider.py::MarketEligibilityGate` blocks `isRisky`, non-Spot, disabled market type, missing competition allowlisting, missing source timestamp, and missing age policy. However, it has no `challenge_enabled`/`orderable`/precision-semantics fields and a positive result explicitly does not establish order authorization.
- `src/mcp_adapter/eligibility.py::configure_elcamp_gate` contains a separate small hard-coded prohibition list. It is not the canonical 345-pair registry and must not be treated as a second source of truth or used to authorize any market. Risky or disabled markets remain blocked conservatively; unknown/stale/contradictory eligibility also blocks.

### Fail-closed behavior and gaps

- Existing parsers reject invalid/non-finite decimal inputs, naive timestamps, malformed or mis-sized candle arrays, empty candle history, inconsistent OHLC, duplicate/out-of-order/gapped candles, malformed trade fields, unsorted/crossed books, and malformed success/result envelopes. They do not silently sort or repair data.
- `check_staleness` exists, but it is a helper rather than an end-to-end freshness contract. Provider methods do not enforce a configured maximum age; `get_markets`, `get_ticker`, and `get_order_book` use local receipt time where available, which is not source-event time. Candle parsing does not attach a source/retrieval provenance envelope. The challenge metadata-age threshold remains unset.
- `MCPTimeout` is declared but the invoker seam has no timeout, retry, pagination, or partial-result policy. Tool exceptions are not normalized into a verified upstream error contract. Candle range checking, timestamp-unit assumptions, and interval completeness need authoritative confirmation before any use.
- Feature 003's offline `AuditPolicy` requires explicit interval, range, as-of/max-age, known-symbol, and precision limits for replay eligibility; missing values remain warnings/unknown and block replay export. Its local audit does not prove authenticity or exchange compatibility.

### Jurisdiction, organizer rules, and compliance gates

- The repository has primary U.S. Treasury/OFAC records. The Treasury release dated 2026-06-02 identifies Wallex in an OFAC designation context; OFAC FAQ 1257, shown as updated 2026-08-07 in the register, states that non-U.S. persons who transact with designated exchanges including Wallex may also face sanctions exposure. These are significant risk signals, not individualized legal advice or a determination about any user's facts. [US-TREASURY-WALLEX-DESIGNATION](https://home.treasury.gov/news/press-releases/sb0519) · [OFAC-FAQ-1257](https://ofac.treasury.gov/faqs/1257)
- No current qualified review for the relevant person/entity, place of establishment/residence, counterparties, payment rails, or applicable EU/French/local law is recorded. Do not infer jurisdiction or eligibility from a location hint, a public API page, or an available tool. Current sanctions, licensing, geographic access, exchange terms, tax, privacy, banking, and other compliance questions remain unresolved.
- No authoritative organizer rules, official competition window/cutoff, current permitted Spot-market list, dedicated-account permission matrix, capital/liability/settlement terms, or explicit owner live-activation decision is present in the inspected repository. The archived challenge brief/transcript are user-provided and not official-verified. Tool existence or operator-reported public-data invocation does not establish legal permission, trading authorization, or account entitlement.

**T004 outcome:** review documented; compliance and execution gates remain unresolved. No gate is marked passed.

## T005 — architecture inventory and reuse assessment

| Existing component | Actual interface / reusable types | Validation behavior and current boundary |
|---|---|---|
| `src/mcp_adapter/__init__.py` | `MarketDataProvider` methods: `get_markets`, `get_candles`, `get_order_book`, `get_recent_trades`, `get_ticker`; dataclasses `MarketMeta`, `Candle`, `Ticker`, `OrderBookLevel`, `OrderBook`, `PublicTrade`; `DataSource.MCP_SMART98`; `Eligibility`/`EligibilityResult`; `MCPError`, `MCPTimeout`, `InvalidDataError`, `StaleDataError`. | Code-level provider contract only. Types are in an MCP-labelled package and default to `MCP_SMART98`; they are not a verified external schema or a fully provider-neutral domain contract. No production invoker is wired in this repository. |
| `src/mcp_adapter/provider.py` | `Smart98MCPProvider`; `set_mcp_invoker(callable)` injection seam; constants for four tool IDs; parsers for market metadata, UDF-like candles, depth, recent trades, and ticker; `MarketEligibilityGate`. | No HTTP/WebSocket/MCP transport client. Strict decimal/timestamp/shape checks are present. Source/tool version and stable provenance are not consistently carried. `MCPTimeout` is not enforced; `check_staleness` is a generic helper and no ticker/book/candle 60s/30s/300s defaults are present; `MarketEligibilityGate.evaluate` requires a caller-supplied maximum age. This conflicts with the report's claim that these are current `mcp_adapter` gates. Fair-price-to-bid/ask mapping is hazardous as described above. |
| `src/mcp_adapter/eligibility.py` | `configure_elcamp_gate()` returns `MarketEligibilityGate` with a small hard-coded deny list and no preapproved markets. | Separate from the canonical disabled-pair registry; must not be used as authorization. |
| `src/wallex_research/models.py` and `src/wallex_research/data_quality.py` | Strict `Decimal`/aware-UTC `Candle`, caller-supplied `TargetExposure`, explicit `SimulationConfig`, `QualityIssue`/`QualityReport`, `ReplayResult` and simulated ledger/fill types. | Local/offline. Invalid numeric/OHLC/chronology/cadence and risk inputs are rejected; no strategy or network source is implemented. |
| `src/wallex_research/historical.py` | Versioned `Provenance`, `DatasetContext`, `CandleRecord`, `MarketMetadataRecord`, `PublicTradeRecord`, `FairPriceSnapshotRecord`, `BookLevel`, `OrderBookSnapshotRecord`, `OrderBookSideSnapshotRecord`, `HistoricalDataRequest`, and `HistoricalDataProvider` protocol. | `SCHEMA_VERSION = 1.0`; exact decimals, timezone-aware UTC, duplicate JSON-key rejection, strict local CSV/JSON parsing. `HistoricalDataProvider` is a local/future-history seam (`read(request) -> Iterable[Mapping]`), only candles/public trades for requests; it is not a Smart98 client or a general live `MarketDataPort`. |
| `src/wallex_research/dataset_store.py`, `src/wallex_research/historical_quality.py`, `scripts/market_data_pipeline.py` | Content-addressed local import, immutable raw bytes/hash manifests, normalized records, `AuditPolicy`/`AuditReport`, local audit and gated candle export. | Raw/normalized hashes and reparsing are checked. Replay eligibility requires explicit expected interval/range/as-of/max age/known symbols/precision policy; missing policy blocks. No fetch or remote provider. |
| `src/wallex_research/challenge.py`, `config/challenge/wallex_disabled_spot_pairs_raw.txt`, `config/challenge/wallex_disabled_spot_pairs.json` | `DisabledPairRegistry`, `MarketSnapshot`, `MarketRequest`, `EligibilityDecision`, `is_challenge_spot_market_allowed`, and `validate_market_order_amounts`. | Hash-bound user-provided 345-pair exclusions; fail-closed challenge, Spot, orderability, precision, source evidence, and risk gates. The disabled list is not a positive allowlist. |
| `src/wallex_research/challenge_execution.py`, `src/wallex_research/replay.py`, `src/wallex_research/decision_log.py` | `dispatch_order_intent`, `run_replay`, `DecisionEvent`, `DecisionAuditLog`. | Backtest/shadow/dry-run are record-only or deterministic local replay; LIVE returns `LIVE_EXECUTION_NOT_IMPLEMENTED`; submitter seam is never invoked. Exchange-origin events are rejected by the current event contract. No order execution path exists. |
| `tests/test_mcp_adapter.py`, `tests/fixtures/mcp_responses.py`, `tests/test_historical_data.py`, `tests/test_challenge.py`, `tests/test_replay.py`; `scripts/validate_sources.py`, `scripts/validate_doc_links.py`, `.github/workflows/ci.yml` | Parser/provider tests patch the injected invoker; all checked-in market examples are synthetic fixtures. Validators check source-register structure/hash/reference integrity and local Markdown links/citations; CI compiles and runs offline tests. | These tests establish local behavior only, not Smart98 schema, production availability, permission, or source provenance. CI has no Wallex/Smart98 credentials or calls. |

### T006 boundary and T007 deferral

There is not currently a true provider-neutral live `MarketDataPort`. The existing `MarketDataProvider` is a reusable method shape but its types are located in `src/mcp_adapter` and label data as `MCP_SMART98`; `HistoricalDataProvider` is a distinct offline/local-history protocol. The versioned `src/wallex_research/historical.py` records are the strongest reusable normalized local types, while `MarketSnapshot` and `DisabledPairRegistry` are the challenge eligibility boundary. T006 may define a thin provider-neutral read-only contract around these existing types only after the exact source/tool contract is available; do not duplicate the data model or mistake local parser fields for upstream schemas. T006 remains open and assumptions/unknowns must remain explicit.

T007 is **not performed**: this review changed no adapter behavior, added no transport or credential path, and enabled no runtime. The existing `src/mcp_adapter/` code is not evidence that implementation gates have passed. No order-submission implementation is authorized.

## Review procedure and validation record

Repository-local guidance and relevant existing skill procedures were applied manually. This Arena environment has no verified native Spec Kit integration; no Spec Kit command/skill invocation is claimed.

- `python3 scripts/validate_sources.py`: final **PASS**, 137 records/unique IDs and URLs; `blocked=8`, `in_progress=5`, `not_started=51`, `reviewed=73`. An earlier run caught a stale SHA-256 for the edited notice file; the actual file hash was corrected and the final validator passed.
- `python3 scripts/validate_doc_links.py`: **PASS**, 216 relative Markdown links and 266 registered citations resolve/match; external URLs were not tested.
- Full offline test suite: **PASS**, 145 tests and 24 subtests. System Python initially lacked `pytest`; the CI-pinned `pytest==9.1.1` was installed only into a temporary `/tmp` virtual environment. No dependency or environment change was added to the repository, and no Wallex/Smart98 request was made.
- `python3 -m compileall -q src tests scripts`: **PASS**.
- `python3 scripts/build_challenge_pair_registry.py --check`: **PASS**, 345 raw/unique, no duplicate or malformed pairs.
- `python3 scripts/check_market_data.py tests/fixtures/synthetic_ohlcv.csv --interval-seconds 60`: **PASS**, three synthetic rows are structurally valid only; provenance, completeness, and exchange compatibility remain unverified.
- `git diff --check`: final **PASS** after report/source-register reconciliation.
- Changed-file secret scan: **PASS**, no matches for four high-signal credential patterns across 19 changed/untracked files (heuristic only, not secret-scanner certification). Source/script scan: **PASS**, no direct HTTP/WebSocket clients in the application modules or scripts.

All tests, validators, and scans are local/offline with respect to Wallex and Smart98. No MCP was installed/configured, no Smart98 or Wallex tool was invoked, no production request or private-account read was made, and no state-changing action occurred.
