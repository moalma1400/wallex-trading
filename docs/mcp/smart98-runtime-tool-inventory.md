# Smart98 runtime MCP inventory — 2026-10-23

## Scope and evidence level

This document records the sanitized runtime schema report provided on 2026-10-23.
The audit session had connector schemas loaded and deliberately did not invoke
any live Wallex tool. Tool discovery and the reported input schemas are evidence
for that session only; connector health, account permissions, order behavior,
timeouts, and idempotency guarantees remain unverified.

| Connector | Discovered tools | Evidence | Limitation |
|---|---:|---|---|
| `wallex-mcp` | 52 | Schemas loaded in the audit session | No live Wallex invocation in this audit; account permissions unknown |
| `mcp-git-moalma` | 46 | Read-only identity check reported successful | Not part of order execution |
| `coingecko-traider-mcp` | 2 | Read-only price query reported successful | Separate from the repository's CoinGecko server |

The Smart98 connector `wallex-mcp` is distinct from the repository-owned
`wallex-standalone-mcp`. The repository tools `wallex_get_markets`,
`wallex_get_balances`, and `wallex_get_open_orders` were not present in the
reported Smart98 runtime inventory.

## Reported order tool inputs

The following details are from the supplied sanitized runtime report; no tool
was invoked during its collection.

| Tool | Required inputs | Optional inputs | Runtime output schema |
|---|---|---|---|
| `wallex_spot_post_account_orders` | `side: string`, `symbol: string`, `type: string` | `client_id: string`, `price: string`, `quantity: string`, `stop_Price: string` | Not exposed |
| `wallex_spot_get_orders_client` | `client_id: string` | None reported | Not exposed |

The create-order input schema does not declare enums for `side` or `type`.
The report found conventional enum values on sibling tools, but those are not
constraints declared by the create tool itself. The adapter must use a
separately verified local allowlist and current official market/order rules;
it must not infer schema guarantees from sibling tools.

### Response, timeout, and idempotency status

- Both runtime output schemas are unavailable in the reported definitions.
- Runtime response envelopes and error formats are unknown.
- Timeout and idempotency behavior are unknown.
- Official documentation was reported to describe a create response envelope
  and a client order identifier for later retrieval. This is documentation-only
  evidence; it does not establish the Smart98 connector's returned MCP result
  format, uniqueness enforcement, or guaranteed lookup after a timed-out POST.
- Supplying an explicit `client_id` is necessary for the intended reconciliation
  pattern, but it is not a proven reliability guarantee. After an ambiguous
  create call, do not retry or submit a replacement until a separately verified
  reconciliation procedure establishes the outcome.

The audit also identified read-only tools for markets, balances, fees, order
book/depth, candles, latest trades, open orders, order history, and client-ID
order detail. Their discovery does not prove successful calls or account access.
The complete sanitized report is retained in the conversation; this file keeps
a compact inventory rather than asserting undocumented response semantics.

## Contract verifier

`wallex_mcp.smart98_contract.verify_smart98_execution_contract` accepts a
sanitized `tools/list` snapshot and checks that both expected tools exist,
their input schemas match the fields currently sent by the adapter, and their
output schemas document the `success: boolean` / `result: object` envelope
currently assumed by `MediatedExecutionClient`. It fingerprints the schemas so
a changed contract cannot silently reuse the same version string. It performs
no network I/O and invokes no tools.

The test schemas are synthetic fixtures. They are **not evidence** that the
real Smart98 tools satisfy this contract. A regression test now models the
reported runtime input schemas with absent output schemas and asserts that
verification fails closed. Therefore the supplied report does not verify the
current adapter contract and does not make the verifier return a verified
contract. T007 remains open.

If Smart98 does not expose `outputSchema`, the next implementation step is to
capture a sanitized actual MCP tool-call result in a separately authorized,
non-order-changing diagnostic process (or a documented mock/fixture from an
existing approved response), establish the real MCP response envelope, and
implement a reviewed normalizer. Do not guess `{success, result}` based on the
Wallex HTTP API's documented JSON response.

## Required before any live activation

Separately verify the official contest rules/window, account permissions,
allowed Spot markets, fees, precision/minimum constraints, compliance eligibility,
and an explicit activation record. The execution adapter has no registered live
MCP tool or invocation bridge in this repository; a callable injected by
Smart98/another runtime is not automatically available to repository Python.
This document does not enable live execution.
