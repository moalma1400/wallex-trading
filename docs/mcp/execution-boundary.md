# Feature 008 — autonomous execution boundary

Feature 008 is a separate execution foundation. It does not broaden Feature 007's public/read-only MCP tool list. The policy and execution adapter do not call Wallex HTTP endpoints, do not hold an API key, and do not register any MCP tool by themselves. They delegate only through an injected caller for a verified Smart98/MCP execution contract.

## Implemented in this slice

- A policy schema requiring explicit official-rule, dedicated-account, market-list, risk-limit and compliance evidence.
- Explicit challenge start/cutoff timestamps, allowed Spot pairs, quote assets and verified order types.
- Deterministic Decimal-based checks for market allowlist/disabled pairs, Spot-only status, data freshness, order-rate/open-order limits, daily loss, spread, total estimated cost and order notional.
- A mediated execution adapter that requires a separately verified tool contract, including tool names, source URL and version.
- No automatic retry for an order-creation call. A timeout or invalid acknowledgement is treated as an unknown outcome and must be reconciled by client ID before any replacement order.
- Reconciliation remains available after the challenge cutoff so an uncertain order can be resolved.
- Offline-only fake-invoker tests. Tests do not invoke Smart98, MCP servers, or Wallex.

## Not yet enabled

No execution MCP tool is registered, no real tool contract is configured, no secret is configured, and no live request is made by tests. The current challenge policy file intentionally has unresolved official times, permissions, allowed markets and risk limits. It is not a valid live activation policy. Synthetic values in unit tests are test fixtures only and do not authorize live trading.

Before connecting this adapter to an agent, the project must verify the official challenge rules and time window, account-level permissions, explicit permitted Spot market list, current fee and precision/minimum-order rules, the exact Smart98/MCP order-tool contract, reliable account/order reconciliation, and current legal/compliance eligibility. Then record a separate owner activation decision. Do not store an API key in this repository or send it through model context.

## Official endpoint documentation

- Create Spot order: https://developers.wallex.ir/spot/createorder
- Spot order detail: https://developers.wallex.ir/spot/singleorderdetail
- Main account balances: https://developers.wallex.ir/basicservices/mainaccountwallet
- Active orders: https://developers.wallex.ir/spot/activeorders

These pages document API endpoints; they do not prove that a particular account is entitled to call them, nor do they establish a Smart98 tool contract. Cancellation remains unimplemented until its exact method, path, parameters and response contract are verified. Direct HTTP access from the agent/execution adapter is prohibited by the current repository constitution.
