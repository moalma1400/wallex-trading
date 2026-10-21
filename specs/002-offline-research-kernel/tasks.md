# Tasks: Offline Strategy-Neutral Research Kernel

**Input**: [spec.md](spec.md), [plan.md](plan.md), [research.md](research.md), [data-model.md](data-model.md), [quickstart.md](quickstart.md), [offline replay contract](contracts/offline-replay.md)

## Phase 1: Setup

- [x] T001 Create the single-project `src/wallex_research/` package layout and document the local `PYTHONPATH=src` execution convention (no install-time dependencies).
- [x] T002 Establish `unittest` discovery and synthetic-only fixtures without adding dependencies.

## Phase 2: Foundational models and data quality (US1)

- [x] T003 [US1] Add strict Decimal/UTC Candle and quality-report models in `src/wallex_research/models.py`.
- [x] T004 [P] [US1] Add no-repair OHLCV chronology/symbol/gap checks in `src/wallex_research/data_quality.py`.
- [x] T005 [P] [US1] Add strict local CSV parser in `src/wallex_research/csv_io.py`.
- [x] T006 [P] [US1] Add synthetic valid/invalid fixtures and unit tests in `tests/fixtures/` and `tests/test_data_quality.py`.
- [x] T007 [US1] Add offline data audit CLI with explicit optional interval in `scripts/check_market_data.py`.

## Phase 3: Strategy-neutral replay/backtest (US2)

- [x] T008 [US2] Define explicit cost/config/target-exposure/replay result types in `src/wallex_research/models.py`.
- [x] T009 [P] [US2] Implement caller-specified Spot exposure fail-closed rules in `src/wallex_research/risk.py`.
- [x] T010 [P] [US2] Add deterministic synthetic replay fixtures and causal timing/cost/risk tests in `tests/test_replay.py`.
- [x] T011 [US2] Implement local close-signal/next-open execution, cash ledger, modeled costs and drawdown in `src/wallex_research/replay.py`.

## Phase 4: Safety, docs, and review (US3)

- [x] T012 [US3] Create reusable source/contract/data-quality/backtest/risk/paper/security/compliance agent skills under `.agents/skills/`.
- [x] T013 [US3] Update constitution and repository security/contribution instructions to permit offline-only work and retain live-use/compliance gates.
- [x] T014 [US3] Add a Persian-first summary of newly reviewed official REST/WebSocket docs and endpoint-host conflicts in `docs/api/`, `docs/fa/`, and Feature 001 discrepancy/open-question records.
- [x] T015 [US3] Run all offline unit tests and source/link validators; inspect diffs for network calls, secrets, unsupported exchange assertions, and unapproved values.
- [x] T016 [US3] Record exact counts, unresolved issues, and validation outcomes in Feature 001 research log and Feature 002 task/spec state.

## Dependencies and execution order

- Data models, strict parsing, and quality checks precede replay; replay tests pin the execution/cost semantics before engine implementation.
- Repository instructions and feature artifacts precede implementation. Skills and documentation can proceed alongside local tests.
- All validation is offline. No task creates credentials, calls a production endpoint, connects to a feed, or modifies an account.

## Implementation Strategy

Deliver a useful offline validator and tested deterministic replay in small increments. Preserve Feature 001 as in progress because most sitemap bodies remain unread. Do not build an integration adapter or claim complete coverage. A later proposal for public read-only exchange access, Smart98-specific integration, or real trading requires a separate specification and review.
