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

## Provenance states and unresolved policy

The accepted tags are `PROVIDED_BY_CHALLENGE_BRIEF`, `OFFICIAL_SOURCE_VERIFIED`, `INFERRED`, `UNRESOLVED`, and `REQUIRES_ORGANIZER_CONFIRMATION`; `SYNTHETIC_FIXTURE` is reserved for test fixtures and is not a sixth challenge-claim status. Current max metadata age, official cutoff, fees and risk caps are unresolved. The config defaults to TMN-only quote support and refuses USDT without official permitted conversion evidence that covers the cutoff.

Feature 002 remains untouched: completed observation → next bar open, using explicit caller cost assumptions. No claim of live execution, Wallex data ingestion, account eligibility, settlement authority or profitability follows from this architecture or its tests.
