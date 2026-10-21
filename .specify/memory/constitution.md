# Wallex Trading Constitution

## Core Principles

### I. Specification Before Implementation
Specifications and measurable acceptance criteria precede implementation. Scope, assumptions, and exclusions must be explicit; changes to agreed requirements are recorded and reviewed.

### II. Evidence-First Documentation
Every material factual claim about Wallex must link to an identifiable, authoritative source. Distinguish verified observations, statements made by official documentation, inference, assumptions, and unresolved questions. Record conflicts instead of silently reconciling them.

### III. Currency and Provenance
Prefer official documentation currently presented by Wallex. Preserve useful legacy evidence with a clear legacy label. Record exact URLs, retrieval time in UTC, publication/update dates only when supplied, and currentness confidence. Do not infer undocumented behavior.

### IV. Traceability and Reviewability
Changes must trace from specification through plan, tasks, artifacts, and validation evidence. Research inventories and validation should be reviewable, reproducible, and explicit about gaps.

### V. Financial Credential and Personal-Data Protection
Never commit API keys, access tokens, cookies, account identifiers, personal data, or secrets. Do not create or use a real Wallex API key for documentation research. Use placeholders only and minimize any sensitive examples.

### VI. Explicit Approval for Account-Changing Actions
No live orders, cancellations, amendments, transfers, withdrawals, or other account-changing actions may be made without separate, explicit user approval for the specific activity. Public documentation research must not call production API endpoints to experiment.

### VII. Risk Before Automation
Document risk controls, permissions, failure handling, and a defined test process before implementing automated trading. A documented capability is not proof of runtime availability, authorization, safety, or suitability. Do not claim a strategy is profitable or safe without appropriate evidence.

### VIII. Current Phase Boundary
The current phase is official-documentation research and SDD preparation only. Strategy implementation, order simulation against Wallex, and production trading execution are excluded.

## Development and Research Constraints

- Use official Wallex sources as primary evidence; identify non-official sources distinctly if ever needed.
- Keep user-facing trading knowledge Persian-first while preserving exact English API identifiers, paths, headers, fields, and enum values.
- Do not copy entire source pages. Write concise, structured original summaries.
- Record inaccessible pages, broken navigation, contradictory claims, and open questions honestly.
- Avoid unnecessary packages, services, databases, bots, credentials, or infrastructure.
- No license is selected yet; do not add one without owner approval.

## Governance

This constitution governs all specifications, plans, tasks, research, implementation, and review in this repository. Any feature that conflicts with it must be revised or explicitly deferred; the constitution itself can be amended only through a reviewed, documented change. Every pull request must check evidence quality, credential hygiene, trading-boundary compliance, and traceability. Acceptance criteria are not considered met without recorded validation evidence. Where user decisions are required, document the question and do not substitute an invented requirement.

**Version**: 1.0.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-21
