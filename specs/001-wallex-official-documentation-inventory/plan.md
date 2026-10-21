# Implementation Plan: Comprehensive Official Wallex Documentation Knowledge Base

**Branch**: `arena/81f9fa39-wallex-trading` (session branch fixed by Arena) | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification in `specs/001-wallex-official-documentation-inventory/spec.md`

> Workflow note: Spec Kit v1.2.2 generated canonical templates/scripts/skills. No Arena-native Spec Kit integration is verified; the generated `speckit-*` skill procedures were applied manually. The available Arena branch policy prohibits creating the requested descriptive feature branch or pushing `main`; publication is restricted to the existing session branch and review PR.

## Summary

Create a traceable snapshot of Wallex's public trading-related documentation landscape, prioritize official navigation/sitemap discovery, summarize inspected sources in Persian, preserve exact API identifiers, and report discrepancies/open questions. Use a JSON-compatible YAML source register for dependency-free offline validation, a page-level coverage matrix, and concise topic summaries. Do not call any Wallex API, use credentials, or implement trading behavior. The first pass inventories 115 developer sitemap destinations and has reviewed 27 page bodies; 88 remain not started.

## Technical Context

**Language/Version**: Markdown, JSON-compatible YAML, Python 3.11 standard library only
**Primary Dependencies**: None at runtime; official Spec Kit CLI used for scaffold generation only
**Storage**: Version-controlled Markdown and source register
**Testing**: `python3 scripts/validate_sources.py`; `python3 scripts/validate_doc_links.py`; `git diff --check`; Spec Kit CLI checks
**Target Platform**: Any Git checkout with Python 3.11+ for local validation
**Project Type**: Documentation / SDD research project
**Performance Goals**: Offline validation of source structure and local links in seconds
**Constraints**: No credentials, no production API tests or account changes, no unverified source claims, Persian-first knowledge base, report incomplete coverage honestly
**Scale/Scope**: 115 page destinations from the retrieved official developer sitemap plus official website/fee pages, one legacy API reference, and separate official-government compliance sources; first pass does not exhaustively review all discovered pages.

## Constitution Check

- Specifications and acceptance criteria precede implementation: **PASS** (spec, quality checklist, plan, and task list exist before documentation artifacts).
- Authoritative evidence, source classes, discrepancies, and UTC provenance: **PASS WITH OPEN WORK** (register records exact URLs and retrieval snapshot; many discovered pages not reviewed).
- Traceability from spec through plan/tasks/artifacts/validation: **PASS** (see tasks and linked artifacts).
- Credentials, personal data, live actions, and strategy boundary: **PASS** (no key, no account/API calls, no trading implementation).
- Risk before automation/profitability claims: **PASS** (no strategy/automation; Margin and compliance risk flagged).
- Language policy: **PASS** (Persian-first user knowledge; English major SDD artifacts and exact API identifiers).
- Publication boundary: **PASS WITH CONSTRAINT** (private repo already exists; owner/default branch verified; commits pushed only to session branch; no main push/branch switch).

## Research and Design Decisions

1. Use official site navigation and sitemap as the discoverability source. Sitemap listing confirms a page URL exists in the sitemap, not its content or runtime validity.
2. Keep each exact URL in its own record. Mark the 88 uninspected bodies `not_started`; do not fabricate titles, claims, or publisher dates for them.
3. Use JSON syntax in `source-register.yaml` (valid YAML 1.2 subset) so Python's standard library can parse it offline. Schema details are documented in `docs/research/README.md`.
4. Keep current-looking developer docs and legacy API reference separate. Classify the legacy reference based on older examples and observed contract differences, not an official end-of-life claim.
5. Record the officially accessible fee schedule with its blank displayed maker/taker table as a gap. Keep time-limited promotional claims historical/unknown-currentness; do not publish a made-up current fee.
6. Include official Treasury/OFAC sources as clearly external legal/compliance context because they are material operational risks; do not treat them as Wallex documentation or as personal legal advice.
7. Do not create `.env` containing a secret or connect to API/WebSocket. The example environment file is a blank placeholder only.
8. Since the repository had one existing README, do not run Spec Kit init with `--force`; initialize canonically in a temporary clean directory and copy/review generated project artifacts into the existing repo.

## Project Structure

```text
.specify/                                      # canonical Spec Kit templates/scripts/workflow/config
.agents/skills/                                # generic agent-neutral generated Spec Kit skills
specs/001-wallex-official-documentation-inventory/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
├── spec-kit-setup.md
└── checklists/
docs/
├── fa/                                        # Persian trading knowledge
├── api/                                       # endpoint/product topic summaries
└── research/                                  # register, coverage, discrepancies, gaps, log
scripts/validate_sources.py                    # offline source register validator
scripts/validate_doc_links.py                   # offline internal-link validator
```

**Structure Decision**: A documentation-only repository with two small stdlib validators. No codebase runtime, database, external dependencies, or live integration is needed.

## Delivery Phases

1. **Discovery**: verify repo, Spec Kit release and integration, source navigation/sitemap, exact page destinations.
2. **Collection**: inspect source content; record URLs, retrieval metadata, dates, claims, source relations, and access failures.
3. **Reconciliation**: compare current-looking docs, legacy reference, website fee/support text, record discrepancies and questions.
4. **Organization**: maintain Persian product knowledge and English/API-specific technical pages linked by source IDs.
5. **Validation**: run offline register and internal-link checks, inspect review statuses/counts, compare source references, review for unsupported claims/secrets.
6. **Publication**: commit and push only on current Arena branch, open unmerged review PR if GitHub permits; do not push main or create/switch branches under the session's fixed branch constraints.

## Complexity Tracking

No constitution violations or additional infrastructure are justified. The two Python validators use only the standard library.
