# Research data model

This is a documentation model for source provenance and coverage, not a trading runtime schema.

## Source record

`docs/research/source-register.yaml` is JSON syntax valid as YAML 1.2 and contains a top-level `schema_version`, `format_note`, `research_snapshot_utc`, and `sources` array.

| Field | Type | Rule |
|---|---|---|
| `source_id` | string | Stable unique identifier; referenced by Markdown and related sources. |
| `title` | string or null | Exact retrieved page title or null if unknown. Never generate a factual title from a path slug. |
| `url` | string | Exact absolute HTTPS URL discovered/attempted. |
| `official_domain` | string | Domain provenance label; host must equal or be a subdomain of it. |
| `documentation_type` | string | Page/source class (API reference, product guide, support page, etc.). |
| `discovery_path` | string | Official navigation/sitemap/internal link or exact exploratory route. |
| `retrieved_at_utc` | UTC ISO-8601 timestamp | Retrieval snapshot; separate from publisher metadata. |
| `published_or_updated_at` | date/time or null | Set only when the source states a date. |
| `currentness_classification` | enum | `current`, `legacy`, `unclear`, `changed`, `inaccessible`, `superseded`. |
| `topics` | string array | Searchable topical labels. |
| `claims_summary` | string | Concise source evidence or discovery-only status; not a substitute for detailed source citation. |
| `confidence_and_evidence_notes` | string | What was read and limitations/confidence. |
| `related_source_ids` | string array | Known corroborating/contradicting/related IDs. |
| `research_status` | enum | `not_started`, `in_progress`, `reviewed`, `validated`, `blocked`. |

## Coverage status semantics

- `reviewed`: content was retrieved and inspected; not necessarily every endpoint/claim exhaustively reviewed.
- `not_started`: URL discovered but page content not reviewed.
- `blocked`: direct access attempt failed or returned a not-found/access restriction; the observed failure is recorded.
- `validated`: a later review independently checked page content and relevant claims/schema; no source in the current sitemap inventory has this stronger status yet.
- `duplicate`, `out_of_scope`, and `inaccessible` are coverage-matrix categories/rationales, not substitutes for provenance records.

## Claim / discrepancy model

Each topic summary links source IDs and exact URLs inline. A discrepancy has an ID, topic, evidence from each side, current interpretation, and unresolved question. A missing field or omitted behavior must remain an unknown rather than an assumed default.
