# Feature 004 challenge-control architecture (offline only)

This documents repository contracts, not Wallex endpoint names or live exchange behavior. Challenge facts come from `USER-WALLEX-HACKATHON-BRIEF` and are not independently official-verified. See the [canonical KB](../knowledge-base/wallex-agentic-ai-hackathon.md).

## Local control path

```text
local metadata + raw-list registry + policy config
            │
            ▼
 is_challenge_spot_market_allowed(...) ── machine-readable reasons
            │ requires explicit config, strategy approval, and a separate
            │ successful risk verdict; metadata must be trusted/current
            ▼
 validate_market_order_amounts(...) ── precision/minimum checks
            │
            ▼
 evaluate_challenge_risk(...) ── configured independent caps and state
            │
            ▼
 DecisionEvent / DecisionAuditLog ── local JSONL, deterministic IDs
            │
            └── dispatch_order_intent(backtest|shadow|dry_run): record-only
                dispatch_order_intent(live): LIVE_EXECUTION_NOT_IMPLEMENTED
```

There is no submitter. `MarketRequest.risk_approved` must be supplied from the separately evaluated risk verdict; false denies. `MarketRequest.algorithmic_decision` must explicitly be true; manual trading intents are denied. `ChallengeModePolicy.explicit_configuration` is false for a bare in-memory default and is set only by loading the checked-in schema-validated offline policy. This prevents accidental authorization by a permissive default object.

## Component contracts

- `config/challenge/wallex_disabled_spot_pairs_raw.txt` is the verbatim user-provided appendix; JSON is derived and hash-checked. Runtime registry refuses duplicates, malformed entries, count/hash mismatch or noncanonical list. It never asserts that a non-disabled pair is available.
- `src/wallex_research/challenge.py` parses pair syntax, enforces the Spot-only policy, requires explicit trusted metadata state (`active`, `orderable`, `is_spot`, `challenge_enabled`), source/time/freshness, supported quote, strategy and risk approvals, and verified precision/minimum-order semantics. Decisions are pure and local; each block has a stable reason code.
- `src/wallex_research/challenge_risk.py` evaluates explicit independent per-order/asset/deployment, loss/drawdown, order-rate, freshness, spread/slippage/liquidity/cost, reconciliation and emergency-stop gates. All checked-in numeric limits are unset. `load_challenge_risk_limits` returns all limits as missing unless configuration status is explicitly `REVIEWED_INTERNAL` and evidence status is supplied; an unreviewed numeric edit cannot activate a cap.
- `src/wallex_research/challenge_execution.py` records offline intent only. The `submit_order` injection seam exists only to prove it is never called in tests. Live is blocked even if a caller attempts to enable the default.
- `src/wallex_research/decision_log.py` provides a versioned event contract and local append-only JSONL writer. It binds code/config/strategy/source and model/prompt provenance, requires typed event payloads, and refuses exchange-origin events, sensitive keys and obvious secrets. It is not connected to an LLM or exchange.
- `src/wallex_research/challenge_settlement.py` reports readiness only from an exact cutoff with source ID/HTTPS URL/SHA-256, reconciled balances, separately provenance-backed official valuation, known fees, known zero unrealized P&L and TMN-only inventory. Internal estimates are explicitly labeled and do not produce a settlement-ready value. A synthetic test-only mode is warned and cannot authorize operations. It does not liquidate, convert assets, retrieve balances or assign stale/invented token values.

## Smart98-mediated integration research (documentation only)

> **Architecture clarification (2026-10-23):** Smart98 is not required for the standalone execution path. The repository-owned MCP server may connect from Python to the official Wallex API and expose narrowly scoped tools to any compatible MCP host. A separate proposed feature branch adds opt-in Spot LIMIT-order tools in `src/wallex_mcp/live_spot.py`; these are distinct from this Feature 004 offline research/settlement module. This architecture text describes Feature 004's offline boundary, not the capability of the separate standalone MCP server. No production request was made by the tests.

### Evidence and confirmed scope

- **Smart98:** the user identifies Smart98 as the organization's AI Agent platform and intended mediator for MCP servers, tools, skills, and controlled workflows. This role is accepted as a project requirement from the user; no Smart98 product documentation, integration contract, runtime, tool list, or configuration is present in this repository. The Arena Smart98 connector lookup for this session returned `unsupported`; this only means no Smart98 connector tools were available here, not that the platform itself is unavailable.
- **Wallex API:** the repository's registered official documentation includes market metadata (`MARKETS`), Spot market metadata (`SPOT-MARKETS`), an overview (`MOD-INTRO`), and a generated order-create page (`MOD-GENERATED-POST-ACCOUNT-ORDERS`). These are **documentation-level capabilities only**. The order-create page is state-changing documentation, not authorization. Host/schema discrepancies and incomplete contracts are already recorded in [API overview](overview.md) and [source register](../research/source-register.yaml); no runtime, account permission, or challenge entitlement is confirmed.
- **Wallex MCP:** no authoritative Wallex MCP implementation, publisher/repository, version, URL, tool inventory, or permission contract is registered in this checkout. The only Wallex MCP mention found is in the user-supplied hackathon transcript; it remains transcript-only, not official confirmation. No Wallex MCP tool is confirmed.
- **Tools accessible through Smart98:** none are verified. There is no evidence that a Wallex MCP can be registered with, routed through, or safely exposed by Smart98.
- **Feature 004 trading/research agent:** this subsystem validates caller-supplied/local data, applies local eligibility/risk checks, replays local decisions, and logs local events. Its `src/wallex_research/challenge_execution.py` remains offline-only and has no submitter. The separate `src/wallex_mcp/` server is the direct API boundary; proposed live tools are opt-in and documented in [the standalone MCP guide](../mcp/README.md).

### Required integration-layer matrix

| Integration layer | Responsibility | Confirmed interface | Authentication boundary | Read/write classification | Evidence | Status |
|---|---|---|---|---|---|---|
| Wallex API | Exchange-side underlying market/account/trading capabilities | Official docs expose market and Spot-market documentation plus a generated order-create schema; exact runtime contract is not selected | Some generated private API pages document API-key authentication, but current host/auth/permission contract is incomplete or conflicting. No credentials are stored or supplied to the model. | Market metadata pages: documented read. Order-create page: documented write/state change; disabled in this project. Account-sensitive reads are not enabled. | [`MOD-INTRO`](https://developers.wallex.ir/docs), [`MARKETS`](https://developers.wallex.ir/docs/basic-services-markets), [`SPOT-MARKETS`](https://developers.wallex.ir/docs/spot-active-markets), [`MOD-GENERATED-POST-ACCOUNT-ORDERS`](https://developers.wallex.ir/docs/generated/post-account-orders); [discrepancies](../research/discrepancies.md) | **Docs confirmed; runtime, auth, permissions, and availability UNKNOWN.** No direct application connection is allowed. |
| Wallex MCP | Potential MCP representation of exchange capabilities | No authoritative implementation or tools confirmed | Unknown; do not infer credential type, delegation, or secret handling | Unknown. No tools exposed/used. Presence of a future tool would not authorize use. | No official MCP source in [source register](../research/source-register.yaml); transcript mention is user-provided and unverified. | **UNKNOWN / unverified.** Require canonical publisher URL/repository, version, source/license, schemas, permissions, and side-effect documentation. |
| Smart98 platform | Organizational AI Agent platform and mandatory mediation layer for any future Wallex API/MCP access | The role as the intended mediator is specified by the user's project context only. No product API, SDK, MCP registry, admin docs, tool catalog, or runtime endpoint is available here. | Actual user/model/tool/secret authentication boundary and credential storage are unknown. Security requirement: exchange credentials must not enter the LLM context or this repository; any future secret reference must be controlled outside the model and separately verified. | Platform capability and access classification unknown. Project policy requires approved, least-privilege tools; no writes are permitted here. | Current user instruction; no Smart98 interface source in checkout. Existing [unresolved questions](../research/unresolved-questions.md). | **Role confirmed by user context; capabilities and interface UNKNOWN.** No Smart98 configuration or integration changed. |
| Tools exposed to the agent through Smart98 | Discover/use only explicitly approved tools/workflows | No tool names, discovery API, schemas, MCP transport, registration flow, or Smart98-to-Wallex path confirmed | Unknown; require evidence for both platform identity/auth and upstream Wallex credential isolation | No tools confirmed. Future categories must be allow-listed separately as public read-only, account-sensitive read, and state-changing write. | No Smart98 docs/runtime or Wallex MCP catalog available in repository/session. | **UNKNOWN.** Compatibility and permissions must be demonstrated before an adapter can be specified. |
| Wallex trading agent in this repo | Strategy-independent validation, backtest, shadow proposal, and risk control | Existing local Python domain models and offline functions. `TargetExposure` is a caller-supplied strategy-output input to replay, not a Smart98 connection or external tool contract. No provider adapter exists. | No network authentication or secrets. | Local file reads and local decision-log writes only. Shadow is record-only; no submit/amend/cancel. | Existing `src/wallex_research/`, tests, [Feature 002 contract](../../specs/002-offline-research-kernel/contracts/offline-replay.md), `.agents/skills/smart98-interface-boundary/`, and this architecture. | **Confirmed local/offline only.** No live feed or live order path. |
| Proposed internal `MarketDataPort` (not implemented) | Keep strategy insulated from MCP/Smart98/provider-specific contracts; receive normalized, provenance-bearing market observations | Conceptual internal, read-only port only. A future implementation spec may define the internal query/result types and mapping to the repository's market-data domain after exact upstream contracts are verified. This label is **not** an MCP tool name or external schema. | Port itself accepts no exchange credential. Any future provider adapter must talk only to a verified Smart98-mediated interface; the Smart98 auth mechanism remains unknown. | Read-only market data. It excludes balances, private orders, and all order mutations. | Proposed design in this document; existing local data and normalized Candle/market snapshot models. | **Proposed, not implemented or transport-bound.** Unknown provider/eligibility blocks use. |

### Proposed strategy-independent data path

```text
Wallex API or an authoritative Wallex MCP (source and contract UNKNOWN)
                              ⇅ only if verified and approved
Smart98-approved integration / workflow (interface and routing UNKNOWN)
                              ⇅ only if verified and approved
Future Smart98 adapter (not implemented; no direct Wallex connection)
                              ⇅ internal domain mapping
Proposed read-only MarketDataPort (provider-neutral; not implemented)
                              ↓
Local provenance + data-quality + fail-closed Spot eligibility + deterministic risk checks
                              ↓
Strategy/backtest/shadow records proposed decisions only
                              X no order placement, amendment, or cancellation path
```

The adapter must be configurable/provider-neutral at the internal boundary: strategy code consumes the internal market-data port, not Wallex MCP names or Smart98 SDK classes. Provider selection, protocol, query schema, and field mapping remain unset until authoritative Smart98 and upstream source contracts are reviewed. An unknown/unconfigured provider must fail closed, not fall back to direct Wallex access.

### Access classes and execution boundary

1. **Public/read-only market data** — only a future explicitly approved Smart98-exposed tool could feed shadow observation. Every record must retain source identity, observation/capture time, completeness, and evidence needed for freshness and market eligibility; exact external schema is not assumed here.
2. **Account-sensitive reads** — balances, private order history, fees, or account state are not part of the proposed market-data port. They require separate explicit authorization, privacy/security review, reconciliation contract, and least-privilege verification. They remain disabled.
3. **State-changing operations** — place, amend, and cancel orders are not exposed by this architecture and remain disabled. No strategy/model output or tool discovery can bypass local deterministic eligibility and risk vetoes. A tool's presence is never permission to call it.
4. **Shadow** — may observe only authorized read-only data and record proposed decisions. It cannot submit, amend, or cancel an order; it does not imply a live feed exists in the current implementation.

Credentials, exchange secrets, and private keys MUST NOT be placed in prompts, model messages, logs, repository files, fixtures, or test output. A future Smart98-side secret-handling boundary is a security requirement to verify, not a confirmed Smart98 feature. All market decisions remain subordinate to deterministic validation/risk code outside the model. `UNKNOWN`, stale, contradictory, inactive, or prohibited market evidence stays blocked.

### Smart98/Wallex compatibility evidence required

Before even a read-only adapter can be proposed, obtain and review:

1. Smart98 product/version documentation or an owner-reviewed interface contract: architecture, environment, supported MCP transport(s)/versions, registration lifecycle, network/egress and service identity.
2. Smart98 approved-tool discovery/allowlist behavior; exact tool descriptions and versioned input/output schemas; input validation and output provenance; model-visible fields and data filtering.
3. Authentication/delegation boundary: who holds Smart98 credentials, how the upstream Wallex secret is referenced and isolated from the model, scopes/permissions, rotation/revocation, and whether agent/tool logs can contain secrets or private data.
4. Error semantics and propagation: timeout budgets, retry behavior, cancellation, partial/invalid output, rate limiting, availability, idempotency where relevant, and how each outcome reaches the caller without inventing success.
5. Audit/logging: actor/tool/version, request/result provenance, timestamps, policy decisions, redaction, retention, access controls, and evidence that no secret or personal/account data leaks into model context or repository.
6. Wallex MCP authority: canonical publisher and source URL, maintained repository/package, release/version, transport and deployment model, tool catalog, schemas, permissions, upstream authentication, read vs write effects, rate limits, and security/disclosure process.
7. An explicit Smart98 compatibility/approval statement for the exact Wallex MCP/API integration and tool scopes. If unavailable, record compatibility as `UNKNOWN`; do not attempt registration or test production.
8. A separate approved non-production contract/security test plan. This documentation task performs no runtime test, production request, credential creation, MCP installation, or Smart98 configuration change.

Until these evidence items exist, Smart98-to-Wallex MCP compatibility remains `UNKNOWN` and is not required for the standalone server. For the standalone direct-API path, rely only on the fixed official host, documented endpoints, explicit local configuration, and reviewed tool scopes; live trading remains disabled unless the separate live-Spot feature is explicitly configured by the operator.

## Provenance states and unresolved policy

The accepted tags are `PROVIDED_BY_CHALLENGE_BRIEF`, `OFFICIAL_SOURCE_VERIFIED`, `INFERRED`, `UNRESOLVED`, and `REQUIRES_ORGANIZER_CONFIRMATION`; `SYNTHETIC_FIXTURE` is reserved for test fixtures and is not a sixth challenge-claim status. Current max metadata age, official cutoff, fees and risk caps are unresolved. The config defaults to TMN-only quote support and refuses USDT without official permitted conversion evidence that covers the cutoff.

Feature 002 remains untouched: completed observation → next bar open, using explicit caller cost assumptions. No claim of live execution, Wallex data ingestion, account eligibility, settlement authority or profitability follows from this architecture or its tests.
