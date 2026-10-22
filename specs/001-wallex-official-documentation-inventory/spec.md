# Feature Specification: Comprehensive Official Wallex Documentation Knowledge Base

**Feature Branch**: `001-wallex-official-documentation-inventory`
**Created**: 2026-10-21
**Status**: In Progress
**Input**: Establish a comprehensive, source-backed inventory and Persian-first knowledge base of public official Wallex trading-related documentation; this is a documentation research feature, not order execution.

## User Scenarios & Testing

### User Story 1 - Find authoritative Wallex sources (Priority: P1)

A future project contributor needs to determine what official Wallex documentation exists, where it lives, what it covers, whether it appears current or legacy, and when it was examined.

**Why this priority**: Source discovery and provenance are prerequisites for trustworthy trading decisions and all later design.

**Independent Test**: Inspect the machine-readable register and coverage matrix; every source discovered from official navigation, sitemaps, and verified official links within trading-related scope has a stable ID, exact URL, discovery path, status, and review evidence or an explicit gap classification.

**Acceptance Scenarios**:

1. **Given** an official documentation navigation or sitemap is examined, **When** its trading-related destinations are identified, **Then** each destination is inventoried or explicitly classified as inaccessible, duplicate, unresolved, or out of scope with rationale.
2. **Given** a contributor opens a source-register entry, **When** they check its provenance, **Then** retrieval time, URL, official domain, currentness classification, and research status are distinguishable from any publisher-provided date.

### User Story 2 - Understand documented trading operations (Priority: P2)

A future designer needs to understand documented markets, trading products, market constraints, fees, API operations, authentication, account information, order behavior, and data streams without relying on undocumented assumptions.

**Why this priority**: The organized knowledge base informs later specifications while avoiding unsupported capability claims.

**Independent Test**: Review each knowledge-base topic and verify material statements cite source IDs and direct official URLs, identifiers are copied accurately, and unknowns are explicitly listed.

**Acceptance Scenarios**:

1. **Given** a material API behavior or trading rule is summarized, **When** a reviewer follows its references, **Then** they can find the official source passage or see that the claim is labeled inference, historical example, assumption, or unresolved.
2. **Given** modern and legacy official sources disagree, **When** the discrepancy is reviewed, **Then** both source records, the exact difference, best-supported interpretation, and remaining uncertainty are preserved without silently merging them.

### User Story 3 - Validate and safely maintain the knowledge base (Priority: P3)

A contributor needs an offline way to detect malformed provenance records and to make changes without credentials or account-changing activity.

**Why this priority**: Repeatable structural validation and explicit safety constraints protect the integrity and boundaries of the research.

**Independent Test**: Run the local source-register validator without network access and inspect the repository diff for secrets and prohibited live trading actions.

**Acceptance Scenarios**:

1. **Given** the YAML register contains required fields for reviewed sources, **When** the offline validator runs, **Then** it exits successfully; malformed or incomplete reviewed entries cause a clear non-zero failure.
2. **Given** research is performed, **When** repository history and tool activity are reviewed, **Then** no API key is used, no production endpoint is called for experimentation, and no account-changing action occurs.

### Edge Cases

- Official pages are missing, blocked, broken, moved, duplicated, or only listed in a sitemap.
- The navigation and sitemap disagree or expose undocumented/legacy categories.
- The same topic appears in current-looking and legacy references with different routes, parameter names, authentication, payloads, or fee examples.
- Documentation has no publication date, version, rate-limit details, permission detail, or lifecycle guarantee.
- Examples contain historical values or apparent errors; these must not be promoted to current rules.
- A claim depends on a product or market being enabled for a particular user or account.
- The source-register validator runs offline and must not silently make a network request.

## Requirements

### Functional Requirements

- **FR-001**: The project MUST inventory every discoverable public official documentation page within the agreed trading-related scope found through official navigation, documentation tables of contents, public sitemaps/robots metadata where available, and verified official links; each page MUST be inventoried or explicitly classified with a reason.
- **FR-002**: The inventory MUST include every API category linked from the official documentation navigation and record pages that cannot be reviewed.
- **FR-003**: Every source record MUST have a stable identifier, title when available, exact URL, official domain, documentation type, discovery path, UTC retrieval time, currentness classification, topic/features, evidence notes, and research status; publisher dates MUST remain unset when not stated.
- **FR-004**: Every material API behavior and trading rule included in the knowledge base MUST cite a source ID and exact source URL; no unverified behavior may be stated as fact.
- **FR-005**: The knowledge base MUST organize verified and clearly qualified material on market discovery, trading products, market data, orders, order states, fees, precision/minimum constraints, authentication/key permissions, balances, REST, and WebSocket topics when officially documented.
- **FR-006**: User-facing trading knowledge MUST be Persian-first and preserve original English API identifiers, fields, methods, paths, headers, and enum values exactly.
- **FR-007**: The repository MUST maintain a coverage matrix showing source ID, exact URL, review status, linked knowledge-base page, validation status, and known gaps, with supported counts for discovered, reviewed, inaccessible, duplicate, out-of-scope, and unresolved entries.
- **FR-008**: The repository MUST maintain discrepancy and unresolved-question registers that preserve conflicting official claims, legacy evidence, inferred behavior, missing documentation, evidence dates, and next authoritative confirmation needed.
- **FR-009**: The source inventory MUST be machine-readable and pass an offline structural validator that checks schema/provenance fields and reviewed-source completeness.
- **FR-010**: All major deliverables MUST trace through the feature specification, plan, tasks, and validation evidence; a final coverage/quality review MUST report gaps instead of claiming unsubstantiated completeness.
- **FR-011**: No real API key may be created or used, no production endpoint may be called to test documentation, and no live trade, order cancellation, transfer, withdrawal, or account-setting change may occur.
- **FR-012**: The feature MUST not implement a trading strategy or production execution system, and MUST NOT assert profitability or safety.
- **FR-013**: Repository governance MUST explain future feature specification/review, source reporting, credential hygiene, and the current-phase boundary.
- **FR-014**: All completed deliverables MUST be committed and published to the session's authorized private repository branch, with a reviewable pull request left unmerged where permissions allow.

### Key Entities

- **Official source**: A page, dataset, or specification with a verified official Wallex domain and discovery lineage.
- **Coverage item**: A discovered documentation destination and its review/accessibility status, linked summary, and gaps.
- **Evidence claim**: A concise statement connected to one or more exact source URLs, with evidence class and confidence.
- **Discrepancy**: A material inconsistency between official records or versions with both citations and unresolved interpretation.
- **Unresolved question**: A specific operational or policy question for which authoritative evidence is missing or unclear.

## Success Criteria

### Measurable Outcomes

- **SC-001**: Every trading-related page surfaced by examined official navigation/sitemap/link inventories appears in the register or in a documented exclusion/accessibility record; there are zero unexplained omissions in the coverage matrix.
- **SC-002**: 100% of source records marked `reviewed`, `validated`, or `blocked` contain the applicable URL, official domain, UTC retrieval time, discovery path, evidence notes, and status fields; publisher dates are recorded only when the page supplies them.
- **SC-003**: 100% of material factual claims in knowledge-base pages link to at least one source ID and direct URL; any unconfirmed interpretation is explicitly labeled.
- **SC-004**: All official navigation-linked API categories are represented in the coverage matrix, including inaccessible or not-yet-reviewed pages.
- **SC-005**: The offline validator exits zero on valid committed inventory and non-zero on a controlled malformed fixture; no network request is made by the validator.
- **SC-006**: The final review reports actual counts by status, discrepancies, unresolved questions, and limitations; it makes no unsupported claim of full review.
- **SC-007**: No production API call, credential use, or account-changing action is made during the feature.

## Assumptions

- Public Wallex marketing and developer documentation may change without a visible version or publication date; retrieval time is recorded separately.
- The official navigation, verified official links, sitemap and other public metadata define the discoverable page universe for the research snapshot; results are a dated snapshot, not a guarantee against hidden or dynamically generated material.
- User-facing trading knowledge is Persian-first; governance and major SDD artifacts are clear English.
- No strategy, asset universe, timeframe, risk appetite, or execution architecture is defined in this feature.
- Repository publication must follow the active Arena branch constraint; the existing private repository is reviewed rather than re-created, and no force-push or visibility change is permitted.
