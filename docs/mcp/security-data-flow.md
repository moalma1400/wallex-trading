# Standalone MCP security and data flow

## Request flow

1. An MCP host launches `wallex-mcp-server` as a local subprocess.
2. MCP JSON-RPC messages are exchanged over stdin/stdout using stdio.
3. The sole registered tool, `wallex_get_markets`, invokes the repository-owned
   `WallexClient`.
4. The client checks the method, exact host, and path against the immutable
   endpoint allowlist before creating an HTTP request.
5. The public endpoint is called without an API key; the response is bounded
   by a maximum byte size, decoded as JSON, and validated by strict Pydantic
   models. An unsuccessful response envelope is rejected.
6. Only normalized market metadata is returned to the MCP caller. Diagnostic
   logging is sent to stderr, with error text passed through redaction.

## Trust boundaries

- **MCP caller:** supplies tool invocation requests, not arbitrary URLs,
  methods, headers, or endpoint paths.
- **Standalone server:** registers one read-only tool. No order-management or
  account-mutation tools are registered.
- **Wallex public endpoint:** external data is untrusted until size, JSON,
  envelope, and schema validation succeeds.
- **CI:** installs dependencies, then runs mocked HTTP tests and a protocol
  discovery smoke test. It has no Wallex credentials and does not invoke the
  market tool against a real endpoint.

## Explicit exclusions

Feature 007 does not provide order placement or cancellation, asset transfers,
deposits, withdrawals, authenticated account access, private WebSocket streams,
or any strategy/execution behavior. It does not make a network call merely to
discover MCP tools. Tests use synthetic fixtures and an injected fake HTTP
transport; no live exchange requests are authorized by this design.

## Extension gate

Before adding another endpoint, record the official documentation URL and
retrieval time in `docs/research/source-register.yaml`, verify the exact
request and response contract, review data sensitivity and permissions, add a
narrow allowlist entry, add offline success/failure/security tests, and update
the Feature 007 specification, roadmap, and operator documentation. Do not
add a route based solely on inferred URL patterns or undocumented examples.
