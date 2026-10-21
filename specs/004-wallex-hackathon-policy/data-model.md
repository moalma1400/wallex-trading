# Data model: challenge evidence and offline control

## Evidence status

Enum string: `PROVIDED_BY_CHALLENGE_BRIEF`, `OFFICIAL_SOURCE_VERIFIED`, `INFERRED`, `UNRESOLVED`, `REQUIRES_ORGANIZER_CONFIRMATION`. Each source record binds source ID, type, local file/hash or official URL, UTC retrieval time when available, and evidence status. A user attachment has no fabricated URL or time.

## Disabled market registry

- Raw source: exact UTF-8 text file, original line order/case/content, SHA-256.
- Canonical derived record: schema version, source ID/hash, raw/unique/duplicate/duplicate-excess/malformed counts, sorted list of canonical pair strings.
- Pair: uppercase ASCII `[A-Z0-9]+/[A-Z0-9]+`; normalization never repairs invalid delimiters or characters.
- Runtime use requires raw hash match and zero duplicates/malformed entries. Canonical list is derived, never hand-maintained.

## Market metadata snapshot

Contains explicit pair, spot/type state, active/enabled/orderable booleans, source identifier, evidence status, official source URL/content hash, observed/fetched UTC timestamps, and verified precision/minimum-order metadata. A validity decision requires all facts explicit, consistent, fresh against configured internal max age, trusted, and not synthetic except under test-only mode. Fields are internal contract semantics, not claims about actual Wallex response field names.

## Eligibility decision

Immutable result: decision (`ALLOW`/`DENY`), normalized pair if valid, ordered machine-readable reason-code tuple, warnings, metadata/source IDs and as-of timestamp. Positive decision requires `ChallengeModePolicy.explicit_configuration=true` (set by the offline policy loader), valid spot state, allowed quote and settlement path, absent from verified disabled registry, explicit `MarketRequest.strategy_allows_pair=true`, `algorithmic_decision=true` (manual intent is denied), and `risk_approved=true`, and verified order constraints. Any unknown denies.

## Risk limits and proposal

Internal risk-limit fields include order, per-asset and total exposure caps; open order/order-rate caps; daily loss/drawdown/consecutive loss/error controls; market/signal age; spread, slippage, liquidity-utilization and aggregate-cost limits. Missing or null values are unset and veto. Proposal captures normalized pair, quantity/notional, known costs, reconciled-state flag and fresh evidence references. Limits are neither official nor numeric recommendations.

## Decision event

Versioned record includes deterministic event ID; UTC timestamp; run ID/sequence; event type; origin/mode; code SHA; config SHA; strategy version; event-schema version; source/data references; typed event payload; and AI model/provider/prompt version when event type is AI analysis. Append-only JSONL stores no credentials, PII or exchange-origin events. Financial values are canonical decimal strings (not binary floats).

## Settlement snapshot

Captures official cutoff evidence and exact timestamp with source ID/HTTPS URL/SHA-256; reconciled balance status; TMN cash; non-TMN holdings; realized P&L; unrealized estimate; fees; and valuation status (`OFFICIAL` or `INTERNAL_ESTIMATE`) with its own evidence status/source ID/URL/hash. Readiness is false unless exact cutoff provenance and official valuation are verified, fees/unrealized are known, balances reconcile, and inventory is TMN-only. Synthetic test evidence can calculate only with an explicit test-only flag and warning. No conversion rate is inferred.
