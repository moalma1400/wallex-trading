# Feature Specification: Historical Market Data and Data Quality

**Feature Directory**: `003-historical-market-data`
**Session Branch**: `arena/81f9fa39-wallex-trading` (fixed by Arena)
**Created**: 2026-10-21
**Status**: Local-only implementation and offline validation complete; no Wallex adapter
**Input**: Build a reproducible, strictly validated local market-data foundation compatible with Feature 002 replay.

## Context and boundaries

Feature 003 ingests only caller-supplied local CSV/JSON. It does not fetch Wallex data, open sockets, use keys, or access accounts. Public Wallex documentation informs versioned normalized record shapes but is not proof of availability, permissions, currentness, or an adapter contract. Source fields not established by evidence remain optional/unknown. Raw input bytes are content-addressed and retained unchanged beside normalized derivatives. No real Wallex historical dataset is included; committed samples are synthetic.

Feature 002 `Candle` and `run_replay` contracts remain unchanged. A validated historical candle record can be exported in Feature 002's exact CSV format; export requires a strict audit policy and clean audit. Research results remain limited by data provenance, missing venue semantics, and simplified replay costs/fills.

## User Scenarios & Testing

### User Story 1 — Import and retain historical local data (P1)

As a researcher, I can import a local CSV or JSON dataset with explicit source metadata and obtain deterministic versioned records without losing the original bytes.

**Independent Test**: Import the same fixture twice and verify identical dataset identity, record count, raw SHA-256 and normalized export; malformed schemas fail closed.

**Acceptance Scenarios**:
1. A canonical OHLCV CSV or a documented UDF/JSON record fixture is imported using explicit symbol, interval where applicable, source, retrieval method, and UTC ingestion time.
2. Reimporting identical bytes with identical dataset identity does not add rows or overwrite raw bytes; duplicates inside an input remain present and are reported, not silently removed.
3. Market metadata, public trade, fair-price snapshot, and documented depth snapshot records retain explicit symbol/time/provenance and Decimal values. Missing source timestamps remain absent; capture/ingestion time is not mislabeled as exchange time.

### User Story 2 — Assess data fitness before replay (P1)

As a researcher, I can receive machine-readable and human-readable data-quality reports that block replay export when material quality or completeness requirements are unknown or violated.

**Independent Test**: Corrupt, stale, incomplete, duplicate, mixed-symbol, out-of-order, unknown-symbol, or precision-policy-violating datasets produce visible issues and cannot be exported as replay-ready data.

**Acceptance Scenarios**:
1. Strict import rejects malformed timestamps/decimals/JSON and invalid OHLC before normalization; audit reports duplicate/out-of-order records, candle gaps, unknown symbols, stale/out-of-range data, precision-scale variation/policy breaches, and raw/normalized checksum conflicts.
2. No gap is interpolated, no row is sorted/dropped, no unknown interval is inferred, and no unknown precision/symbol policy is treated as validated.
3. Audit always emits JSON, issue CSV, and Markdown. Replay-compatible CSV export occurs only when all required caller policies are explicit and the dataset passes.

### User Story 3 — Preserve compatibility and safe extension seams (P2)

As a contributor, I can extend the local pipeline to future public providers without activating network access or changing Feature 002 replay semantics.

**Independent Test**: Provider protocol has no implementation, imports do not call network/credential libraries, and exported fixtures round-trip through the existing replay loader/engine.

**Acceptance Scenarios**:
1. Valid candle exports use Feature 002's unchanged seven-column schema and load via `load_candles`.
2. Only local CSV/JSON fixture readers exist; no HTTP, WebSocket, account, or order adapter is implemented.
3. Existing next-bar-open replay timing and explicit cost model remain unchanged.

## Functional Requirements

- **FR-001**: Support local CSV candle data and local JSON candle/market metadata/public trade/fair-price/depth fixtures with versioned schemas.
- **FR-002**: Require exact decimal parsing and aware timestamps; normalize aware times to UTC and reject naive/ambiguous times.
- **FR-003**: Each normalized record and dataset manifest MUST retain source ID/URL, retrieval method, ingestion/retrieval timestamp, schema version, and raw source SHA-256. A time supplied for capture is not represented as exchange-event time.
- **FR-004**: Preserve original input bytes unchanged in content-addressed storage and store normalized data as a separate deterministic derivative.
- **FR-005**: Repeated import of the same raw dataset identity MUST be idempotent. Do not silently deduplicate source records; declare logical keys and their limitations, report duplicates/conflicts, and preserve rows.
- **FR-006**: Validate record schema, symbol identity, timestamp order/timezone, OHLC/positive price/nonnegative quantity, interval consistency/gaps, explicit expected range/completeness, staleness against explicit as-of/max-age, and caller-supplied known-symbol/precision policies.
- **FR-007**: Missing interval, date range, freshness limit, symbol registry, or precision policy MUST be reported unknown; unknown policy MUST prevent replay readiness rather than silently pass.
- **FR-008**: Detect raw-file and normalized-file checksum mismatches and reparse-vs-normalized representation conflicts.
- **FR-009**: Produce deterministic JSON/CSV machine outputs and Markdown audit reports, including dataset/raw fingerprints, code/schema versions, source, range, symbol, interval, counts, warnings, and suitability.
- **FR-010**: Replay-ready exports MUST require an error-free candle audit with explicit caller-supplied interval, range, as-of/max-age, known symbol registry, and precision limits. Export exact Feature 002 CSV columns; leave raw files untouched.
- **FR-011**: Define a read-only future data-provider Protocol without a concrete network implementation. No network dependency, live feed, key, private account, order, transfer, or withdrawal path is permitted.
- **FR-012**: Model Wallex-documented market metadata, UDF OHLCV, public trades, fair-price snapshots, and depth data only to the extent of cited page schemas. Preserve differing REST/WebSocket representations and do not synthesize undocumented fields.
- **FR-013**: Do not change Feature 002 replay timing, fill logic, or cost model without a separately specified defect and regression test.
- **FR-014**: Document source disagreements, per-endpoint limits/pagination/timestamp unknowns, and incomplete OpenAPI artifact capture honestly. Never claim Wallex ingestion works without a reviewed, enabled adapter.

## Data records

- **Market metadata**: explicit symbol/base/quote and source-present optional Spot/product flags/precision labels.
- **Candle record**: symbol, explicit interval seconds, UTC start timestamp, Decimal OHLCV, and provenance; convertible to Feature 002 Candle.
- **Public trade**: symbol, UTC trade timestamp, Decimal quantity/price, source-present side indicator/sum when available; no exchange trade ID is invented.
- **Fair-price snapshot**: source timestamp plus symbol-to-Decimal price map, retaining omission semantics.
- **Order-book snapshot/side**: Decimal price/quantity levels, source/capture time distinction, and documented snapshot semantics; no deltas/sequence guarantees invented.
- **Dataset manifest/audit**: raw/normalized hashes, versions, source, ingestion time, range, counts, explicit policy, issues, and replay suitability.

## Success Criteria

- **SC-001**: CSV and JSON fixtures import locally with byte-preserved raw source, deterministic normalized records, and idempotent repeat imports.
- **SC-002**: Invalid, incomplete, stale, out-of-order, duplicate/conflicting, unknown-symbol, and precision-policy data cannot silently become replay-ready.
- **SC-003**: Audit emits reproducible JSON, CSV, and Markdown outputs with SHA-256 and provenance.
- **SC-004**: A clean synthetic candle dataset exports and runs through Feature 002 unchanged; invalid data is blocked before replay export.
- **SC-005**: Full existing/new tests and offline repository validators pass, with no network or credential integration.
- **SC-006**: Feature 001 coverage remains dated/incomplete; API-spec byte archives/checksums are claimed only if actual bytes were retrieved.

## Assumptions and deferred decisions

No Wallex public-data adapter, supported endpoint, request cadence, pagination rule, point-in-time market metadata, historical retention guarantee, symbol lifecycle, tick/lot interpretation, timezone boundary, or completeness boundary is assumed. Caller supplies source metadata and all audit policies. Identical trade tuples may be separate executions because current documented public-trade payloads lack a stable trade ID. Fair price is distinct from last-trade price. Depth snapshots from separate channels are not treated as an atomic two-sided book.
