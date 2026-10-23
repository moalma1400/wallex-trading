# Research log

## Snapshot 1 — 2026-10-21 (UTC)

### Method

- Started from user-specified official sources: `https://wallex.ir/`, `https://developers.wallex.ir/`, and `https://api-docs.wallex.ir/`.
- Opened the official developer-docs sitemap and transcribed 115 exact `/docs` destinations into the source register. The sitemap was used as page discovery evidence, not as evidence of page content.
- Inspected the developer introduction and representative API/product pages across Spot, OTC, Margin, trade credit, account fees, market metadata, candles, depth, and WebSocket. Page-specific status is recorded per source; remaining sitemap pages are explicitly `not_started`.
- Inspected all seven chunks returned for the legacy single-page API reference. Its top-level navigation categories are prerequisites, markets, user account, orders/trades, OTC, WebSocket, and Wallgate. Wallgate is distinguished as non-trading scope; old examples are retained as legacy evidence rather than treated as current values.
- Inspected the official Wallex homepage, commission page, and a linked fee announcement. The fee table rows in the commission-page extract were blank; the help-center fee candidate returned a 404 page. No missing rates were filled from a search snippet.
- Checked the official page entrypoint `https://wallex.ir/api-document`; the fetch tool failed without returning a status code/body. `developers.wallex.ir/robots.txt` returned the site's localized not-found page, not robot directives. Two guessed `/docs/api` and `/docs/api-reference` routes returned localized 404 pages; these guesses are not counted as official discovered destinations.
- For significant compliance risk, consulted primary official U.S. Treasury and OFAC sources directly. Treasury's June 2, 2026 release explicitly names Wallex as designated under E.O. 13902; OFAC FAQ 1257 states non-U.S. persons transacting with designated exchanges including Wallex may also face sanctions exposure and shows update date August 7, 2026. This is governmental legal context, not Wallex documentation or individualized legal advice.
- No Wallex API key was created or used; no account was accessed; no production REST endpoint or WebSocket was called; no orders/transfers/settings were changed.

### Coverage snapshot

- Official developer sitemap destination URLs discovered: **115**.
- Content pages reviewed in the sitemap inventory: **27**.
- Sitemap pages not yet content-reviewed: **88**.
- Sitemap-listed pages confirmed inaccessible: **0** in this pass; these were not individually attempted except pages recorded as reviewed.
- Duplicate sitemap destinations: **0** identified.
- Sitemap destinations excluded as out of scope: **0**; account/withdrawal/transfer-related pages remain inventoried but not reviewed, while Wallgate appears inside the legacy page and is marked non-trading scope.
- Additional official Wallex material reviewed: homepage, commission page, fee article, legacy API reference; failed help-center and API-document entrypoint attempts recorded separately.
- Government legal sources reviewed: Treasury release and OFAC FAQ.

These counts do not mean complete content coverage. The 88 `not_started` entries are material outstanding research, support/FAQ navigation may reveal more sources, and route availability has not been tested. See the [coverage matrix](coverage-matrix.md).

### Offline validation evidence

- `python3 scripts/validate_sources.py`: **PASS**, 127 records, 127 unique source IDs and URLs; status counts `reviewed=34`, `not_started=88`, `blocked=5` (includes 27 reviewed and 88 not-started sitemap pages; other reviewed/blocked records are listed outside that page count).
- A temporary malformed register missing `retrieved_at_utc` returned **exit code 1** with a specific missing-field error; no repository source data was altered for this test.
- `python3 scripts/validate_doc_links.py`: **PASS**, 45 local relative Markdown links resolve and 139 source citations match registered IDs and exact URLs; external links were not network-checked.
- `git diff --check`: **PASS** after trimming trailing whitespace.
- `python3 -m py_compile scripts/validate_sources.py scripts/validate_doc_links.py`: **PASS**.
- Credential-pattern scan for common GitHub token formats/private-key headers: no matches. This is a heuristic scan, not a guarantee of secret absence.

### Important source integrity notes

- No publication date is inferred from a page's appearance or from the research retrieval date. The page reader did not expose per-request timestamps; the register records the exact UTC timestamp at which the session compiled the retrieved-source snapshot and explicitly labels it as such, not as a per-page request time.
- Current-looking documentation is classified `unclear` unless the page itself establishes date/currentness. The old API reference is labelled `legacy` as a research label based on older examples and contract differences, not as a claimed official withdrawal notice.
- API limits, fees, enums, and precision are not guessed from sample values; disagreements are captured in [discrepancies](discrepancies.md).
- Search results were not used as proof of Wallex behavior or fee values. When an official URL was found, its page was fetched directly; missing content remains unresolved.

## Snapshot 2 — 2026-10-21 (UTC)

### Scope and method

- Continued from the existing official sitemap and source register. Kept Feature 001 active/incomplete; did not reinitialize Spec Kit or replace its templates/scripts.
- Read the actual constitution, Feature 001 artifacts, validators, source register, coverage matrix, discrepancy/open-question registers, docs, repository instructions, and generated skill structure before editing.
- Verified the installed Spec Kit CLI is `1.2.2`; GitHub release listing still marks `v1.2.2` Latest (released 2026-10-19). The current integration is generic. The feature creation dry-run indicated a descriptive feature branch, so only its directory naming was used; no branch command was executed and the Arena session branch is unchanged.
- Retrieved and reviewed 22 additional sitemap page bodies as complete one-chunk pages: basic-services overview, generated Spot market/depth/trade/account/order pages, and the eight documented Margin pages. Retrieved all chunks for the eight new WebSocket pages: all-price, fair-price, trade, buy/sell depth, candle, private channel, and raw protocol. Updated each register row with the actual page title, inspected content, currentness caveat, and status.
- Added five official OpenAPI/Swagger asset references (basic services, Spot, Margin, OTC, trade credit). The page reader exposed transformed/chunked excerpts (trade-credit reported 16 chunks); complete source bytes, checksums, publisher release metadata, and byte-for-byte local archives are unavailable. They remain `in_progress`, not complete. No live endpoint or WebSocket was contacted.
- Added `D-013` for generated REST host/path disagreements and `D-014` for UDF versus candle-WebSocket resolution coverage. A cited endpoint in any source remains documentation text, not proof of availability.
- Updated English API summaries and Persian-first WebSocket/data summaries. Added repository-specific custom skills while preserving all generated `speckit-*` skills. These files are reusable procedures, not verified slash commands; none is claimed as invoked.
- Amended the constitution to permit only local/offline strategy-neutral research code, with explicit Spot-only and compliance gates. Recorded the amendment and retained no-live, no-network, no-account, no-leverage, no-key, no-transfer/withdrawal boundaries.

### Coverage after follow-up

- Exact developer sitemap page destinations: **115**.
- Page bodies reviewed: **57** (27 in Snapshot 1 + 30 in this follow-up).
- Sitemap pages not yet body-reviewed: **58**.
- Sitemap pages individually confirmed inaccessible: **0**; the 5 `blocked` records in the whole register include separate probes and external source attempts, not sitemap page bodies.
- Duplicate sitemap URLs identified: **0**.
- Separate linked OpenAPI/Swagger artifacts: **5**, all `in_progress` pending complete source capture/review.
- Total source records: **132**; statuses: `reviewed=64`, `not_started=58`, `in_progress=5`, `blocked=5`. These whole-register counts are distinct from 115 sitemap-page counts.
- Coverage is not complete; auth, detailed permissions/schema, all remaining sitemap pages, support/terms/notices, and full API-spec capture remain open.

### Material findings

- The introduction says base host `api.wallex.ir`, while the basic-services and Spot Swagger artifacts and several generated pages state `api.wallex.com`; some generated order/depth examples begin `//api.wallex.com`. Margin and OTC artifacts declare `.ir`. The legacy all-depth route is `/v2/depth/all`, while a generated page shows `/depth/all`. The conflict is recorded; no host or path was executed or selected.
- Official v2 WebSocket pages distinguish full periodic fair-price snapshots from price-change-only updates, state no replay for most channels, describe depth as full snapshots without an initial snapshot, and document limited candle history. The eight source pages were read in all reported chunks. These are descriptions, not runtime service-level guarantees.
- REST UDF history and WebSocket candle examples show different resolution sets. The distinction is recorded without assuming one is exhaustive.
- Generated account balance, fee, wallet, order and private WebSocket documentation includes account-specific fields/authentication. None was accessed with a credential or account.
- A Margin product guide states maximum position age and extension terminology; these remain Margin documentation evidence only and are excluded from implementation.

### Offline implementation and test evidence

- Created Feature 002 specification, plan, research, data model, local contract, quickstart, tasks and requirements checklist before implementing the kernel. Feature 002 is in progress; Feature 001 remains in progress.
- Added dependency-free `src/wallex_research/` models, strict CSV input, OHLCV checks, explicit Spot risk validation, next-bar-open replay, modeled costs, partial-fill shortfall reporting, and an offline CSV audit CLI. No strategy generator, network adapter, credentials, account access, Smart98 adapter, or live feed exists.
- Tests use fixed synthetic fixtures. The passing suite has **16 unit tests** covering exact Decimal parsing, UTC normalization, OHLC constraints, order/duplicate/symbol/gap checks, CSV failures, next-bar causality, cost/cash reconciliation, explicit risk rejection, no shorting, drawdown, partial unfilled quantities, and a network-side-effect guard.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: **PASS**, 16 tests.
- `python3 scripts/check_market_data.py tests/fixtures/synthetic_ohlcv.csv --interval-seconds 60`: **PASS**, 3 synthetic rows; structurally valid only. This does not validate provenance, completeness outside the configured interval, or exchange compatibility.
- All generic costs/risk/capital/currency values in tests are synthetic; none is a Wallex fee or recommendation. No strategy, asset, market, timeframe, or user risk profile was selected.

## Snapshot 3 — 2026-10-21 (UTC)

- Reviewed five additional complete generated pages: historical UDF candles, Margin user levels, per-market Margin user levels, public-ratio schema, and user PNL. Account/user-level and PNL material remained documentation-only; no key or private request was used.
- The sitemap-listed `/docs/weekly` returned the official site's localized not-found body. The reader did not expose an HTTP status. Marked that single sitemap page inaccessible/blocked rather than not-started; no replacement is guessed.
- Added `D-015`: the basic UDF page marks its query fields Optional, while generated `candle-history` marks all four Required and lists a different set of resolution examples; the generated page also says `api.wallex.com`. Kept the mismatch unresolved.
- Updated current sitemap counts: **115 total**, **62 reviewed**, **52 not started**, **1 blocked/inaccessible**. Five API specification artifacts remain `in_progress`. Whole-register totals: **132 records** (`reviewed=69`, `not_started=52`, `in_progress=5`, `blocked=6`).
- No production request, WebSocket connection, credentials, account data, or account-changing action was used in this snapshot.

## Snapshot 4 — 2026-10-21 (UTC)

- Reviewed one additional complete generated Spot cancellation page: it documents `DELETE //api.wallex.com/v1/account/orders`, a required JSON `clientOrderId`, `x-api-key` authorization text, and response examples. This remains documentation evidence only; no key, request, or cancellation was used.
- Added `D-016` because this generated form differs from the prose path `DELETE /v1/account/orders/{client_id}` and the legacy query form. No canonical host, route, identifier, or auth is selected.
- Updated sitemap counts to **115 total**, **63 reviewed**, **51 not started**, and **1 blocked/inaccessible**. The sitemap itself was not re-fetched; it remains the 115-URL set captured in Snapshot 1. Whole-register totals are **132 records** (`reviewed=70`, `not_started=51`, `in_progress=5`, `blocked=6`).
- No API request, account access, key, WebSocket connection, or account-changing operation occurred.

### Validation after Snapshot 4

- `python3 scripts/validate_sources.py`: **PASS**, 132 source records with 132 unique IDs and URLs; statuses `reviewed=70`, `not_started=51`, `in_progress=5`, `blocked=6`.
- `python3 scripts/validate_doc_links.py`: **PASS**, 67 relative Markdown links resolve locally and 217 citations match registered source IDs and exact URLs. External URLs were not tested.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: **PASS**, 16 synthetic/offline unit tests (including arithmetic total-return assertion versus explicit initial cash).
- `python3 scripts/check_market_data.py tests/fixtures/synthetic_ohlcv.csv --interval-seconds 60`: **PASS**, three synthetic rows are structurally valid only.
- `python3 -m py_compile scripts/validate_sources.py scripts/validate_doc_links.py scripts/check_market_data.py src/wallex_research/*.py tests/test_*.py` and `git diff --check`: **PASS**. Feature 002 task checklist is fully checked; Feature 001 and whole-repository research remain incomplete.

## Feature 003 historical-market-data evidence and implementation follow-up

### Scope and method

- Revisited the official Basic markets, UDF candles, latest trades and depth prose pages; corresponding generated markets, candle-history, latest-trades and depth pages; the selected all-price, fair-price, public-trade, buy-depth and candle WebSocket pages; and the returned Basic Services/Spot specification chunks relevant to market data.
- No REST route or WebSocket was contacted. Documentation examples are not evidence of current runtime access or account entitlement. Basic/Spot artifacts were read as transformed chunks (6/6 and 3/3 respectively), not retrieved as exact bytes; no archive or checksum was fabricated. Margin, OTC and Trade Credit remain partially reviewed (1/5, 1/2 and 1/16 chunks).
- Maintained separate modern prose/generated, legacy and REST/WebSocket claims. Added [D-017](discrepancies.md) for depth numeric representations and [D-018](discrepancies.md) for security annotation differences, without selecting an implementation contract.
- Important unknowns retained: numerical polling limits, REST pagination, history retention, timestamp inclusivity/alignment, endpoint auth and runtime availability. The documentation only gives qualitative polling warnings.

### Feature outcome boundary

Feature 003 adds local-only import and audit support backed by synthetic fixtures. The implementation does not claim the source data is Wallex data and does not enable a provider/network path. Check test/validator outcomes in [Feature 003 research](../../specs/003-historical-market-data/research.md) after validation is complete.


## Feature 004 — Wallex/Starcoach hackathon policy (2026-10-21)

- Source `USER-WALLEX-HACKATHON-BRIEF` is the user-attached Markdown prompt; it is not independently official-verified. Its verbatim local archive SHA-256 is `da60ec1e3421f50990766b97ec611891f2d94a4226ffc64e301d343b0bebe144`. No public challenge URL or audio attachment was available. No challenge source was fetched or organizer contacted.
- Preserved the disabled-pair fenced block byte-for-byte as a local raw appendix and derived uppercase sorted JSON. Raw block: 345 entries, 345 unique, zero duplicates/malformed; SHA-256 `48a9d12c5660929bf2044c30535864eb4f008d0580aa3e0cf75f5b528242eba0`. The pair-list hash covers only that extracted appendix.
- Added local policy, explicit-config/risk-aware market eligibility, risk limit loader with all 15 numeric limits unset, deterministic pair-registry builder, offline execution boundary, versioned audit event schema, settlement readiness, synthetic-only metadata fixture, and challenge tests. No remote/API/account/credential/order actions were taken.
- Added English challenge KB/restrictions/judge/demo guides, Persian summary, Feature 004 Spec Kit artifacts, skills, roadmap and source/coverage/unresolved-question updates. Proposed rubric remains explicitly unconfirmed; Feature 002 next-bar-open/cost semantics were preserved.
- Audio review/transcription remains incomplete because no audio file was present in the workspace. No official challenge source, private account, or network execution was used.

### Offline validation results (2026-10-21)

- `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_challenge.py' -v`: **PASS**, 27 challenge tests.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: **PASS**, all 55 repository tests, including unchanged Feature 002 next-bar-open/cost regression tests.
- `python3 scripts/build_challenge_pair_registry.py --check`: **PASS**, derived registry matches raw source; raw=345, unique=345, duplicate pairs/excess=0, malformed=0.
- `python3 scripts/validate_sources.py`: **PASS**, 133 records/IDs/URLs; reviewed=71, not_started=51, in_progress=5, blocked=6. Full user-source SHA-256 validation and existing HTTPS validation both pass.
- `python3 scripts/validate_doc_links.py`: **PASS**, 147 relative Markdown links and 245 source citations; network links are not tested.
- `python3 -m py_compile scripts/*.py src/wallex_research/*.py tests/test_*.py`: **PASS**.
- `git diff --check`: **PASS**.
- Challenge source/config audit: **PASS**; full archived attachment and extracted raw pair block match exactly; 345 raw/unique pairs, no duplicates or malformed entries; raw-list SHA-256 `48a9d12c5660929bf2044c30535864eb4f008d0580aa3e0cf75f5b528242eba0`; cutoff remains null; execution scope offline-only.
- Offline source scan: **PASS**, no network request clients in new challenge modules; credential-pattern scan of 50 changed/untracked files: **PASS**.
- No dedicated Spec Kit Markdown validator exists in the repository; new spec/checklist links are covered by the document-link validator. External official sources were not fetched or validated.

## Transcript integration follow-up — 2026-10-21

- Added the inline user-supplied Persian cleaned working transcript as source `USER-WALLEX-HACKATHON-AUDIO-TRANSCRIPT`; verbatim text-file SHA-256 `c7831200b22590f5b076e43fbe6834d4c1905023abcd03297e20c34dcc732a5e`. It is not a raw ASR transcript or an audio file. No audio binary was available; listening/verification remains incomplete.
- Preserved timestamps and uncertain wording unchanged. The metadata says approximately `00:00:00–00:03:54`, while the last visible segment is `00:03:33`; speaker identity/affiliation and ambiguous words are not independently verified.
- Added a Persian synthesis and reconciliation table. The 80-million-Toman Wallex prize and separate prize are transcript-only/unverified; the earlier written user brief states 5,000,000 Toman but is not official. Video deadline/format/consequence, MCP capabilities/permissions and current eligible markets remain unverified.
- Official Wallex API documentation already present in the register supports only page-level documentation claims for market metadata/Spot/order schema; it does not verify contest permission or runtime. No MCP source is registered. No new API/MCP service, pair-list edit, code/trading behavior change, or live action was made.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: **PASS**, 55 tests; no replay/execution code changed.
- `python3 scripts/validate_sources.py`: **PASS**, 134 source records; reviewed=72, not_started=51, in_progress=5, blocked=6. Transcript file hash matches the local user-source record.
- `python3 scripts/validate_doc_links.py`: **PASS**, 155 relative Markdown links and 245 registered citations; external network links not tested.
- `python3 -m py_compile scripts/*.py src/wallex_research/*.py tests/test_*.py` and `git diff --check`: **PASS**.
- Transcript hash audit: **PASS**, `c7831200b22590f5b076e43fbe6834d4c1905023abcd03297e20c34dcc732a5e`; no audio binary was found.

## Credit-plan excerpt reconciliation — 2026-10-21

- Registered `USER-WALLEX-CREDIT-PLAN-EXCERPT` as user-provided/unverified. User identified the underlying source language as Persian, but supplied an English bullet summary only; preserved that distinction and SHA-256 `c93ed591efd00be2e084d35a6119239d7ac68cb5105551b479ebd6128dda8172` for the local summary artifact. Exact URL, publication/retrieval dates, official verification, eligible-market list, and readable permission table remain unknown/missing.
- Checked existing source register and `docs/api/margin-and-credit.md`: `CREDIT-INTRO` covers separate accounts; importantly, the already reviewed official `CREDIT-TYPES` record describes a general 30-day plan, daily fee and warning/liquidation levels. This does not verify the user excerpt's exact amounts/example, detailed outcomes, or applicability to Starcoach. No new official page was fetched and no endpoint/account was accessed.
- Added English/Persian reconciliation knowledge pages and a prominent warning; distinguished generic-plan excerpt claims from the prior user-provided challenge brief and from the offline Spot-only code. The brief's no-shortfall claim remains unverified and is not treated as a no-liability guarantee.
- Updated challenge policy metadata to label 5,000,000 Toman as a user-brief-reported allocation whose ownership/withdrawability, fee, liquidation and liability semantics are unknown. No fee rate, warning threshold, eligible market or permission was invented; no pair list or live behavior changed.
- Added `ReplayResult.limitations` disclosure and test assertions. Updated Feature 002 replay contract, data model, quickstart, and judge reproduction materials: generic starting cash/commission/slippage are not official ownership/cost terms, and credit fees/liquidation/special settlement are not modeled.
- Organizer questions are recorded in `docs/research/unresolved-questions.md`.
- Validation: full suite **PASS**, 55 tests; focused challenge suite **PASS**, 27 tests. Pair-registry consistency **PASS** (raw=345, unique=345, duplicates=0, malformed=0); synthetic CSV cadence audit **PASS** for structure only. Source register **PASS**, 135 records (reviewed=73, not_started=51, in_progress=5, blocked=6), including local source-summary hash verification. Documentation links/citations **PASS**, 163 local links and 248 registered citations; external URLs were not fetched. `py_compile` and `git diff --check` **PASS**.

## Smart98-mediated integration boundary (documentation research) — 2026-10-21

- Applied the current user requirement that any future Wallex API/MCP access intended for the trading agent must be mediated by Smart98; direct application-to-Wallex access is not an allowed fallback. This is a project architecture requirement from user context, not evidence of Smart98's technical capability.
- Repository inspection found existing docs for local/offline replay, official Wallex market/Spot metadata and a generated order-create schema; those API documents are not runtime, permission, or account-entitlement evidence. The order-create page is classified as a documented write operation and remains disabled.
- No authoritative Wallex MCP source or tool inventory is registered. Existing MCP mention is from the user-supplied, unverified transcript only.
- No Smart98 docs, runtime contract, tool catalog, transport, auth, schemas, or config are present in this checkout. The Arena Smart98 connector lookup returned `unsupported` for this session; it exposed no Smart98 tools and is not evidence that Smart98 itself is unavailable. No external Smart98/MCP page or production runtime was queried.
- Added a layer matrix and conditional data-flow proposal to `docs/api/challenge-architecture.md`; proposed a provider-neutral, read-only `MarketDataPort` (design label only, not an external tool/schema). Public market-data reads, account-sensitive reads, and order-changing tools are explicitly separated; the latter two remain disabled. Shadow is observation/decision-record-only.
- Expanded open evidence requests for MCP transport/registration, tool discovery/allow-listing, authentication/secret boundary, schemas, error/timeouts, logging/audit, Wallex MCP authority, Smart98 compatibility, and a non-production test plan. No adapter, credential, MCP installation, Smart98 config change, or network request was made.
- Validation: full offline suite **PASS**, 55 tests; source register **PASS**, 135 records (reviewed=73, not_started=51, in_progress=5, blocked=6); documentation links **PASS**, 174 local links / 248 registered citations; disabled-pair registry check **PASS** (345 unique, no duplicates/malformed); `py_compile` and `git diff --check` **PASS**. External URLs were not tested.

## Public trade WebSocket protocol pass and candle-recorder fix — 2026-10-23

- Re-read the four relevant official WebSocket pages with the public page reader: [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol), [MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade), [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) and [SOCKET-MIGRATION](https://developers.wallex.ir/docs/socket-migration). Existing `retrieved_at_utc` values (2026-10-21) and summaries were preserved; new observations were appended and indexed in `retrieval_history`; `reverification_snapshot_utc` records the new pass.
- Confirmed from the official pages that the public v2 protocol is JSON over `wss://api.wallex.ir/connection/websocket` with `{"id": 1, "connect": {}}`, per-channel `{"id": N, "subscribe": {"channel": "public:<SYMBOL>@trade"}}`, an empty `{"id": N, "subscribe": {}}` acknowledgement, publications under `push.pub.data`, and an empty-object `{}` heartbeat that must be echoed within 8 seconds (close code `3012`). Documented request errors are 102/103/105/106/107/108/109; documented close codes are 3005/3008/3012 (retryable) and 3500/3501 (client fault). One frame may contain several newline-separated messages.
- Confirmed from [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) that `wss://api.wallex.ir/ws` is version 1, deprecated but still documented as working, and that its first message is an Engine.IO-style `{sid, upgrades, pingInterval: 20000, pingTimeout: 30000}` object. The page describes the logical frame `["subscribe", {"channel": "..."}]` but not Socket.IO packet framing, which matches the 2026-10-23 operator evidence and is recorded as `D-019`.
- Retrieved the two legacy documentation paths previously cited by the recorder, `https://developers.wallex.ir/socket/trade` and `https://developers.wallex.ir/socket`; both returned the site's localized not-found body with no HTTP status exposed. Registered as new `inaccessible`/`blocked` sources and recorded as `D-020`; no deprecation reason or redirect target is inferred.
- **Root cause: strong hypothesis, not established.** The recorder connected to the deprecated v1 endpoint and wrote the logical v1 frame as a bare text frame; the documented v1 contract is a logical frame only, the endpoint's first message is Engine.IO-shaped, and no trade arrived. The Engine.IO handshake object was the single `malformed_or_unmatched_messages` entry. This explains every observation, but no retrieval or runtime evidence proves that the server ignored the frame for this reason; the alternative (a market with no trades) cannot be excluded from the old manifest. See the third-pass entry below and `D-022`. The recorder now implements only the documented v2 protocol with the existing `websockets` dependency (no new package, no SDK, no token).
- Bounded public runtime attempt: `wallex-candle-recorder --symbol BTCTMN --interval-seconds 60 --max-runtime-seconds 8 --max-reconnect-attempts 1` against the documented v2 endpoint. TCP to `api.wallex.ir:443` succeeded, the TLS handshake was reset, both attempts ended in `ConnectionResetError` (`connection_count: 0`, `connection_errors: 2`, `subscription_status: "not_attempted"`), no trade and no candle were produced. This indicates environment egress filtering; it is **not** evidence that the Wallex endpoint is down. Live verification remains `pending`.
- Code and tests: rewrote `src/wallex_agent/candle_recorder.py` for the v2 frames (message classification, heartbeat echo, bounded reconnects, documented fatal close codes, fail-closed subscription rejection, schema-2 manifest with separate transport/subscription state and per-class frame counters), and rewrote `tests/test_candle_recorder.py` with 41 deterministic offline tests. Manifest schema is now 2; the fields read by `wallex-data-audit` were preserved.
- Validation performed: `PYTHONPATH=src python -m pytest` → **PASS**, 373 tests + 26 subtests (baseline before changes: 339 + 26); `python -m pytest tests/test_candle_recorder.py -q` → **PASS**, 41 tests; `python -m compileall -q src tests scripts` → **PASS**; `python scripts/validate_sources.py` → **PASS**, 138 records (blocked=8, in_progress=5, not_started=51, reviewed=74); `python scripts/validate_doc_links.py` → **PASS**, 205 relative links and 290 register citations; `git diff --check` → **PASS**. No network access was used by tests or validators. No commit, push, branch switch or pull request was made.

## Senior review pass on the candle-recorder change — 2026-10-23

Second-pass review of the v2 recorder implementation. Five defects were found in the first revision and fixed; each has
a deterministic regression test.

1. **Duplicate buckets on restart (data-integrity, trader-facing).** Appending to an existing recording re-finalized an
   already-written bucket when a late trade for that bucket arrived after a restart. Reproduced: two runs produced
   `2026-10-23T10:00:00Z` twice, `wallex-backtest.load_candles` raised `BacktestError: candles must have unique,
   strictly increasing timestamps`, and `wallex-data-audit` returned `INVALID`/`DUPLICATE_TIMESTAMP`. Fixed by reading
   the last finalized bucket from the output tail at startup and treating it as a floor; such trades now increment
   `late_or_out_of_order_trades_ignored`. New manifest fields `resumed_from_existing_output` and
   `previous_last_closed_candle_utc` document the boundary. A file whose tail cannot be parsed is refused
   (fail closed) rather than appended to.
2. **`subscription_acknowledged` could be true without a confirmed subscription.** An acknowledgement frame carrying a
   wrong request `id` incremented the accepted-ack counter, so the manifest claimed `subscription_acknowledged: true`
   while `subscription_status` was still `pending`. Now only acknowledgements matching our command ids are counted, and
   the boolean is derived from `subscription_status`.
3. **Ctrl+C was recorded as `status: "failed"`.** Cancellation is an intentional stop; the manifest now reports
   `status: "stopped"` with `stop_reason: "cancelled"`, discards the partial candle and closes the socket.
4. **Tests depended on wall-clock timing.** Typical runs sat inside recording code longer than the 0.2–0.5 s run limits,
   so deadline tests were flaky. Eight of them now use an injected stepped clock; one test still exercises the real
   `asyncio` deadline. Recorder test time dropped from ~4.5 s to ~0.8 s.
5. **Numeric JSON payloads lost precision.** `json.loads` produced binary floats before `Decimal(str(...))`, so a
   numeric (non-string) `price` would have been rounded. Parsing now uses `parse_float=Decimal`; the documented string
   form was never affected. Manifest writes are also atomic (`os.replace`) so a concurrent reader cannot see a
   half-written status.

Review conclusions that required documentation rather than code changes: `volume` is one-sided (each trade added once,
maker/taker not double counted, no buy/sell split, `isBuyOrder` not reinterpreted); `open`/`close` follow arrival order
because the channel has no sequence number, with only a one-bucket exposure on those two fields; the 60-second silence
timeout is an implementation choice (`inferred`), not a documented value; and a restart always costs the first
post-restart bucket, which the audit reports as a potential gap.

Validation after the review: `PYTHONPATH=src python -m pytest` → **PASS**, 385 tests + 26 subtests;
`tests/test_candle_recorder.py` → **PASS**, 53 tests in ~0.8 s; `python -m compileall -q src tests scripts` → **PASS**;
`python -m pyflakes src/wallex_agent/candle_recorder.py tests/test_candle_recorder.py` → **PASS**;
`python scripts/validate_sources.py` → **PASS**, 138 records; `python scripts/validate_doc_links.py` → **PASS**, 205
links and 290 citations; `git diff --check` → **PASS**. Live verification remains `pending` (no network path to the
Wallex TLS endpoint from this environment). No commit, push, branch switch or pull request was made.

## Third retrieval pass: resolving the v1/v2 documentation conflict — 2026-10-23T13:46:00Z

- Trigger: an independent retrieval path reported `https://developers.wallex.ir/docs/socket-trade` as documenting only the legacy contract (`wss://api.wallex.ir/ws`, `["subscribe", {"channel": "MARKET@trade"}]`) and `docs/socket-intro` as describing legacy heartbeat behaviour, which appears to contradict this register's v2 summaries.
- Method: all four pages were fetched again from the official host in one UTC session, and **both chunks** of `socket-trade` and `socket-raw-protocol` were read, including the final chunk of `socket-trade` that no earlier pass had examined.
- Result: no documentation conflict. `socket-trade` documents three access methods on one page and lists **version 1 (deprecated) first**, then v2-with-SDK, then v2-without-SDK; `socket-intro` deliberately documents v2 rules followed by a "version 1 (deprecated) details" section. A truncated or top-only read of either page therefore shows exactly the legacy content the independent path reported. Recorded as `D-022`; each source keeps its earlier `retrieved_at_utc`, gains a third `retrieval_history` entry and a `reverification_note`.
- Newline splitting is **documented**, not assumed: the raw-protocol page's Python sample contains the comment «یک فریم ممکن است چند پیام داشته باشد» followed by `for line in raw.split("\n")`, and the Go sample uses `strings.Split(string(raw), "\n")`. Both were re-read in this pass.
- Because no live session was observed, the earlier root-cause sentence was downgraded from "established" to **strong hypothesis**, and the v2 runtime protocol remains `documented`, never `verified`. The bounded live attempt from this environment still fails at TLS (`ConnectionResetError`), so transport, application subscription, trade receipt and candle finalization all remain `pending`.

## Handshake-order review and PR #22 follow-up — 2026-10-23 (after publication)

- Scope: audit of the published recorder (`e53f9ab`, PR #22) against `/docs/socket-raw-protocol`, which was re-read in
  both chunks in this pass. The page defines numbered steps: `connect` first, `subscribe` second.
- Verified, and worth stating plainly: the page's own complete Python and Go samples send `connect` and `subscribe`
  back-to-back without waiting for the connect reply. The previous implementation therefore did **not** violate a
  documented requirement — it matched the sample. Recorded as `D-023` rather than as a defect claim.
- Changed anyway, as a stricter reading of the numbered steps: `subscribe` is now sent only after an `id`-validated
  connect reply, and a subscription acknowledgement is accepted only for the request id that was actually sent. This
  removes a real weakness — a subscribe ack could previously be accepted before the connection was validated, and any
  error arriving before the subscription ack was reported as a *subscription rejection*, whatever request id it
  answered.
- Also changed: an error is now attributed to the command it answers (connect error → retryable connection failure,
  subscription error → fatal rejection, any other id → counted and ignored); `failure_reason` is set where the failure
  is detected instead of being inferred from `subscription_status` afterwards; the retry budget resets on a validated
  subscription rather than on a trade, so a quiet market cannot exhaust it; transport frames are split on `\n` only,
  matching the published sample instead of `str.splitlines()`, which would split a JSON string containing `U+2028`; and
  the fatal-close check reads `ConnectionClosed.rcvd.code` instead of the deprecated flat `.code`.
- Every new guard is mutation-checked: removing the connect gate, the "subscribe was actually sent" guard, the error
  attribution fix, or the `\n`-only split each makes the corresponding test fail; the source was restored
  byte-identically afterwards.
- Evidence class: all of this is `verified_by_test` against scripted frames, plus `documented` page text. No live
  handshake, subscription acknowledgement or trade receipt was observed, so the runtime sequence remains `pending`.

## Connect-reply field validation — 2026-10-23 (PR #22 follow-up)

- Trigger: review observation that `classify_server_message()` accepted any `connect` object and `record_trades()` only
  compared `id`, so a reply `{"id": 1, "connect": {}}` — or one with mistyped fields — would authorize `subscribe`.
- Source re-read this pass: `/docs/socket-raw-protocol`, both chunks. The documented reply is
  `{"id": 1, "connect": {"client": "<uuid>", "ping": 25, "pong": true}}`; the field table gives `client` = "unique
  identifier of this connection", `ping` = "the server ping interval in seconds", `pong` = "if `true`, you must answer".
  The page also states that **every example on it is a real frame exchanged with the server**. The private-channel
  reply adds `expires`, `ttl` and `subs` to the same object.
- What the page does **not** state: requiredness, or the JSON type of each field beyond what the example shows. The SDK
  connection page linked from the socket overview documents SDK events only and no connect-reply fields.
- Decision, labelled as a client choice rather than a documented requirement: require a non-empty `client` string, a
  positive integer `ping`, and a boolean `pong`; allow extra fields. A reply that fails this is counted in a new
  `malformed_handshake_frames_received` counter, its reason is stored in `last_handshake_error`, no `subscribe` is sent,
  the recorder keeps waiting for a valid reply, and the eventual timeout carries the rejection reason. `pong: false` is
  accepted; the client still echoes the `{}` heartbeat whenever it arrives, per step 4.
- Tests: 70 → 89 recorder tests, including eleven missing-or-mistyped shapes at classification level, four end-to-end
  cases proving no `subscribe` and no subscribed state, a recovery case proving a rejected reply followed by a valid one
  still subscribes, and acceptance of the documented private extras with `pong` true and false. Mutation checks: removing
  the pre-subscribe gate fails five tests; removing the `pong`, `client` or `ping` check fails three, four and six
  respectively. Source restored byte-identically (`sha256 e320792c…`).
- Evidence class: `documented` (reply shape and field meanings) plus `verified_by_test` (the enforcement). No live
  session exists, so whether the real server always sends all three fields remains unverified.
