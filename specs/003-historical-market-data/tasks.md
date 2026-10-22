# Tasks: Historical Market Data and Data Quality

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md)

## Phase 1: Specification and source evidence

- [x] T001 Inspect Feature 001/002, tests, repository state and document current API evidence/gaps before implementation.
- [x] T002 Create Feature 003 specification, plan, model, research, quickstart, requirements checklist and roadmap entry before code.
- [x] T003 Re-review official market/candle/trade/depth/ticker/stream pages; preserve modern/legacy and REST/WebSocket differences.
- [ ] T004 Complete the remaining Margin/OTC/Trade Credit artifact chunks where useful; exact raw bytes/checksums remain unavailable through transformed page-reader output.

## Phase 2: Canonical records and deterministic local storage

- [x] T005 Add versioned Decimal/UTC/provenance record models for market metadata, candles, public trades, fair-price snapshots, and documented depth snapshots.
- [x] T006 Add strict CSV/JSON parsers including UDF array length checks and duplicate JSON-key rejection.
- [x] T007 Add content-addressed immutable raw-file retention, deterministic normalized JSONL, hash-checked manifests and idempotent dataset identity.
- [x] T008 Add declared audit dedupe keys without discarding source rows; document trade-key collision limits.
- [x] T009 Add future read-only provider Protocol only, without concrete/network implementation.

## Phase 3: Quality audit and Feature 002 compatibility

- [x] T010 Implement explicit audit policies for intervals/ranges, freshness, known symbols and precision.
- [x] T011 Detect duplicates/conflicts, out-of-order data, gaps, invalid OHLC/quantities, incomplete/stale data, raw/normalized hash conflict, and unknown policies.
- [x] T012 Generate deterministic JSON, CSV and Markdown audit reports and a strict replay-eligibility gate.
- [x] T013 Export only clean candle data to Feature 002's unchanged seven-column CSV and prove replay compatibility.
- [x] T014 Add synthetic CSV/JSON fixtures and tests for idempotency, corruption, JSON/CSV errors, normalization, reports and replay gating.

## Phase 4: Documentation and validation

- [x] T015 Update data-quality skill, Persian-first data/API summaries, source register, coverage, research log and discrepancy register with bounded claims.
- [x] T016 Run complete old/new test suite, source/link validators, compilation and diff/security review; record exact results.
