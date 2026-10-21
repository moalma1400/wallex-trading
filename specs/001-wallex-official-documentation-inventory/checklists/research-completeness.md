# Research and coverage quality checklist

**Feature**: [spec.md](../spec.md)
**Coverage matrix**: [docs/research/coverage-matrix.md](../../../docs/research/coverage-matrix.md)
**Snapshot**: 2026-10-21 UTC

## Discovery

- [x] Main website, developer docs, and legacy API reference were examined.
- [x] Official developer sitemap was retrieved and the 115 page URLs were represented in the source register and coverage matrix.
- [x] Major legacy API navigation categories were recorded.
- [x] Official homepage fee/product claims and direct fee page were examined.
- [x] Official Treasury/OFAC compliance context was separately sourced and labeled non-Wallex.
- [ ] All official support, help, terms, notices and FAQ navigation has been exhaustively discovered; one candidate fee-help URL returned 404 and current destination is unresolved.

## Content review

- [x] 27 of 115 sitemap page bodies were inspected across key trading categories.
- [x] The legacy API reference's seven chunks were inspected for navigation and broad section content; endpoint-specific review is incomplete.
- [x] Current/legacy behavior differences are recorded without silently merging contracts.
- [x] Unknown fee values, precision/minimum limits, order states, auth details, and WebSocket guarantees remain explicit questions.
- [ ] All 88 remaining sitemap page bodies and linked Swagger/OpenAPI files have been reviewed.
- [ ] All material API behavior in the full documentation landscape has been reconciled and validated.
- [ ] Complete support and operating restrictions have been reviewed from direct official pages.

## Provenance and validation

- [x] The source register is machine-readable JSON syntax valid as YAML 1.2 and has a documented schema.
- [x] `python3 scripts/validate_sources.py` passed: 127 records, 127 unique IDs/URLs; statuses `reviewed=34`, `not_started=88`, `blocked=5`.
- [x] A malformed temporary register fixture failed as expected with exit code 1.
- [x] `python3 scripts/validate_doc_links.py` passed: 45 internal local Markdown links resolved and 139 source citations matched exact register IDs/URLs; external URLs were not network-checked.
- [x] `git diff --check` passed at the review point.
- [ ] Remote external links and all 115 page URLs have not been independently checked for current HTTP availability; no remote URL rewriting was performed.
- [ ] Final publication commit, remote verification, PR creation and clean-tree check remain pending until the final push attempt.

## Safety and completion

- [x] No API key was created or used; no account or production API was accessed.
- [x] No live WebSocket was opened, no trade/order action, transfer, withdrawal, or settings change was performed.
- [x] No strategy or return claim was implemented.
- [x] Official sanctions risk was documented with a non-legal-advice caveat.
- [ ] Feature is **not complete**: content coverage is partial; 88 pages plus broader official support/navigation research remain.
