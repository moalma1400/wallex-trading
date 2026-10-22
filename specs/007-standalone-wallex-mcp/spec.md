# Feature 007 Specification: Standalone Wallex MCP Server

**Feature**: 007-standalone-wallex-mcp
**Status**: Approved for implementation
**Date**: 2026-10-22
**Constitution**: v1.3.0

## Context

Feature 005 authorized a Smart98-mediated adapter for verified public, read-only Wallex Spot market data. That path requires Smart98 to be running and acting as the mandatory intermediary. The owner has now directed a second, independent path: a repository-owned standalone Model Context Protocol (MCP) server that GitHub Actions can launch and test directly, without Smart98.

This feature does not replace Smart98. Smart98 remains an optional MCP host/client. The standalone server is an alternative mediation path for the same narrowly scoped capability: verified public, read-only Spot market data.

## User Story

As a maintainer, I want GitHub Actions to be able to launch a repository-owned Wallex MCP server over stdio, connect an official MCP client, discover its tools, and invoke them against verified public endpoints — so that MCP integration is testable in CI without any external platform running.

## Scope

### Included
- A standalone MCP server owned by this repository, transport `stdio`.
- One verified public tool: `wallex_get_markets`, backed by `GET https://api.wallex.ir/hector/web/v1/markets`.
- Official MCP Python SDK, pinned version, declared dependency.
- A genuine MCP client smoke test that launches the server as a subprocess and invokes the tool over the MCP protocol.
- Mocked-HTTP unit tests for parsing, validation, timeouts, retries, size limits, and arbitrary-URL rejection.
- A manual `workflow_dispatch` GitHub Actions workflow with an opt-in public network smoke step and a gated authenticated read-only path behind a protected environment.
- Documentation: operator guide, security/data-flow review, endpoint evidence register.

### Excluded
- Any state-changing operation: order placement, cancellation, amendment, transfer, deposit, withdrawal, wallet action, margin, leverage, OTC execution.
- Arbitrary HTTP, user-supplied URLs, arbitrary headers, arbitrary methods, hidden credential forwarding.
- WebSocket streaming.
- Any capability whose official contract is unverified (recorded as `NOT IMPLEMENTED — official contract not verified`).
- Authenticated requests outside the gated, manually triggered, protected-environment path.

## Requirements

### Functional

- **FR-001**: The server MUST speak MCP over stdio, using stdout for protocol messages and stderr for diagnostics.
- **FR-002**: The server MUST register at least one tool, `wallex_get_markets`, with a validated input schema and a normalized output.
- **FR-003**: The server MUST access only explicitly allowlisted Wallex endpoints; the initial allowlist contains exactly one endpoint.
- **FR-004**: The server MUST use Decimal for all financially relevant values.
- **FR-005**: The server MUST enforce connection/read timeouts, response-size limits, and bounded retries on safe GET requests.
- **FR-006**: The server MUST reject invalid symbols, unsupported parameters, malformed JSON, and invalid response structures, failing closed.
- **FR-007**: The server MUST distinguish source timestamps from retrieval timestamps and preserve UTC.
- **FR-008**: The server MUST never log API keys, authentication headers, cookies, or sensitive account data.
- **FR-009**: Public tools MUST work with no API key unless official documentation explicitly requires one.
- **FR-010**: The server MUST NOT send WALLEX_API_KEY to public endpoints by default.

### Non-functional

- **NFR-001**: Offline unit tests and CI MUST perform no network traffic to Wallex.
- **NFR-002**: All automated tests MUST be deterministic and use sanitized fixtures.
- **NFR-003**: No secret value may appear in test output, fixtures, reports, or artifacts.
- **NFR-004**: The MCP SDK version MUST be pinned and verified against the official repository.
- **NFR-005**: Existing Smart98-adapter tests and behavior MUST remain compatible.

## Acceptance Criteria

1. The MCP server starts over stdio and completes MCP initialization with an official client.
2. The client discovers `wallex_get_markets` and invokes it through the MCP protocol, not a direct Python call.
3. A valid market-list response is normalized into a deterministic, Decimal-safe structure.
4. Unsuccessful Wallex responses, unexpected schemas, and invalid numeric values fail closed.
5. Timeouts, retries, and size limits behave as configured and are testable with a mocked transport.
6. Arbitrary URLs and unsupported endpoints are rejected before any request is attempted.
7. Public tools work without a key; gated authenticated tests fail closed when unconfigured.
8. Credentials are redacted from errors and logs (verified with synthetic secrets only).
9. The offline unit/CI suite cannot reach Wallex or submit trading actions.
10. Existing Smart98-adapter tests still pass.
11. `git diff --check` passes and no secrets are committed.

## Official Endpoint Evidence

- **Implemented**: `GET https://api.wallex.ir/hector/web/v1/markets` — verified against source `MARKETS` (`https://developers.wallex.ir/docs/basic-services-markets`, reviewed 2026-10-22) and `MOD-GENERATED-GET-MARKETS`.
- **Not implemented — official contract not verified**: market depth/order book, candle/OHLCV history, recent public trades, ticker observations. Official prose and generated pages exist but disagree on hosts, requiredness, and auth annotations; per constitution III and the evidence-first rule, these are not implemented until a single consistent verified contract exists.

## Governance

Constitution v1.3.0, AGENTS.md, and README.md are amended by this feature. Smart98 is an optional MCP host/client, not a mandatory dependency of the standalone runtime. The standalone server may access only officially documented Wallex endpoints approved for this feature. No order or state-changing capability is implemented. Offline CI, paper replay, and backtesting remain incapable of authenticated requests or real trading actions. Unverified endpoints, undocumented permissions, and ambiguous behaviors fail closed.