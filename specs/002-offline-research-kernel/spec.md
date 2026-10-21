# Feature Specification: Offline Strategy-Neutral Research Kernel

**Feature Directory**: `002-offline-research-kernel`<br>
**Session Branch**: `arena/81f9fa39-wallex-trading` (fixed by Arena; no feature branch created)<br>
**Created**: 2026-10-21<br>
**Status**: In Progress — offline first slice delivered; additional integrations and research remain deferred<br>
**Input**: Continue the Wallex research repository with safe offline data-quality, deterministic replay/backtesting, risk and paper-ledger primitives, reusable agent skills, and an integration boundary that does not assume Smart98's contract.

## Context and boundaries

Feature 001 remains the source inventory and Persian-first knowledge base and is not complete. This feature implements a small, strategy-neutral local research kernel using only synthetic fixtures or local files supplied by the user. It is not a Wallex client and does not fetch, subscribe, authenticate, execute, or modify anything remotely. It selects no strategy, market, interval, capital amount, fees, leverage, or personal risk profile. Required simulation assumptions are explicit caller inputs. Spot-only simulated exposure is supported; short positions and margin/leverage are rejected or out of scope.

The official docs currently expose materially inconsistent API hosts, WebSocket versions, and endpoint schemas; none of those contracts are adopted as runtime interfaces. The sourced conclusions and open gaps remain in Feature 001 artifacts. No verified Smart98 API/SDK contract was found in this repository; no Smart98 adapter is built.

## User Scenarios & Testing

### User Story 1 — Validate local market data (Priority: P1)

As a researcher, I can load a caller-supplied local CSV dataset and get deterministic, actionable data-quality results before replaying it.

**Why this priority**: All later offline analysis depends on trustworthy inputs; missing/duplicate/out-of-order data must not be silently repaired.

**Independent Test**: Standard-library tests exercise valid and invalid synthetic OHLCV rows, UTC parsing, duplicates, ordering, symbol consistency, and optional expected-interval gaps; the CLI works with local fixtures and never fetches data.

**Acceptance Scenarios**:
1. **Given** a well-formed local CSV, **When** it is parsed and audited, **Then** exact decimal values and UTC timestamps are preserved and the report is valid.
2. **Given** malformed prices/timestamps or invalid OHLCV values, **When** the CSV is loaded, **Then** parsing fails with a row-specific `CSVDataError`; given duplicate or unordered timestamps, mixed symbols, or a configured interval mismatch/gap, the audit reports stable issue codes and never auto-corrects the data.
3. **Given** no expected interval is supplied, **When** the dataset is audited, **Then** cadence/gap completeness is reported as unknown rather than inferred.

### User Story 2 — Run a strategy-neutral deterministic backtest (Priority: P2)

As a researcher, I can replay explicitly supplied target-exposure signals over valid local OHLCV data without the repository choosing a strategy or using future prices.

**Why this priority**: This provides a verifiable calculation path while separating the choice of a strategy from the engine and making simplified execution assumptions visible.

**Independent Test**: Fixed fixtures and explicit configuration produce stable fills, cash/equity series, fees, slippage, and drawdown. A signal observed at a bar close can only fill at the next bar open; a final-bar signal without a later bar is rejected.

**Acceptance Scenarios**:
1. **Given** valid ordered bars, explicit initial cash, explicit cost rates, an explicit exposure limit, and target-exposure signals, **When** replay runs, **Then** results are deterministic and all fills occur no earlier than the next bar open.
2. **Given** an omitted or invalid required assumption, a target exposure above the supplied maximum, or an attempt to short, **When** replay is requested, **Then** it fails closed with a clear error and does not silently substitute a default or clamp risk.
3. **Given** a synthetic fixture with a known price path and explicit costs, **When** replay runs, **Then** the reported accounting components reconcile and are described as model outputs, not profitability evidence or Wallex fees.

### User Story 3 — Keep paper research safe and reusable (Priority: P3)

As a contributor, I can use a local paper ledger and shared agent skills while knowing no exchange, account, or Smart98 action can be reached from the implementation.

**Why this priority**: Reusable research procedures, explicit risk boundaries, and lack of live adapters reduce the chance that offline experiments are mistaken for execution.

**Independent Test**: Inspect the import/dependency surface and run tests offline; verify no network client, credential loader, live-feed adapter, or order-submission interface exists. Verify all example data is synthetic and all required simulation values are explicit.

**Acceptance Scenarios**:
1. **Given** a paper replay, **When** its ledger records a fill, **Then** it is an in-memory/local simulation result with an explicit synthetic execution model and no remote side effect.
2. **Given** a contributor uses a source, contract, data-quality, backtest, risk, paper-simulation, security, or compliance skill, **When** they follow it, **Then** it directs them to cite evidence, remain offline, and defer unknown decisions rather than inventing them.
3. **Given** a proposal to connect a real exchange or Smart98, **When** it is reviewed, **Then** implementation is blocked pending separate specification, current contract/security/risk review, explicit authorization, and jurisdiction-specific legal/compliance review; no legality guarantee is made.

## Edge Cases

- A CSV uses naive timestamps, invalid ISO-8601, non-finite Decimal values, or numeric binary floats.
- High/low values violate OHLC consistency; prices are zero/negative; volume is negative.
- Duplicate or non-increasing candle timestamps occur, or multiple symbols appear in a single-series replay.
- An interval is not specified; no gap assertion is made. If supplied, gaps are reported and never filled synthetically.
- No signal exists, a signal timestamp is not a candle close, signals are duplicated/out of order, or the final signal has no later execution bar.
- Costs are omitted, negative, or at/above invalid bounds; the engine does not inject a presumed Wallex fee.
- Available cash is insufficient after simulated fee/slippage; the fill is explicitly limited by the local cash ledger and the shortfall is reported.
- The data is stale, incomplete, adjusted, licensed restrictively, or supplied from an unknown source; provenance/fitness remains the user's responsibility and the program does not assert exchange provenance.

## Requirements

### Functional Requirements

- **FR-001**: System MUST parse only local CSV inputs with an explicit OHLCV schema and exact decimal conversion; no online data fetch is permitted.
- **FR-002**: System MUST normalize aware timestamps to UTC and reject naive or invalid timestamps.
- **FR-003**: System MUST reject malformed CSV/OHLCV values with a row-specific local parsing error and report duplicate/non-monotonic timestamps, mixed symbols, and gaps when an expected interval is explicitly supplied.
- **FR-004**: System MUST NOT repair, interpolate, forward-fill, or fabricate missing observations.
- **FR-005**: System MUST use a strategy-neutral target-exposure input port; it MUST NOT include a selected or sample trading strategy.
- **FR-006**: The replay MUST use close-observed signals no earlier than the next candle's open and MUST reject signals that cannot be causally executed.
- **FR-007**: Every simulation MUST require explicit initial cash, quote-currency label, commission rate, slippage rate, and maximum Spot exposure; no personalized or Wallex-specific values may be defaulted.
- **FR-008**: Risk checks MUST reject invalid or over-limit exposure and short positions; no leverage or margin simulation is implemented.
- **FR-009**: Paper fills MUST remain local simulated outputs and MUST never call an exchange, account, public feed, order endpoint, or remote Smart98 service.
- **FR-010**: Results MUST report assumptions and modeled fees/slippage, returns, and drawdown without profitability claims or execution guarantees.
- **FR-011**: Runtime and tests MUST use only the Python standard library and MUST work offline.
- **FR-012**: The system MUST contain no credential loading, user/account-data collection, or exchange execution adapter.
- **FR-013**: Smart98 MUST remain an unspecified future strategy-signal provider boundary only; no endpoint, authentication, payload, capability, or SDK may be invented.
- **FR-014**: Documentation MUST preserve Feature 001's incomplete status and source conflicts; the offline kernel MUST not be presented as a validated Wallex API implementation.
- **FR-015**: Before any future real exchange-use proposal, documentation MUST require an independent, current, jurisdiction-specific legal/compliance gate, including sanctions and access restrictions, without guaranteeing legality.

### Key Entities

- **Candle**: Caller-supplied market observation with symbol, UTC timestamp, decimal OHLC, and decimal volume.
- **QualityIssue / QualityReport**: Deterministic audit findings with stable code, severity, optional row, and validity result; CSV parsing/model failures raise `CSVDataError` separately.
- **TargetExposure**: Caller/strategy-produced desired Spot exposure fraction observed at a candle close; it is input, not a repository-selected strategy.
- **SimulationConfig**: Explicit initial cash, quote-currency label, cost model, and maximum exposure.
- **SimulatedFill**: Local modeled fill at a later candle open with reference price, modeled fill price, quantity, fee, and side.
- **LedgerPoint / ReplayResult**: Cash, position, equity, peak-to-trough drawdown, modeled costs, and event outputs for a deterministic replay.

## Success Criteria

- **SC-001**: Offline standard-library tests cover valid input, malformed input, time-zone handling, duplicate/order/gap detection, and no-auto-repair behavior.
- **SC-002**: Deterministic replay tests verify next-bar execution, cost accounting, cash bounds, Spot-only limits, and drawdown calculations using synthetic fixtures.
- **SC-003**: Runtime source contains no network or credential integration and requires explicit simulation assumptions; this is verified by code review and offline tests.
- **SC-004**: Both source and Markdown validators pass, the full local test suite passes, and repository diff is clean.
- **SC-005**: User-facing safety, source gaps, known model simplifications, and feature status are documented in English artifacts and Persian-first knowledge pages.

## Assumptions and Deferred Decisions

- Python 3.11 is available in this workspace; implementation uses only Python standard library features.
- The first replay processes a single symbol/quote ledger per run. Multi-asset portfolio accounting is deferred rather than inferred.
- Dataset licensing, source authenticity, and intended use are outside automated verification and must be supplied/assessed by the user.
- Fee and slippage inputs are deliberately generic simulation parameters; they are not current Wallex values.
- No strategy, market, candle interval, initial capital, risk preference, or Smart98 contract is selected by this feature.
- Public read-only Wallex access, API contract adapters, live paper trading, user-specific compliance advice, and all live trading are excluded.
