# Feature 005 — Smart98 evidence intake, security review, and architecture inventory

**Review date:** 2026-10-22

**Scope:** T003 evidence intake; T004 security, privacy, risk, and compliance review; T005 repository architecture inspection.

**Evidence boundary:** operator-provided report notice plus repository-held documentation/code only. No Smart98 or Wallex tool was invoked by Arena for this review.

## Executive status

- **T003 — OPEN / BLOCKED.** The user reports that an operator supplied a Smart98-generated report titled “Feature 005 Task T003 — MCP Tool Evidence Report,” dated 2026-10-22, describing live, read-only invocation of public Wallex market-data tools through the existing Smart98-mediated MCP environment. The original report body or attachment is not present in the prompt or workspace. Only this aggregate claim can be recorded. Exact tool identifiers, inputs/outputs, timestamps, decimal encodings, source/version, permissions, and the report's individual status labels cannot be preserved or audited. This is not authoritative tool-contract evidence and Arena did not independently invoke the tools. The intake note is [`USER-SMART98-MCP-REPORT-NOTICE-2026-10-22`](user-sources/smart98_mcp_report_notice_2026-10-22.md); it is not the raw report.
- **T004 — REVIEW RECORDED; PERMISSION/COMPLIANCE GATES UNRESOLVED.** Credential, privacy, data-classification, eligibility, failure, price-reference, and compliance boundaries were reviewed below. A completed review is not a legal, account-permission, or trading-authorization approval.
- **T005 — ARCHITECTURE INVENTORY RECORDED.** Existing parser/provider and offline domain/data-quality/risk/replay components are documented below. No production adapter was written, enabled, or connected.
- **T006–T008 remain open.** No provider-neutral contract, adapter, fixtures, or new tests were implemented; T007 remains specifically deferred. T009's offline validation and T010's evidence/documentation updates are recorded below and in `tasks.md`.

## T003 — What the supplied notice supports, and what it does not

The task message's evidence is operator-provided. It supports only this aggregate statement: **an operator reports that Smart98-mediated MCP tools were invoked read-only for public Wallex market data**. It does not enumerate a capability in the text available for review.

| Capability class | What can be attributed to the supplied notice | Review status / boundary |
|---|---|---|
| Public Wallex market data (aggregate) | The operator says the report describes live, read-only invocations through Smart98. | **OPERATOR-REPORTED (aggregate claim only); not independently verified by Arena.** No exact tool or returned data is available here. |
| Spot market metadata | No tool identifier or invocation details appear in the supplied message. | **UNKNOWN** at tool level; do not infer support from the aggregate claim. |
| Candles / OHLCV | No identifier, interval, input range, response, timestamp unit, decimal representation, or completeness finding appears in the supplied message. | **UNKNOWN.** |
| Order-book depth | No identifier, side/depth limit, snapshot semantics, timestamp, or response appears in the supplied message. | **UNKNOWN.** |
| Recent public trades | No identifier, limit, retention, pagination, stable ID, timestamps, or response appears in the supplied message. | **UNKNOWN.** |
| Ticker / `fair_price` | No ticker tool or response appears in the supplied message. | **UNKNOWN.** In all cases, `fair_price` is not an executable bid/ask quote; see the warning below. |
| Streaming / WebSocket | The task message says the report identifies pagination/streaming gaps, but the report's wording and any status tag are unavailable. | **UNKNOWN** from the notice; do not convert this into a current `NOT_AVAILABLE` claim. |
| OTC | No OTC tool invocation is identified in the supplied message. | No new evidence. OTC is a separate product class, not Spot authorization, and is outside Feature 005's approved public Spot adapter scope. |
| Margin | No Margin tool invocation is identified in the supplied message. | No new evidence. Margin is a separate product class and outside Feature 005's approved scope. |
| Private-account reads | No private tool invocation is identified. | Not authorized or accessed; keep balances, private orders, account fees/wallets, positions, and other private data separate and disabled. |
| State-changing tools | No state-changing invocation is identified. | Not authorized or invoked; order placement/cancellation, OTC execution, transfers, deposits, withdrawals, wallet actions, and margin actions remain prohibited. |

The existing `docs/smart98_mcp_capability_matrix.md` is a **2026-10-21 historical snapshot**. Its tool rows and checkmarks are not evidence from the newly mentioned report and its own notice says the responses are synthetic fixtures and current capability is unverified. Its historical “Not Available via MCP” list (WebSocket streaming, full historical trade list, historical order-book snapshots, and account transaction history) is retained as a historical claim only; it is not a current verified absence. The report notice does not let this review promote or correct any individual matrix row.

### Missing report fields and evidence gaps

The task message says the report has gaps in source/version, permissions, rate limits, timeouts, pagination/streaming, and candle ranges. It does not include the report's exact wording, status tags, values, evidence, or scope. Accordingly, the following are this review's conservative statuses—not quotations from the missing report:

| Evidence item | Status in this review | Specific evidence still needed |
|---|---|---|
| Smart98 product/interface version; MCP publisher, repository, release, and schema version | **UNKNOWN** | Canonical source, exact versions, dates, and a versioned tool catalog/schema. |
| Tool identity, input schema, output schema, and unmodified results | **UNKNOWN** | Exact tool IDs, arguments as sent, full sanitized response shapes/payloads or exact errors, and truncation indicators. |
| Read-only effect and least-privilege permissions | **UNVERIFIED** beyond the operator's aggregate characterization | Per-tool side-effect classification, upstream permissions, and evidence separating public reads from private or write-capable tools. Tool presence/name is not authorization. |
| Authentication and secret boundary | **UNKNOWN** | Which system holds credentials, how scopes/rotation/revocation work, what reaches model context, and log redaction/retention controls. No credentials are requested. |
| Rate limits, timeout, retry, cancellation, and error propagation | **UNKNOWN** | Exact Smart98 and upstream limits/budgets and behavior for errors, timeouts, partial results, retries, and cancellation. No numeric limits are inferred. |
| Pagination, truncation, and streaming | **UNKNOWN** | Whether each tool paginates/truncates; continuation semantics; supported stream/transport; ordering, replay, reconnect, and recovery behavior. The exact report may contain `NOT_AVAILABLE` findings, but its body is unavailable. |
| Candle query range and completeness | **UNKNOWN** | Accepted time units and range boundaries; maximum history; resolution set; inclusivity/alignment; omitted/partial candles; pagination and retention. |
| Timestamp, decimal, and provenance representation | **UNKNOWN** | Source-event timestamp fields, units/timezone/meaning, caller retrieval time, decimal string/number encoding, and provenance fields. Local parser expectations are not evidence of upstream behavior. |
| Individual report findings labeled `UNKNOWN`, `UNVERIFIED`, `PARTIAL`, or `NOT_AVAILABLE` | **NOT AVAILABLE in the supplied message** | The original report is needed to preserve its complete status vocabulary and wording verbatim. |

No transcript, raw request/response, or report file was fabricated. The evidence record's hash identifies only the repository's short intake note, not the original Smart98 report.

### Local adapter assumptions are not Smart98 evidence

The repository already contains code under `src/mcp_adapter/`; those code-level expectations are inventoried in T005 below. In particular, the following identifiers and shapes are read from the checked-in implementation and fixtures—not from the missing report and not independently verified as Smart98 contracts:

- `wallex_basic_get_markets`: invoked without parameters; parser accepts an optional boolean `success`, an optional `result` object, and expects a non-empty `markets` array.
- `wallex_basic_candle_history`: local caller sends `symbol`, `resolution`, `from`, and `to`; code maps integer-looking resolution strings to intervals and expects UDF-like `s`, `t`, `o`, `h`, `l`, `c`, `v` arrays. The parser treats `t` as Unix seconds and values as exact decimal-compatible inputs. These are code assumptions only.
- `wallex_basic_get_market_depth`: local caller sends `symbol`; parser expects `ask` and `bid` arrays containing `price` and `quantity`.
- `wallex_basic_get_latest_trades`: local caller sends `symbol`; parser expects `latestTrades` with `symbol`, `price`, `quantity`, `isBuyOrder`, and ISO-8601 `timestamp`.

The checked-in tests patch the invoker and use `tests/fixtures/mcp_responses.py`; they do not demonstrate live access or prove the actual Smart98 schemas. The code's candle range check accepts an event at `to` (`timestamp > end` is rejected), but upstream boundary semantics remain **UNKNOWN**. The source documentation itself records discrepancies/limits rather than runtime guarantees: [Basic candle guide](https://developers.wallex.ir/docs/basic-services-candles), [generated candle-history page](https://developers.wallex.ir/docs/generated/candle-history), and [Basic depth guide](https://developers.wallex.ir/docs/basic-services-depth).

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
| `src/mcp_adapter/provider.py` | `Smart98MCPProvider`; `set_mcp_invoker(callable)` injection seam; constants for four tool IDs; parsers for market metadata, UDF-like candles, depth, recent trades, and ticker; `MarketEligibilityGate`. | No HTTP/WebSocket/MCP transport client. Strict decimal/timestamp/shape checks are present. Source/tool version and stable provenance are not consistently carried. `MCPTimeout` is not enforced; freshness helper is not wired through provider calls; fair-price-to-bid/ask mapping is hazardous as described above. |
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

- `python3 scripts/validate_sources.py`: **PASS**, 136 records/unique IDs and URLs; `blocked=7`, `in_progress=5`, `not_started=51`, `reviewed=73`.
- `python3 scripts/validate_doc_links.py`: **PASS**, 196 relative Markdown links and 265 registered citations resolve/match; external URLs were not tested.
- Full offline test suite: **PASS**, 145 tests and 24 subtests. System Python initially lacked `pytest`; the CI-pinned `pytest==9.1.1` was installed only into a temporary `/tmp` virtual environment. No dependency or environment change was added to the repository, and no Wallex/Smart98 request was made.
- `python3 -m compileall -q src tests scripts`: **PASS**.
- `python3 scripts/build_challenge_pair_registry.py --check`: **PASS**, 345 raw/unique, no duplicate or malformed pairs.
- `python3 scripts/check_market_data.py tests/fixtures/synthetic_ohlcv.csv --interval-seconds 60`: **PASS**, three synthetic rows are structurally valid only; provenance, completeness, and exchange compatibility remain unverified.
- `git diff --check`: **PASS** after documentation edits.
- Changed-file secret scan: **PASS**, no matches for four high-signal credential patterns; this is heuristic, not a substitute for secret-scanner certification. Source/script scan found no direct HTTP/WebSocket clients in application modules or scripts.

All tests, validators, and scans were local/offline with respect to Wallex and Smart98. No MCP was installed/configured, no Smart98 or Wallex tool was invoked, no production request or private-account read was made, and no state-changing action occurred.
