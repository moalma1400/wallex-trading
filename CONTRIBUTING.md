# Contributing

## Required workflow

1. Review the constitution, current feature specification, plan, and tasks before changes.
2. For new work, follow the official Spec Kit workflow and canonical project templates under `.specify/`; use the generated skill instructions under `.agents/skills/`. Keep the specification ahead of implementation.
3. Research public official Wallex sources through their documented navigation. Do not bypass access controls, authenticate, use API credentials, or call live production API endpoints.
4. Add sources to `docs/research/source-register.yaml` with exact URL, retrieval time in UTC, discovery path, status, evidence notes, and known relationships. Never fabricate a publication date or mark an unopened page reviewed.
5. Update `coverage-matrix.md`, `discrepancies.md`, `unresolved-questions.md`, and relevant Persian knowledge pages alongside register changes.
6. Cite every material statement with its source ID and exact URL. Identify official documentation statements separately from inference, assumptions, historical examples, and unknowns. Report conflicts, not silent reconciliations.
7. Run `python3 scripts/validate_sources.py` and `git diff --check`; review references, changed files, and the final diff for unsupported claims or secrets.
8. Submit a reviewable pull request tracing changes to specification, plan, tasks, and validation evidence. Do not merge on behalf of the owner.

## Documentation style

User-facing trading knowledge is Persian-first. Keep API names and original identifiers unchanged. Summaries should be concise and original rather than reproducing entire pages. Clearly date time-sensitive values such as fees, precision, minimums, and rate limits. If a source is unavailable, record the attempted URL, date, actual failure, and what remains unverified.

## Current phase boundaries

Feature 001 remains the official-source inventory and knowledge base. Feature 002 permits only offline, strategy-neutral data validation, deterministic replay, backtest calculations, risk gates, and a paper ledger using synthetic or user-supplied local files. Do not implement a strategy, fetch public Wallex data, call a production endpoint, connect to Wallex or Smart98, create/use a key, access an account, or simulate an exchange connection. No order, transfer, withdrawal, or account-setting changes are permitted. Keep all costs and risk parameters explicit inputs; do not select them for users. Record source conflicts instead of harmonizing contracts by guesswork. Any future real-exchange proposal needs separate review and a current jurisdiction-specific compliance gate; no legality guarantee is possible.
