# Feature 007 Security and Data-Flow Review

## Data flow

```
MCP host (client)
        │  stdio: JSON-RPC on stdout
        ▼
wallex_mcp.server (MCPServer)
        │
        ▼
wallex_mcp.config (allowlist lookup)
        │
        ▼
wallex_mcp.wallex_client (HTTP GET to one allowlisted host+path)
        │
        ▼
api.wallex.ir/hector/web/v1/markets
        │
        ▼
wallex_mcp.schemas (Decimal-safe validation)
        │
        ▼
MCP tool result → client
```

Diagnostics (logs, tracebacks) go to stderr only. Protocol messages use stdout only. No network listener is opened.

## Credential boundaries

- Public tool: no API key is sent. The `WALLEX_API_KEY` secret is never referenced by the public path.
- Authenticated path: the secret is read from the GitHub Actions runtime environment, never from a file committed to the repository, never from a command-line argument, and never from an MCP tool parameter. It is injected by the platform into the job environment.
- The secret is never printed, echoed, serialized, committed, uploaded, or included in exception messages, return payloads, audit reports, or workflow artifacts.
- The secret is never sent to a public endpoint, an arbitrary MCP endpoint, or a third-party host.

## Allowed and disallowed operations

| Operation | Status |
|---|---|
| GET to allowlisted endpoint | Allowed |
| GET to non-allowlisted host or path | Rejected before any request |
| User-supplied URL | Rejected |
| User-supplied request headers | Rejected |
| User-supplied HTTP method | Rejected |
| POST/PUT/PATCH/DELETE | Rejected (allowlist is GET-only) |
| Order placement, cancellation, amendment | Not implemented |
| Transfer, deposit, withdrawal, wallet action | Not implemented |
| Margin, leverage, OTC execution | Not implemented |
| WebSocket | Not implemented |

## Error and log hygiene

- Errors are sanitized before logging: no secrets, no authorization headers, no cookies, no account identifiers, no balances.
- A dedicated redaction helper strips sensitive patterns from log records and exception text.
- Timeouts, retries, and size limits are configured conservatively; repeated failures fail closed.

## Test isolation

- Offline unit tests and CI perform no network traffic to Wallex. This is enforced by a test that patches the network and asserts no call is made.
- Integration smoke tests are opt-in and never a pull-request check.
- Authenticated tests are disabled by default and run only from the trusted default branch in a protected environment.

## Residual risk

- The public endpoint's auth requirement is disputed between official prose (no key) and a generated page annotation (`x-api-key`). The public tool sends no key; the gated authenticated path resolves this empirically only with owner approval.
- Rate limits are not documented numerically. The client applies conservative bounded retries and fails closed.
- This review does not establish legal or compliance approval for any real exchange use.