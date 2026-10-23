# Feature 007 Plan: Standalone Wallex MCP Server

**Feature**: 007-standalone-wallex-mcp
**Constitution**: v1.3.0

## Architecture

```
GitHub Actions runner
        │
        ▼  stdio subprocess (python -m wallex_mcp.server)
  src/wallex_mcp/server.py          — MCP server entry, tool registration
        │
        ▼
  src/wallex_mcp/config.py          — endpoint allowlist, timeouts, size limits
        │
        ▼
  src/wallex_mcp/wallex_client.py   — HTTP access only to allowlisted endpoints
        │
        ▼
  src/wallex_mcp/schemas.py         — validated input/output models (Decimal-safe)
        │
        ▼
  api.wallex.ir/hector/web/v1/markets   (only allowlisted endpoint)
```

Diagnostics go to stderr. Protocol messages go to stdout only. No network listener is opened.

## Components

| File | Responsibility |
|---|---|
| `src/wallex_mcp/__init__.py` | Package marker and public surface. |
| `src/wallex_mcp/server.py` | `MCPServer` construction, `wallex_get_markets` tool registration, stdio run entry. |
| `src/wallex_mcp/config.py` | Endpoint allowlist, timeout/size/retry constants, credential gating. |
| `src/wallex_mcp/wallex_client.py` | HTTP client restricted to allowlisted endpoints; no arbitrary URLs. |
| `src/wallex_mcp/schemas.py` | Pydantic models for market metadata; Decimal coercion. |
| `src/wallex_mcp/redaction.py` | Secret-aware logging helpers. |
| `tests/test_server_protocol.py` | MCP client smoke test over stdio. |
| `tests/test_client.py` | Mocked-HTTP client tests. |
| `tests/test_schemas.py` | Schema validation tests. |
| `tests/test_security.py` | Redaction, arbitrary-URL rejection, offline isolation. |
| `tests/fixtures/market_response.json` | Sanitized fixture. |
| `.github/workflows/wallex-mcp.yml` | Manual MCP integration workflow. |
| `docs/mcp/README.md` | Operator guide. |
| `docs/mcp/security-data-flow.md` | Security and data-flow review. |

## Dependency management

The repository currently has no `pyproject.toml` or `requirements.txt`. CI installs dependencies inline. This feature adds `pyproject.toml` with pinned `mcp==2.3.0` and `pydantic>=2.12,<3`, and updates CI to install from it. The `mcp` SDK is verified against PyPI as the official `modelcontextprotocol/python-sdk` package, MIT-licensed, requires Python >=3.10 (compatible with CI's 3.12).

## Migration and compatibility

- The existing `src/mcp_adapter/` Smart98 adapter is untouched. Its tests must continue to pass.
- A new `DataSource.MCP_STANDALONE` value is added to `src/mcp_adapter/__init__.py` so standalone data is not mislabelled as Smart98 data. No existing behavior changes.
- No allowlist, eligibility policy, or trading risk rule is duplicated.

## Rollout order

1. Governance amendment (constitution, AGENTS.md, README).
2. Feature 007 spec/plan/tasks/research/quickstart/security.
3. Dependency declaration (`pyproject.toml`).
4. `src/wallex_mcp/` implementation.
5. Offline test suite.
6. MCP client protocol smoke test.
7. GitHub Actions workflow.
8. Documentation.
9. Source register, roadmap, changelog.
10. Validators, compile, tests, `git diff --check`, review, commit, push, PR.