# Implementation Plan — Feature 008

## Architecture

Keep three boundaries separate:

1. **Research/data layer:** existing offline kernel and verified public-data MCP tools; provenance and freshness are explicit.
2. **Decision layer:** strategy/AI analysis returns a typed intent and evidence. It cannot call HTTP or bypass policy.
3. **Execution layer:** deterministic policy validation plus a mediated adapter. It has no direct Wallex HTTP client and no API key. It delegates only to an explicitly verified Smart98/MCP tool contract. Until the actual tool names, schemas, permissions and error semantics are verified, the adapter is not connected to a runtime.

## Implementation sequence

1. Reconcile official order-create/order-detail URLs and source IDs in the source register.
2. Define a strict activation policy schema with required evidence fields and no numeric defaults.
3. Implement deterministic order validation using Decimal, explicit symbol/quote allowlists, canonical disabled-pair registry, and configured risk caps.
4. Define the mediated execution interface without inventing Smart98 tool names or schemas.
5. Add audit events and secret redaction; do not persist private balances or unnecessary account data.
6. Add tests for failures, timeout ambiguity, duplicate intent handling, partial fills, reconciliation and mode isolation.
7. Update docs, roadmap, discrepancy register, and source register.
8. Run all offline validators/tests and open a draft PR. Do not merge or activate live mode.

## Security and failure handling

- This adapter never receives an API key and never sends HTTP directly to Wallex.
- The model cannot supply arbitrary tool names; the caller uses only the verified contract supplied by the integration.
- Order intent fields must be validated and normalized before mediation.
- A timeout on order creation is an unknown outcome, not a failed order. Reconcile by client ID before any replacement intent.
- Unknown market state, unsupported pair, stale market data, missing risk limits, unknown fees, or unverified challenge rules blocks execution.
- Logs include intent ID, sanitized symbol, mode, policy version, and outcome class; never log keys, auth headers, private account snapshots, or full raw exchange responses.
- Offline tests use a synthetic policy and fake tool invoker only.
