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

Feature 001 remains the official-source inventory and knowledge base. Feature 002 is the offline, strategy-neutral data-validation/replay kernel; Feature 003 is local-only historical-data import/audit/export; Feature 004 is the user-brief-based offline challenge policy and fail-closed controls. Feature 005 is approved only for a narrowly scoped public, read-only **Spot market-data** adapter through a verified Smart98-mediated contract, plus offline tests and documentation, after its evidence/security/architecture gates pass. T003 remains blocked: the user-supplied report text records tool-specific observations, but authoritative source/version, Smart98 auth/permissions, rate limits, timeouts, pagination/streaming, and order-lifecycle contracts remain unresolved. The repository's existing `src/mcp_adapter/` parser/provider code and synthetic tests do not satisfy those gates. No live adapter is enabled by this approval.

Do not make direct Wallex requests or add a direct-access fallback; do not install/configure MCP servers or request/create credentials. Do not read private accounts or implement order placement/cancellation, transfers, deposits, withdrawals, wallet operations, Margin, leverage, borrowing, shorting, derivatives, OTC execution, or other state-changing actions. Keep tests, CI, backtests, shadow and dry-run offline with respect to Wallex and Smart98. Keep all costs and risk parameters explicit inputs; do not select them for users. Record source conflicts instead of harmonizing contracts by guesswork. Any future real-exchange use needs verified challenge rules/account permissions, deterministic risk/reconciliation controls, explicit owner activation, and a current jurisdiction-specific legal/compliance review; no legality or authorization guarantee is possible.
