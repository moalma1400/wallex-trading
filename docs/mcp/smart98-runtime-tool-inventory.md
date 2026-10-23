# Smart98 runtime MCP inventory — 2026-10-23

## Scope and evidence level

This document records two distinct kinds of evidence supplied on 2026-10-23:
(1) loaded Smart98 runtime tool definitions and (2) one live, public,
read-only diagnostic invocation of `wallex_basic_get_markets`. No order tool was
invoked. No authenticated account read, order placement, cancellation,
modification, credential access, Smart98 configuration change, or activation
occurred.

| Connector | Discovered tools | Evidence | Limitation |
|---|---:|---|---|
| `wallex-mcp` | 52 | Runtime definitions inspected; one public market tool invoked | Does not verify account access or order-tool behavior |
| `mcp-git-moalma` | 46 | Listed in runtime inventory | Not part of order execution |
| `coingecko-traider-mcp` | 2 | Listed in runtime inventory | Separate from the repository's CoinGecko server |

The Smart98 connector `wallex-mcp` is distinct from the repository-owned
`wallex-standalone-mcp`. The repository tools `wallex_get_markets`,
`wallex_get_balances`, and `wallex_get_open_orders` were not present in the
reported Smart98 runtime inventory.

## Supported invocation boundary

**Confirmed:** the demonstrated invocation surface is the Smart98 agent runtime's
connected-MCP tool-call mechanism. A public tool was successfully called inside
that runtime.

**Not evidenced:** no external Smart98 HTTP invocation endpoint, SDK, gateway,
or callable client for repository Python was documented or discovered. This is
not proof that no such interface exists; its availability is unknown. Do not
invent or assume an endpoint.

Therefore `MediatedExecutionClient`'s injected Python callable is a test/design
seam, not a Smart98 bridge. Repository Python cannot be said to reach the
connected tool unless a supported, documented bridge is separately established.
The architecture supported by current evidence is Smart98-side orchestration,
but the mechanism for running this repository's deterministic policy code from
that orchestration is still unresolved. Owner-managed MCP registration remains
the rule; this PR did not install or register any MCP.

## Public-market diagnostic result

Only `wallex_basic_get_markets` was invoked. The returned runtime-visible
payload was presented as a direct JSON object under a `result` key, with
market data under `result.markets[]`. A sanitized visible sample included
`USDTTMN`, `USDT`, `TMN`, price and market metadata. The actual payload was
large and truncated in the report.

This establishes that this public market tool could be invoked in that session.
It does **not** establish the wire-level MCP response format: no raw MCP
`content` or `structuredContent` array was exposed. It does not establish the
response envelope for either order tool. A prior report of a top-level
`success: true` for this same market tool is historical evidence, not proof
of the order tools' response contract.

| Observation | Status |
|---|---|
| Public market call returned data in the agent runtime | CONFIRMED for this session |
| Visible data path | `result.markets[]` in the runtime-presented object |
| Raw MCP `content` / `structuredContent` details | UNKNOWN / not exposed |
| Order-tool success envelope | UNKNOWN |
| Error representation and timeout semantics | UNKNOWN |
| Request/correlation ID | None exposed in the reported market payload |
| Whether order POST is idempotent or lookup is guaranteed after timeout | UNKNOWN |

## Reported order tool inputs

The following input definitions were read from loaded Smart98 runtime tool
definitions. Neither order tool was invoked.

| Tool | Required inputs | Optional inputs | Runtime output schema |
|---|---|---|---|
| `wallex_spot_post_account_orders` | `side: string`, `symbol: string`, `type: string` | `client_id: string`, `price: string`, `quantity: string`, `stop_Price: string` | `null` / not exposed |
| `wallex_spot_get_orders_client` | `client_id: string` | None reported | `null` / not exposed |

The create-order input schema declares no enums for `side` or `type`. Values
on sibling tools are not guarantees for the create tool. Apply only a separately
verified allowlist based on official current order rules; do not infer schema
constraints from sibling tools.

Official Wallex API documentation was reported to describe an HTTP create
response and an order identifier for later lookup. This is documentation-only
evidence and does not establish the Smart98 connector's returned tool result,
uniqueness enforcement, or a guaranteed lookup after a timed-out POST. Supplying
`client_id` is useful for reconciliation but is not, by itself, a reliability
guarantee. Never retry or submit a replacement after an ambiguous create call
until a separately verified reconciliation procedure establishes the outcome.

Other read-only tools were discovered for markets, balances, fees, order book /
depth, candles, latest trades, open orders, order history, and client-ID order
detail. Discovery does not prove that those tools were invoked successfully or
that account access is available.

## Contract verifier

`wallex_mcp.smart98_contract.verify_smart98_execution_contract` accepts a
sanitized `tools/list` snapshot and requires both expected order tools, input
schemas matching the fields used by the adapter, and output schemas explicitly
documenting the `success: boolean` / `result: object` envelope currently
assumed by `MediatedExecutionClient`. It fingerprints these schemas and performs
no network I/O or tool invocation.

The test schemas are synthetic fixtures, not proof of the live contract. A
regression test models the reported inputs with absent output schemas and
asserts that verification fails closed. The supplied runtime report therefore
does not verify the adapter contract and must not produce a verified execution
contract. T007 remains open.

Do not relax the verifier simply because a public market tool returned data.
That tool's result is not evidence for either order tool's result schema. If the
order tools have no declared `outputSchema`, the next evidence step must be a
separately authorized, non-order-changing way to observe their real call-result
shape (or an approved fixture from a pre-existing authorized observation). Only
then can a reviewed normalizer be designed. Do not guess `{success, result}`
based on the Wallex HTTP API's documented JSON response.

## Required before any live activation

Before any activation decision, separately verify the official contest rules and
window, account permissions, eligible Spot markets, fees, quantity/price
precision and minimums, compliance eligibility, and the explicit activation
record. Execution is still disabled. There is no evidenced invocation bridge
from repository Python to Smart98's connected MCP tools. The open architecture
decision is how deterministic policy should be enforced in the Smart98 runtime
or through a separately owner-configured and verified MCP service; neither
mechanism should be invented or treated as implemented.
