---
description: "Task list for official Wallex documentation inventory"
---

# Tasks: Comprehensive Official Wallex Documentation Knowledge Base

**Input**: Feature documents in `specs/001-wallex-official-documentation-inventory/`
**Prerequisites**: [plan.md](plan.md), [spec.md](spec.md), [research.md](research.md), [data-model.md](data-model.md)
**Status note**: Checkboxes reflect work performed in this session, not a claim that all acceptance criteria are complete. The research snapshot remains incomplete: 88 sitemap pages have not been content-reviewed.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Independent work can proceed in parallel.
- **[Story]**: User story from the specification.

## Phase 1: Setup (complete)

- [x] T001 Verify private repository owner, default branch, status, and existing contents without reinitializing it.
- [x] T002 Install the pinned official Spec Kit CLI and initialize canonical files in a clean temporary directory without `--force`.
- [x] T003 [P] Review and retain canonical templates/scripts/integration files; set Generic skills mode and record the setup.
- [x] T004 Establish constitution, governance docs, Persian-first README, secret hygiene, and `.env.example` placeholder.
- [x] T005 [P] Create feature specification and requirements checklist before research artifacts.

## Phase 2: Foundational discovery and scope (complete for first snapshot)

- [x] T006 Verify official Spec Kit release `v1.2.2`, installation instructions, Generic integration syntax, generated workflow/skills, and CLI version.
- [x] T007 Inspect official Wallex homepage, current-looking developer introduction, legacy API page, and official sitemap.
- [x] T008 Transcribe all 115 sitemap-listed developer `/docs` destinations into unique source-register records.
- [x] T009 [P] Record exact public sources, UTC snapshot, observed failures, publisher-provided dates when visible, and no invented dates.
- [x] T010 Capture the legacy API navigation categories and mark the Wallgate commerce section as out of trading-summary scope.

## Phase 3: User Story 1 — Find authoritative sources (Priority: P1)

**Goal**: Give contributors an auditable source inventory and page-level coverage.
**Independent Test**: Compare every URL in the retrieved official sitemap with one exact register/matrix row; check status and discovery path.

- [x] T011 [US1] Create schema documentation for the machine-readable source register in `docs/research/README.md`.
- [x] T012 [US1] Add stable IDs, exact URLs, source types, retrieval snapshot, currentness labels, topics, evidence notes, relations, and review statuses in `docs/research/source-register.yaml`.
- [x] T013 [US1] Generate coverage rows for all 115 sitemap page destinations, with discovered/reviewed/not-started/inaccessible/duplicate/out-of-scope counts in `docs/research/coverage-matrix.md`.
- [x] T014 [US1] Record the 27 inspected sitemap pages and distinguish 88 sitemap-listed pages not yet content-reviewed.
- [x] T015 [US1] Record 404/API-document/robots exploratory attempts with actual observed failure and do not count guessed URLs as official discoveries.
- [ ] T016 [US1] Inspect each remaining `not_started` page (88 at snapshot) and update title/content/status, official navigation category, exact gaps, and summary.
- [ ] T017 [US1] Follow official navigation/verified links from each reviewed page to find additional support, policy, fee, and operational notices beyond the sitemap; inventory or explain exclusions.
- [ ] T018 [US1] Validate every page's currentness and relevant schema/claims against authoritative current evidence; retain legacy/historical status where applicable.

## Phase 4: User Story 2 — Understand documented operations (Priority: P2)

**Goal**: Provide Persian-first, source-linked technical summaries without unsupported claims.
**Independent Test**: Sample material claims and verify the direct source, exact API identifier, evidence class, and explicit unresolved status.

- [x] T019 [P] [US2] Summarize reviewed Spot, market discovery, account key, fee, order, depth, candle, OTC, Margin, credit, WebSocket topics in `docs/fa/` and `docs/api/`.
- [x] T020 [US2] Preserve current-looking/legacy differences and exact field/path variants; create the discrepancy register.
- [x] T021 [US2] Record unknown operational questions, missing fee display, access limits and compliance caveats in `docs/research/unresolved-questions.md`.
- [x] T022 [US2] Include official U.S. Treasury/OFAC sanctions sources as clearly external legal/compliance context; avoid individualized legal advice or a conclusion about a particular user's circumstances.
- [ ] T023 [US2] Review all remaining official Swagger/OpenAPI artifacts and document endpoint request/response fields, required permissions, enums, limits, status lifecycle, pagination and errors.
- [ ] T024 [US2] Review official customer support/FAQ/terms/trading restrictions/risk warnings and all in-scope fee/market-rule material reached from official navigation.
- [ ] T025 [US2] Complete source-by-source discrepancy reconciliation (modern vs legacy, API vs product/help docs, time-bound fee promotions) and record evidence dates.
- [ ] T026 [US2] Create a final coverage and quality review showing actual page status counts, sources of counts, remaining gaps, and acceptance-criteria disposition.

## Phase 5: User Story 3 — Validate and safely maintain (Priority: P3)

**Goal**: Provide offline structural and internal-link checks while maintaining no-live-action boundaries.
**Independent Test**: Run both validators offline, run diff check, inspect result and final diff for credentials/unsupported claims.

- [x] T027 [P] [US3] Implement dependency-free source-register validator in `scripts/validate_sources.py`.
- [x] T028 [P] [US3] Implement offline relative Markdown link checker in `scripts/validate_doc_links.py`; clearly exclude external URLs from network checks.
- [x] T029 [US3] Run validators, fix all failures, and perform a controlled malformed-register test proving a non-zero failure.
- [x] T030 [US3] Review all Markdown citations and final diff for source accuracy, broken internal links, credentials, personal data, and claims that imply live runtime verification.
- [x] T031 [US3] Reconcile final matrix counts with source-register records and update `research-log.md`/checklists with validation evidence.

## Phase 6: Publication and review

- [x] T032 Push the initial scaffold commit only to the fixed Arena session branch; do not change `main` or create a new branch.
- [ ] T033 Commit and push research changes to `arena/81f9fa39-wallex-trading` after validation.
- [ ] T034 Open a pull request to `main` if GitHub permissions permit; include actual source counts/limitations and leave unmerged.
- [ ] T035 Verify remote commit SHA, private visibility, PR status, and final local git status; report any real permission blocker.

## Dependencies and execution order

- Setup and source discovery precede detailed research summaries.
- T016–T018 and T023–T026 are the major remaining content-review dependencies; do not declare comprehensive content coverage until they are complete.
- T029–T031 depend on the current artifact set; run again after source coverage grows.
- T033–T035 depend on validation and final diff review. The fixed session branch is used despite the requested descriptive research branch, because Arena branch tracking cannot be changed in this task.

## Implementation strategy

This session delivers the initial source inventory, first representative research pass, discrepancy/open-question registers and offline validators. Continue with page batches grouped by API category; update source records/matrix alongside summaries. Only set `research_status: validated` after checking source claims and required fields; a successful structural validator alone is insufficient.
