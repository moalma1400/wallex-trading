# Smart98 runtime MCP inventory — 2026-10-23

## Scope and evidence level

This document records the read-only runtime audit reported on 2026-10-23.
The audit session had connector schemas loaded and deliberately did not invoke
any live Wallex tool. Tool discovery is confirmed for that session; Wallex
connector health, account permissions, and successful order behavior remain
unverified.

| Connector | Discovered tools | Evidence | Limitation |
|---|---:|---|---|
| `wallex-mcp` | 52 | Schemas loaded in the audit session | No live Wallex invocation in this audit; account permissions unknown |
| `mcp-git-moalma` | 46 | Read-only identity check reported successful | Not part of order execution |
| `coingecko-traider-mcp` | 2 | Read-only price query reported successful | Separate from the repository's CoinGecko server |

The Smart98 connector `wallex-mcp` is distinct from the repository-owned
`wallex-standalone-mcp`. The repository tools `wallex_get_markets`,
`wallex_get_balances`, and `wallex_get_open_orders` were not present in the
reported Smart98 runtime inventory.

## Relevant discovered tool names

| Tool | Reported inputs | Classification | Verification status |
|---|---|---|---|
| `wallex_spot_post_account_orders` | Required: `side`, `symbol`, `type`; optional: `client_id`, `price`, `quantity`, `stop_Price` | State-changing | Discoverable; not invoked |
| `wallex_spot_get_orders_client` | `client_id` | Read-only order lookup | Discoverable; not invoked |
| `wallex_basic_get_account_balances` | No parameters reported | Read-only | Discoverable; live result unverified |
| `wallex_spot_get_open_order` | `symbol`, `page`, `per_page` | Read-only | Discoverable; live result unverified |
| `wallex_spot_get_orders` | `market`, `side`, `type`, `from`, `to`, `page`, `per_page` | Read-only | Discoverable; live result unverified |
| `wallex_basic_get_markets` / `wallex_spot_get_markets` | No parameters reported | Read-only | Discoverable; live result unverified |
| `wallex_basic_get_market_depth` | `symbol` | Read-only | Discoverable; live result unverified |
| `wallex_basic_candle_history` | `symbol` and range/resolution parameters | Read-only | Discoverable; live result unverified |
| `wallex_basic_get_latest_trades` | `symbol` | Read-only | Discoverable; live result unverified |

The report retained parameter-name summaries, not complete raw JSON Schemas.
It did not preserve every field type, enum, `additionalProperties` rule,
`outputSchema`, response envelope, error contract, or timeout semantic.
These gaps prevent certifying the current adapter against the actual runtime.

## Contract verifier

`wallex_mcp.smart98_contract.verify_smart98_execution_contract` accepts a
sanitized `tools/list` snapshot and checks that both expected tools exist,
their input schemas match the fields currently sent by the adapter, and their
output schemas document the required `success: boolean` / `result: object`
envelope. It fingerprints the schemas so a changed contract cannot silently
reuse the same version string. It performs no network I/O and invokes no tools.

The test schemas are synthetic fixtures. They are **not evidence** that the
real Smart98 tools satisfy this contract. T007 remains open until actual
runtime schemas are captured and checked.

## Required next evidence

Capture the actual sanitized JSON Schema for both tools from Smart98, including
`inputSchema` and `outputSchema` where supported. If Smart98 does not expose
`outputSchema`, document and review an explicit response normalizer for the
actual returned MCP result format and test it using sanitized fixtures. Do not
simply mark the contract verified.

Separately verify official contest rules/window, account permissions, allowed
Spot markets, fees and market constraints, compliance eligibility, and the
activation record. This document does not enable live execution.
