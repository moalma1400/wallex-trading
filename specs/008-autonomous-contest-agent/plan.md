# Implementation Plan — Feature 008

## Architecture

Keep three boundaries separate:

1. **Research/data layer:** existing offline kernel and verified public-data MCP tools; provenance and freshness are explicit.
2. **Decision layer:** strategy/AI analysis returns a typed intent and evidence. It cannot call HTTP or bypass policy.
3. **Execution layer:** a separate, fixed-contract MCP module owns the API key, allowlist, pre-trade risk gate, order submitter, and reconciliation.

The execution layer must not be imported by backtest/shadow dispatch. State-changing requests have no automatic retries. All API routes are constants from official docs, not model-controlled inputs.

## Implementation sequence

1. Reconcile official order-create/order-detail URLs and source IDs in the source register.
2. Define a strict activation policy schema with required evidence fields and no numeric defaults.
3. Implement the fixed-contract client and offline fake transport.
4. Implement deterministic order validation using `Decimal`, explicit symbol/quote allowlists, canonical disabled-pair registry, and configured risk caps.
5. Expose create-order and order-detail tools only when live execution is enabled and the policy file passes validation.
6. Add event audit records and secret redaction; do not persist private balances or unnecessary account data.
7. Add tests for failures, timeout ambiguity, duplicate intent handling, and mode isolation.
8. Update docs, roadmap, discrepancy register, and source register.
9. Run all offline validators/tests and open a draft PR. Do not merge or activate live execution.

## Security and failure handling

- The model never receives the raw API key; only the execution process does.
- Order intent fields are validated and normalized before request construction.
- A timeout on order creation is an unknown outcome, not a failed order. Query by client ID before allowing any replacement intent.
- Unknown market state, unsupported pair, stale market metadata, missing risk limits, unknown fees, or unverified challenge rules blocks execution.
- Logs include intent ID, sanitized symbol, mode, policy version, and outcome class; never log keys, auth headers, private account snapshots, or full raw exchange responses.
- Offline tests use a synthetic API key and fake transport only.
