# Feature 008 Specification: Autonomous Contest Agent Execution

**Status:** Approved for implementation preparation; live execution remains disabled until activation evidence is complete  
**Date:** 2026-10-23  
**Parent context:** Features 004, 005, and 007; Wallex Trading Constitution v1.3.0

## Goal

Extend the existing research and MCP foundation toward a continuously operating, algorithmic Spot-trading agent for the Wallex/Starcoach competition. The agent should gather verified data, analyze it, generate and evaluate strategy hypotheses, apply deterministic risk/eligibility gates, and manage permitted orders with an auditable lifecycle. The AI may choose among supported analysis tools, but cannot bypass deterministic eligibility or risk policy.

This feature is separate from Feature 007's public/read-only MCP scope. It must not silently broaden Feature 007 or weaken its tests. State-changing order tools live in a distinct execution module and remain disabled by default.

## Evidence and known constraints

- Official Wallex documentation describes Spot order creation as `POST /v1/account/orders`, authenticated with `x-api-key`, with JSON fields `client_id`, `price`, `quantity`, `side`, `stop_Price`, `symbol`, and `type`. Source ID: SPOT-CREATE — [official create-order documentation](https://developers.wallex.ir/docs/spot-create-order).
- Official documentation describes order lookup as `GET /v1/account/orders/{client_id}` with `x-api-key`. Source ID: SPOT-DETAIL — [official order details](https://developers.wallex.ir/docs/spot-single-order-detail).
- The official API docs use the `api.wallex.ir` host in the introduction and these endpoint pages. Documentation conflicts remain for some generated market-data routes and are tracked in `docs/research/discrepancies.md`.
- The exact order-cancellation contract, account-level API permissions, challenge-account access, current challenge window, allowed markets, fee schedule, precision/minimums, and settlement rules are not yet independently verified. Do not invent these.
- The owner has requested autonomous algorithmic execution for the competition. That is product intent, not proof that an account or tool is currently authorized.

## Included

1. A separate execution package that exposes only fixed, documented Spot-order operations; no arbitrary HTTP, URL, header, method, or path inputs.
2. Order submission and order-detail lookup through the repository-owned MCP mediation layer, not from the strategy/model directly to Wallex.
3. A policy loader that fails closed unless live mode, owner activation, verified challenge rules/account, explicit allowed Spot pairs, fee evidence, verified price/quantity steps and minimums, and numeric risk limits are present.
4. Deterministic pre-trade checks for symbol eligibility, disabled-pair registry, Spot-only scope, explicit quote allowlist, verified precision/step/minimum constraints, quote/base balances by side, maximum order and asset notional, total deployed exposure, open-order cap, order-rate cap, fee/spread limits, daily loss, and stale/missing inputs.
5. Decimal-safe values, unique client order IDs, no automatic retry of state-changing POST requests, and explicit “outcome uncertain; reconcile by client ID” behavior on timeouts.
6. Offline fake-transport tests; no live requests or secrets in CI.
7. Decision, risk-verdict, order-intent, acknowledgement, and reconciliation audit events with redaction.
8. Integration points for AI analysis, backtesting, shadow mode, and tool selection without granting the model authority to override policy.

## Excluded until exact evidence is verified

- Order cancellation/amendment: do not implement until the exact official route, method, parameters, and response contract are recorded and reviewed.
- Margin, leverage, borrowing, shorting, derivatives, OTC execution, deposits, transfers, withdrawals, wallet actions, or any action not explicitly permitted by official competition rules.
- Arbitrary API access, credential forwarding to the model, or direct Wallex calls from strategy/business logic.
- Automatic live activation from a prompt, config toggle alone, or missing/ambiguous evidence.
- A built-in trading strategy, default market, timeframe, fee, capital amount, numeric risk value, or profitability claim.

## Required behavior

- Public data collection, strategy evaluation, and backtests must not need a private API key.
- Shadow and paper modes must be structurally unable to call the order submitter.
- Live mode must fail closed unless all readiness evidence is valid and the dedicated activation record is present.
- Every live order must pass deterministic policy and risk validation outside the LLM.
- The client must never automatically retry an order POST after timeout or connection loss; it must reconcile by `client_id` before a new intent can be sent.
- The agent must reject symbols missing from an explicit allowlist, symbols in the canonical disabled-pair registry, non-Spot markets, unsupported quote assets, stale market metadata, malformed decimals, missing risk limits, and unreconciled account/order state.
- No claim of successful execution may be made unless a valid exchange acknowledgement or reconciled order detail confirms it.

## Acceptance criteria

1. Existing Feature 007 public-only behavior and tests remain unchanged.
2. Execution tools are in a separate package and disabled by default.
3. Order creation uses only the official fixed host/path and documented JSON field names.
4. Order lookup escapes/rejects path injection and uses only a validated client ID.
5. All financially relevant arithmetic uses `Decimal`; no binary-float sizing.
6. The policy gate rejects missing, stale, contradictory, or incomplete challenge/account/risk evidence.
7. Offline tests cover valid orders, invalid symbols, disabled pairs, unsupported quote assets, notional cap, open-order cap, invalid decimals, missing API key, live mode disabled, timeout ambiguity, and redaction.
8. No automatic retries occur for POST; GET lookup may use bounded retry only when safe.
9. No cancel/withdraw/transfer/deposit/margin/derivatives tools are registered.
10. Source-register and discrepancy entries cite the official order docs and retain unresolved permission/competition questions.
11. Full offline test suite, source validator, link validator, compile check, and `git diff --check` pass before merge.
12. Live activation remains disabled until challenge rules/window, dedicated-account permissions, allowed Spot markets, deterministic risk values, current compliance review, and explicit activation are recorded.

## Open blockers

- Organizer-confirmed official rules, window/cutoff, and allowed Spot-market list.
- Dedicated challenge-account API permissions and safe credential storage.
- Exact fee schedule, symbol precision/minimums, order rate limits, and settlement route.
- Exact cancellation contract.
- Current jurisdiction/compliance eligibility review.
- Strategy/model selection and measurable objective: not inferred by this feature.
