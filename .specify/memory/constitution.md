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
The current phase includes continued official-documentation research and specification, plus local, offline-only, strategy-neutral research tooling. Permitted implementation is limited to synthetic or user-supplied local fixtures for data models, validation, deterministic replay, backtesting, risk checks, and paper-ledger simulation. No code may call Wallex or Smart98, retrieve public data automatically, connect to an account or live feed, or submit, modify, or cancel real orders. Strategy selection and user-specific assets, periods, fees, leverage, capital, and risk tolerances remain unset; any required parameters must be explicitly supplied by the caller. Spot-only simulation is permitted; leveraged or margin execution is not.

### IX. Jurisdiction and Compliance Gate
No real exchange access or use may be enabled by this project. Any future proposal must first specify the applicable jurisdiction and purpose, and obtain independent, current legal/compliance review covering sanctions, access restrictions, exchange eligibility, and local law. This is a gate, not a guarantee of legality or individualized legal advice. A successful code test or public API contract does not satisfy this gate.

## Development and Research Constraints

- Use official Wallex sources as primary evidence; identify non-official sources distinctly if ever needed.
- Keep user-facing trading knowledge Persian-first while preserving exact English API identifiers, paths, headers, fields, and enum values.
- Do not copy entire source pages. Write concise, structured original summaries.
- Record inaccessible pages, broken navigation, contradictory claims, and open questions honestly.
- Offline software must be deterministic, network-free, and use only caller-supplied local data. Do not embed example market, timeframe, fee, capital, strategy, leverage, or risk settings as defaults.
- Keep Smart98 and exchange integrations behind future, unspecified interfaces; do not invent their contracts or add adapters.
- Avoid unnecessary packages, services, databases, bots, credentials, or infrastructure.
- No license is selected yet; do not add one without owner approval.

## Governance

This constitution governs all specifications, plans, tasks, research, implementation, and review in this repository. Any feature that conflicts with it must be revised or explicitly deferred; the constitution itself can be amended only through a reviewed, documented change. Every pull request must check evidence quality, credential hygiene, trading-boundary compliance, and traceability. Acceptance criteria are not considered met without recorded validation evidence. Where user decisions are required, document the question and do not substitute an invented requirement.

**Version**: 1.1.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-21

### Amendment record

Version 1.1.0 implements the owner's explicit scope expansion: local offline research/data-quality/replay/backtest/paper-ledger code is now permitted under the safeguards above. It does not authorize live exchange use, network data retrieval, account access, strategy selection, or leveraged execution. A jurisdiction-specific legal/compliance review is required before any future real exchange use.
