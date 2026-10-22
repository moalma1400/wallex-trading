# Implementation Plan: Historical Market Data and Data Quality

**Branch**: `arena/81f9fa39-wallex-trading` (fixed Arena branch) | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

## Summary

Add a dependency-free local import/store/audit/export layer. Preserve source bytes by SHA-256, normalize into versioned JSONL, and record deterministic manifests. Accept strict candle CSV and documented JSON shapes for market metadata, public trades, fair-price snapshots, order-book snapshots/side snapshots, and UDF candle arrays. Gate replay-compatible export using explicit freshness, completeness, symbol and precision policies. Do not alter Feature 002 replay or add remote providers.

## Technical context

- Python 3.11+, standard library, `unittest`; no dependency installation.
- Local dataset root with `raw/sha256/`, `datasets/<dataset-id>/`, and report files.
- Caller-provided source metadata and explicit UTC retrieval/ingestion timestamps; depth also requires distinct capture time. No implied Wallex retrieval.
- Versioned normalized record schemas; decimal strings/canonical JSON; no lossy float parsing.
- Atomic, deterministic normalized writes; raw inputs are immutable and content-addressed.
- Future provider contract is a Protocol only; no concrete provider and no network calls.

## Design decisions

1. Keep Feature 002 `Candle`, CSV loader, `run_replay`, next-bar timing and cost model unchanged.
2. Raw bytes are retained independently of normalized JSONL. Dataset identity includes raw hash, record type, source identity, symbol/interval and code/schema versions, but not a later re-import timestamp; repeat import returns the original manifest and never appends duplicate rows.
3. Logical duplicate keys are audit identities, not automatic deletion instructions. Candle key is `(symbol, interval_seconds, timestamp)`. Trade rows have no documented stable ID; the fallback content fingerprint can collide for distinct identical trades and therefore only raises a possible-duplicate finding.
4. Report `event_timestamp` only when present in source. For depth payloads without a source time, retain a distinct caller capture/ingest timestamp.
5. Replay eligibility requires an explicit expected interval, expected start/end, as-of and maximum age, known symbol set, and field precision limits; this conservative gate prevents unknown policies from becoming a clean backtest.
6. Generated REST documentation and WebSocket streams remain separate source representations. No host, auth, rate limit, pagination or currentness is chosen for runtime.

## Project structure

```text
src/wallex_research/
├── historical.py              # versioned canonical record models/parsers
├── dataset_store.py            # content-addressed raw, manifests, normalized JSONL
├── historical_quality.py       # audit policy, issues, deterministic reports
└── market_data_pipeline.py     # import/audit/replay-export CLI
scripts/market_data_pipeline.py       # import/audit/replay-export CLI
specs/003-historical-market-data/
tests/test_historical_data.py
tests/fixtures/                # synthetic JSON and CSV only
```

## Risks and limits

A complete Wallex OpenAPI byte archive is not currently available through the page reader; reader chunks are not raw-download evidence. Documentation can be internally inconsistent about hosts/auth and omitted time/pagination fields. The pipeline makes no online request and uses caller evidence only. Data completeness/source truth/licensing remain external responsibilities.
