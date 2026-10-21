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
