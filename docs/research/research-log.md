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
