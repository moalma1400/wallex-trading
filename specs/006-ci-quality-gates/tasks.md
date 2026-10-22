# Tasks: Offline CI Quality Gates

**Input**: Design documents from `specs/006-ci-quality-gates/`

**Prerequisites**: spec.md, plan.md, research.md

## Phase 1: Setup

- [x] T001 Review repository instructions, constitution, existing Spec Kit artifacts, and current workflow/dependency configuration.
- [x] T002 Record scope, acceptance criteria, design decisions, and baseline validation evidence.

## Phase 2: User Story 1 - Pull request checks (Priority: P1)

**Goal**: Run the existing offline quality checks for pull requests to `main`.

**Independent Test**: Run each configured command locally with Python 3.12 and pytest installed.

- [x] T003 Add `.github/workflows/ci.yml` with least-privilege permissions and bounded execution time.
- [x] T004 Configure source validation, local documentation-link validation, compileall, pytest, and `git diff --check`.
- [x] T005 Confirm the workflow does not configure secrets, invoke Wallex/Smart98 endpoints, or perform live actions.

## Phase 3: User Story 2 - Main branch checks (Priority: P2)

**Goal**: Run the same checks for pushes to `main`.

- [x] T006 Configure and review pull-request and push triggers.
- [x] T007 Run the complete validation suite, review the final diff, and record whether a real GitHub Actions run has completed.

## Dependencies

- T001-T002 are complete before implementation.
- T003-T006 depend on the approved scope and can be implemented together.
- T007 depends on T003-T006.

## Completion Evidence

- [x] Hosted GitHub Actions run completed successfully on 2026-10-22 (workflow run 5, commit `f3aa86a1b8e9c1935084b66db3d52733766b1e6c`).
- [x] Source validator: 135 records; 135 unique IDs and URLs.
- [x] Documentation validator: 180 relative Markdown links resolved; 248 source citations matched register IDs and exact URLs (network links not tested).
- [x] Python compilation passed.
- [x] pytest: 145 passed, 24 subtests passed.
- [x] Event diff whitespace check passed.
- [x] No Wallex or Smart98 secrets are configured; no live trading actions are part of the workflow.
