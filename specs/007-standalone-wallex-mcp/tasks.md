# Feature 007 Tasks: Standalone Wallex MCP Server

## Phase 1 — Governance and specification
- [x] 1.1 Constitution amended to v1.3.0 with standalone MCP clause.
- [x] 1.2 AGENTS.md updated with Feature 007 boundaries.
- [x] 1.3 README.md updated with Feature 007 references.
- [x] 1.4 Create `specs/007-standalone-wallex-mcp/spec.md`.
- [x] 1.5 Create `specs/007-standalone-wallex-mcp/plan.md`.
- [x] 1.6 Create this task checklist.
- [x] 1.7 Create `specs/007-standalone-wallex-mcp/research.md`.
- [x] 1.8 Create `specs/007-standalone-wallex-mcp/quickstart.md`.
- [x] 1.9 Create `specs/007-standalone-wallex-mcp/security-data-flow.md`.

## Phase 2 — Dependencies and CI installation
- [x] 2.1 Pin MCP Python SDK to `mcp==2.3.0`.
- [x] 2.2 Declare Python compatibility (`>=3.10`; CI uses 3.12).
- [x] 2.3 Declare package dependencies and `wallex-mcp-server` entry point in `pyproject.toml`.
- [x] 2.4 Update `.github/workflows/ci.yml` to install `-e ".[test]"`.

## Phase 3 — Implementation
- [x] 3.1 Create `src/wallex_mcp/__init__.py`.
- [x] 3.2 Create Decimal-safe response models.
- [x] 3.3 Create immutable endpoint allowlist.
- [x] 3.4 Create allowlisted HTTP client with timeout/retry/size bounds.
- [x] 3.5 Create secret-redaction helpers.
- [x] 3.6 Register the `wallex_get_markets` MCP tool.
- [x] 3.7 Add `DataSource.MCP_STANDALONE` to `src/mcp_adapter/__init__.py`.
- [x] 3.8 Reject unsuccessful market response envelopes.
- [x] 3.9 Redact transient transport exception text before logging.

## Phase 4 — Offline tests
- [x] 4.1 Add the standalone markets response fixture.
- [x] 4.2 Add schema and Decimal validation tests in `tests/test_wallex_mcp.py`.
- [x] 4.3 Add fake-transport client tests for errors, retries, limits and allowlisting.
- [x] 4.4 Add credential redaction and no-key-on-public-call tests.
- [x] 4.5 Add MCP SDK server registration and stdio client discovery smoke tests.
- [ ] 4.6 Run the full offline suite and confirm CI passes; tests must not call Wallex.

## Phase 5 — GitHub Actions
- [x] 5.1 Add `.github/workflows/wallex-mcp.yml` (manual dispatch; validation job guarded to `main`).
- [x] 5.2 Document that no API key or account credential is needed for Feature 007 tests.
- [x] 5.3 Keep CI credential-free and offline with respect to Wallex.
- [ ] 5.4 Verify the new workflow and regular CI through GitHub Actions results.

## Phase 6 — Documentation and evidence
- [x] 6.1 Add `docs/mcp/README.md` operator guide.
- [x] 6.2 Add `docs/mcp/security-data-flow.md`.
- [x] 6.3 Confirm the `MARKETS` official documentation source is registered in `docs/research/source-register.yaml`.
- [x] 6.4 Add Feature 007 to `specs/ROADMAP.md`.
- [ ] 6.5 Add a changelog entry if/when a repository changelog convention is adopted.

## Phase 7 — Validation and delivery
- [ ] 7.1 Run `python scripts/validate_sources.py`.
- [ ] 7.2 Run `python scripts/validate_doc_links.py`.
- [ ] 7.3 Run `python -m compileall -q src tests scripts`.
- [ ] 7.4 Run `python -m pytest -v`.
- [ ] 7.5 Run `git diff --check`.
- [ ] 7.6 Review full diff for secret leakage, network calls, unsupported endpoints, and governance contradictions.
- [ ] 7.7 Commit and push validated changes to `feat/standalone-wallex-mcp`.
- [ ] 7.8 Open a reviewable PR against `main`; do not merge automatically.
