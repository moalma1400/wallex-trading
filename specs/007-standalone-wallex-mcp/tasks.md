# Feature 007 Tasks: Standalone Wallex MCP Server

## Phase 1 — Governance and specification
- [ ] 1.1 Amend constitution to v1.3.0 with standalone MCP clause.
- [ ] 1.2 Update AGENTS.md Feature 007 section.
- [ ] 1.3 Update README.md feature list.
- [ ] 1.4 Create `specs/007-standalone-wallex-mcp/spec.md`.
- [ ] 1.5 Create `specs/007-standalone-wallex-mcp/plan.md`.
- [ ] 1.6 Create `specs/007-standalone-wallex-mcp/tasks.md`.
- [ ] 1.7 Create `specs/007-standalone-wallex-mcp/research.md`.
- [ ] 1.8 Create `specs/007-standalone-wallex-mcp/quickstart.md`.
- [ ] 1.9 Create `specs/007-standalone-wallex-mcp/security-data-flow.md`.

## Phase 2 — Dependencies
- [ ] 2.1 Verify official MCP Python SDK version (mcp==2.3.0, PyPI).
- [ ] 2.2 Verify Python version compatibility (>=3.10; CI uses 3.12).
- [ ] 2.3 Add `pyproject.toml` with pinned dependencies.
- [ ] 2.4 Update `.github/workflows/ci.yml` to install from `pyproject.toml`.

## Phase 3 — Implementation
- [ ] 3.1 Create `src/wallex_mcp/__init__.py`.
- [ ] 3.2 Create `src/wallex_mcp/schemas.py` with Decimal-safe models.
- [ ] 3.3 Create `src/wallex_mcp/config.py` with endpoint allowlist.
- [ ] 3.4 Create `src/wallex_mcp/wallex_client.py` with allowlisted HTTP access.
- [ ] 3.5 Create `src/wallex_mcp/redaction.py`.
- [ ] 3.6 Create `src/wallex_mcp/server.py` with MCP tool registration.
- [ ] 3.7 Add `DataSource.MCP_STANDALONE` to `src/mcp_adapter/__init__.py`.

## Phase 4 — Tests
- [ ] 4.1 Create `tests/fixtures/market_response.json`.
- [ ] 4.2 Create `tests/test_schemas.py`.
- [ ] 4.3 Create `tests/test_client.py` (mocked HTTP).
- [ ] 4.4 Create `tests/test_security.py`.
- [ ] 4.5 Create `tests/test_server_protocol.py` (MCP client smoke test).
- [ ] 4.6 Run full offline test suite; confirm no network traffic.

## Phase 5 — GitHub Actions
- [ ] 5.1 Create `.github/workflows/wallex-mcp.yml`.
- [ ] 5.2 Add `wallex-readonly` protected environment documentation.
- [ ] 5.3 Confirm offline CI workflow remains credential-free.

## Phase 6 — Documentation
- [ ] 6.1 Create `docs/mcp/README.md` operator guide.
- [ ] 6.2 Create `docs/mcp/security-data-flow.md`.
- [ ] 6.3 Update `docs/research/source-register.yaml` with endpoint evidence.
- [ ] 6.4 Update `specs/ROADMAP.md`.
- [ ] 6.5 Add changelog entry.

## Phase 7 — Validation and delivery
- [ ] 7.1 Run `python scripts/validate_sources.py`.
- [ ] 7.2 Run `python scripts/validate_doc_links.py`.
- [ ] 7.3 Run `python -m compileall -q src tests scripts`.
- [ ] 7.4 Run `python -m pytest -v`.
- [ ] 7.5 Run `git diff --check`.
- [ ] 7.6 Secret-leakage review of full diff.
- [ ] 7.7 Commit and push to `feat/standalone-wallex-mcp`.
- [ ] 7.8 Open reviewable PR.