# Feature Specification: Offline CI Quality Gates

**Feature Branch**: `arena/post-merge-ci`
**Created**: 2026-10-22
**Status**: Draft for review
**Input**: Add a small GitHub Actions workflow to run the repository's existing offline validation suite.

## User Scenarios & Testing

### User Story 1 - Catch repository regressions on pull requests (Priority: P1)

As a contributor, I want the existing offline checks to run automatically for pull requests targeting `main), so that broken source registers, local documentation links, Python syntax, or tests are detected before review.

**Why this priority**: These checks already exist and pass locally; automating them makes review evidence repeatable.

**Independent Test**: Inspect the workflow and run each configured command locally under Python 3.12 with pytest installed.

**Acceptance Scenarios**:
1. **Given** a pull request targeting `main`, **When** GitHub Actions runs, **Then** source validation, documentation-link validation, Python compilation, pytest, and `git diff --check` are executed.
2. **Given** any required check fails, **When** the workflow runs, **Then** the job fails rather than reporting success.
3. **Given** the workflow runs, **When** tests execute, **Then** they do not call Wallex or Smart98 production services or submit orders.

### User Story 2 - Verify changes to main (Priority: P2)

As a maintainer, I want the same checks to run on pushes to `main), so that the resulting main branch is checked after changes land.

**Independent Test**: Confirm the workflow trigger includes pushes to `main` and uses the same job steps as pull requests.

## Edge Cases

- Missing or malformed source-register data must fail the relevant validator.
- Broken relative Markdown links must fail the documentation-link validator.
- Test failures or Python syntax errors must fail the job.
- CI must not require Wallex credentials, Smart98 credentials, secrets, or live network access to target services.

## Requirements

### Functional Requirements

- **FR-001**: The workflow MUST run on pull requests targeting `main` and pushes to `main`.
- **FR-002**: The workflow MUST use Python 3.12.
- **FR-003**: The workflow MUST run `python scripts/validate_sources.py`.
- **FR-004**: The workflow MUST run `python scripts/validate_doc_links.py`.
- **FR-005**: The workflow MUST run `python -m compileall -q src tests scripts`.
- **FR-006**: The workflow MUST run the full existing pytest suite with `PYTHONPATH=src:.`.
- **FR-007**: The workflow MUST run `git diff --check`.
- **FR-008**: The workflow MUST grant only read access to repository contents and MUST NOT configure exchange credentials or perform live trading actions.
- **FR-009**: The workflow MUST fail when any required check fails.

## Success Criteria

- **SC-001**: All configured checks pass on a clean pull request when the repository's code and documentation satisfy the current validators and tests.
- **SC-002**: A failure in any required command produces a failed workflow job.
- **SC-003**: The workflow requires no Wallex or Smart98 secrets and performs no target-service calls.
- **SC-004**: The workflow and its documented commands can be reviewed from the repository without access to private account data.

## Assumptions and Scope

- This feature automates existing checks only; it does not introduce linting, coverage thresholds, deployment, release, strategy, market-data retrieval, Smart98 integration, or trading execution.
- pytest is the only additional test dependency for CI and is pinned to the version validated in the current Python 3.12 environment.
- CI may download the pinned test dependency from the package index; application tests and validators must remain offline with respect to Wallex and Smart98.
