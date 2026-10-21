# Research records and schema

## Source register

`source-register.yaml` is emitted as JSON syntax, which is a valid YAML 1.2 subset. This deliberate format permits parsing and validation offline with Python's standard library, without installing runtime dependencies.

| Field | Meaning |
|---|---|
| `source_id` | Stable, unique identifier used for citations in repository documents. |
| `title` | Exact title when exposed by the retrieved page; `null` if not available/reviewed. |
| `url` | Exact canonical URL actually discovered/attempted; never silently rewritten. |
| `official_domain` | Domain whose official ownership/status is supported by evidence; for external official legal sources, the relevant government domain. |
| `documentation_type` | Source class (API reference, sitemap, fee page, announcement, government legal source, etc.). |
| `discovery_path` | Direct source, sitemap, internal official link, or precise exploratory route. |
| `retrieved_at_utc` | Exact UTC time the research session compiled this retrieved-source snapshot, separate from publication date. The page reader did not expose per-request timestamps; `retrieval_time_note` records this limitation, so this value is not represented as an individual fetch timestamp. |
| `published_or_updated_at` | Publisher-provided date only; `null` when none was shown. |
| `currentness_classification` | `current`, `legacy`, `unclear`, `changed`, `inaccessible`, or `superseded`; a research classification, not runtime proof. |
| `topics` | Subject tags. |
| `claims_summary` | Concise content or discovery-only summary; sitemap listing is not page-body review. |
| `confidence_and_evidence_notes` | What was observed and limits of inference. |
| `related_source_ids` | Other records confirming, contradicting, or contextualizing this source. |
| `research_status` | `not_started`, `in_progress`, `reviewed`, `validated`, or `blocked`. `reviewed` means the content was inspected; it is not exhaustive endpoint validation. |

Run `python3 scripts/validate_sources.py` to validate offline. This validates structure and provenance presence, not factual truth, accessibility, or remote currentness.

## Coverage scope

The coverage matrix enumerates the exact 115 destination URLs returned by the official developer sitemap during the snapshot. The modern docs content pages are tracked individually. The legacy API reference is a single long page with an embedded navigation; it is tracked as one source and its major navigation sections are described separately. Official Wallex website, fee, help-center and regulatory sources are listed outside the 115 sitemap-page count.
