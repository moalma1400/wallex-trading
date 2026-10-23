# Standalone MCP security and data flow

## Request flow

1. An MCP host launches the installed `wallex-mcp` entry point (or
   `python -m wallex_mcp.server`) as a local subprocess.
2. MCP JSON-RPC messages use stdin/stdout over the stdio transport. Diagnostics
   are directed to stderr so they do not corrupt the protocol stream.
3. By default, the server registers only `wallex_get_markets`. It calls the
   public `GET https://api.wallex.ir/hector/web/v1/markets` endpoint without
   an API key.
4. Account-read tools are registered only when the operator sets both
   `WALLEX_API_KEY` and `WALLEX_ENABLE_ACCOUNT_READONLY=1`. In that mode,
   `wallex_get_balances` and `wallex_get_open_orders` are added for the
   exact allowlisted GET paths `/v1/account/balances` and
   `/v1/account/openOrders`.
5. Before every request, the client checks the HTTP method, exact host, and
   path against the allowlist. It sends `x-api-key` only for an allowlisted
   entry marked as requiring a key. It rejects non-2xx responses, oversized
   response bodies, invalid JSON, and invalid response envelopes/shapes.
6. Error messages sent to logs pass through the redaction helper. API keys
   must be supplied by the MCP host's environment/secret manager, never by a
   tool argument, source file, chat message, or CI variable.

## Trust boundaries

- **MCP caller:** can invoke registered tools; it does not supply arbitrary
  URLs, methods, headers, or endpoint paths.
- **Standalone server:** exposes public market metadata by default. In the
  explicitly enabled account-read mode, it additionally exposes only the two
  allowlisted account GET tools. It does not expose trading or account-mutation
  actions.
- **Wallex API:** responses are untrusted until HTTP status, size, JSON, and
  endpoint-specific response validation have succeeded. Response fields from
  the exchange are data, not instructions.
- **Credential provider:** the MCP host/operator is responsible for securely
  storing and injecting `WALLEX_API_KEY`. Use the least-privileged key
  supported by Wallex and do not enable account reads in shared or untrusted
  MCP environments.
- **CI and tests:** use synthetic credentials and injected fake HTTP
  transports. Offline tests must not require a real API key or make live
  exchange requests.

## Explicit exclusions

This feature does not provide order placement, order cancellation, deposits,
withdrawals, transfers, private WebSocket streams, or trading-strategy and
execution behavior. The account tools are read-only and limited to balances
and active orders. Tool discovery itself does not invoke Wallex endpoints.
A successful offline test does not establish that a real API key is valid or
that the live exchange response matches the tested fixtures.

## Extension gate

Before adding another endpoint, record its official documentation URL and
retrieval time in `docs/research/source-register.yaml`, verify the request and
response contract, review data sensitivity and required permissions, add a
narrow allowlist entry, and add offline success/failure/security tests. Update
the Feature 007 specification, roadmap, operator guide, and this data-flow
document. Do not add a route based solely on inferred URL patterns or
undocumented examples.
