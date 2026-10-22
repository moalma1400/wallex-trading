# Tasks: Offline CI Quality Gates

**Input**: Design documents from `specs/006-ci-quality-gates/`

**Prerequisites**: spec.md, plan.md, research.md

## Phase 1: Setup

- [x] T001 Review repository instructions, constitution, existing Spec Kit artifacts, and current workflow/dependency configuration.
- [x] T002 Record scope, acceptance criteria, design decisions, and baseline validation evidence.

## Phase 2: User Story 1 - Pull request checks (Priority: P1)

**Goal**: Run the existing offline quality checks for pull requests to `main`.

**Independent Test**: Run each configured command locally with Python 3.12 and pytest installed.

- [ ] T003 Add `.github/workflows/ci.yml` with least-privilege permissions and bounded execution time.
- [ ] T004 Configure source validation, local documentation-link validation, compileall, pytest, and `git diff --check`.
- [ ] T005 Confirm the workflow does not configure secrets, invoke Wallex/Smart98 endpoints, or perform live actions.

## Phase 3: User Story 2 - Main branch checks (Priority: P2)

**Goal**: Run the same checks for pushes to `main`.

- [ ] T006 Configure and review pull-request and push triggers.
- [ ] T007 Run the complete validation suite, review the final diff, and record whether a real GitHub Actions run has completed.

## Dependencies

- T001-T002 are complete before implementation.
- T003-T006 depend on the approved scope and can be implemented together.
- T007 depends on T003-T006.

## Completion Evidence

Record local command results and the GitHub Actions run result separately. Do not describe a local test run as proof that the hosted workflow executed successfully.
