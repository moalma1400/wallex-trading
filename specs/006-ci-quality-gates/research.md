# Research: Offline CI Quality Gates

**Date**: 2026-10-22

## Context inspected

- `AGENTS.md`: requires the constitution, canonical Spec Kit artifacts, offline tests, validators, and `git diff --check`.
- `CONTRIBUTING.md`: prohibits live Wallex requests, keys, account access, and order actions; requires reviewable changes and says not to merge on behalf of the owner.
- `.specify/memory/constitution.md`: requires deterministic, network-free tests and prohibits committing credentials or private account data.
- Existing workflow/dependency-file search returned no workflow or Python dependency manifest at the searched depth.
- A local Python 3.12 run completed successfully before implementation: 135 source records validated; 179 local Markdown links resolved and 248 citations matched; `compileall` passed; pytest reported 145 passed and 24 subtests passed. These are baseline results, not evidence that GitHub Actions has run.

## Decisions

1. Use Python 3.12 because the current test suite uses `enum.StrEnum`, unavailable in Python 3.10, and the existing baseline was verified on Python 3.12.
2. Pin pytest to `9.1.1`, matching the validated local environment, and avoid adding a runtime dependency manifest for this CI-only requirement.
3. Execute the existing validators and test suite as separate visible steps so failures are easy to diagnose.
4. Use `permissions: contents: read`; do not request write permissions, secrets, services, deployments, or external target access.
5. Trigger on pull requests targeting `main`, pushes to `main`, and pushes to `arena/post-merge-ci` so the implementation branch can be checked.

## Limitations

- This repository environment has no verified native Spec Kit integration; these artifacts were authored by manually applying the generated repository skill instructions, not by invoking a native Spec Kit command.
- GitHub Actions behavior and workflow syntax still require confirmation from an actual run after the workflow is pushed.
- Installing pytest requires package-index access on the runner. The project's validators and tests themselves must remain offline with respect to Wallex and Smart98.
