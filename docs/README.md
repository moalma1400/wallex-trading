# Wallex documentation knowledge base

This documentation set is an evidence-backed snapshot, not a substitute for current official Wallex guidance. User-facing content is Persian-first; endpoint identifiers and original field names remain unchanged.

- [Persian trading knowledge](fa/README.md)
- [API topic summaries](api/overview.md)
- [Source register](research/source-register.yaml) — YAML 1.2-compatible JSON subset to permit offline validation using only Python's standard library.
- [Coverage matrix](research/coverage-matrix.md)
- [Discrepancies](research/discrepancies.md)
- [Open questions](research/unresolved-questions.md)
- [Research log](research/research-log.md)

Status words describe documentary review, not capability availability. `reviewed` means the official page content was inspected through the research tool; `not_started` means a URL appeared in official sitemap/navigation but the page content has not yet been reviewed. Repository research, validators, and tests do not access production endpoints or accounts. A user message reports a separate Smart98-mediated public read-only market-data report, but its body is unavailable; Arena did not independently invoke the tools. See the [Feature 005 evidence review](research/feature-005-smart98-evidence-review-2026-10-22.md).

Feature 003 local historical-data implementation: [English architecture note](api/historical-data-pipeline.md), [Persian-first summary](fa/historical-market-data.md), and [repository roadmap](../specs/ROADMAP.md). The code is offline-only; official documentation does not prove live availability or permission. Feature 005's narrowly scoped public Spot adapter remains gated on verified Smart98/tool contracts and does not authorize private or state-changing actions.
