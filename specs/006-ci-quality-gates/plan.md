# Implementation Plan: Offline CI Quality Gates

**Branch**: `arena/post-merge-ci` | **Date**: 2026-10-22 | **Spec**: [spec.md](spec.md)

## Summary

Add one GitHub Actions workflow that runs the repository's established offline validators, Python compilation, full pytest suite, and whitespace/error check on pull requests to `main` and pushes to `main`. No application behavior changes are in scope.

## Technical Context

- **Language/Version**: Python 3.12
- **Primary Dependencies**: pytest 9.1.1 for the existing test suite; no new application dependency
- **Storage**: N/A
- **Testing**: Existing source validator, documentation-link validator, compileall, pytest, git diff check
- **Target Platform**: GitHub-hosted Linux runner
- **Project Type**: Python repository with documentation and scripts
- **Constraints**: Tests and validators must not call Wallex or Smart98; no secrets, live trading, or write permissions
- **Scale/Scope**: One workflow and feature documentation only

## Constitution Check

- **Specification before implementation**: PASS — scope and acceptance criteria are recorded in spec.md.
- **Evidence and traceability**: PASS — this workflow validates repository artifacts and does not make new factual claims about Wallex.
- **Credential protection**: PASS — no secrets are required or referenced.
- **Offline and trading boundaries**: PASS — no target API calls, Smart98 integration, or order execution is added.
- **Least privilege**: PASS — workflow permissions are limited to `contents: read`.

## Design

Use a single job on `ubuntu-latest` with a bounded timeout. Trigger on pull requests targeting `main` and pushes to `main` or the implementation branch. Set up Python 3.12, install the pinned pytest version, then run the checks in deterministic sequence. Do not use services, deployment actions, repository write permissions, or secrets.

## Project Structure

```text
.github/workflows/ci.yml
specs/006-ci-quality-gates/
├── spec.md
├── plan.md
├── research.md
└── tasks.md
```

## Validation

Run all workflow commands locally under Python 3.12, then run `git diff --check`. A successful local run validates the commands but does not substitute for observing a completed GitHub Actions run after the branch is pushed.
