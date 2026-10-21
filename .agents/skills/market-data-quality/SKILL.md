---
name: market-data-quality
description: Audit caller-supplied local OHLCV data without network access, guessing, or repair.
compatibility: Uses the local Python standard-library research package and synthetic/user-provided files only.
metadata:
  owner: wallex-trading
  scope: offline-data-quality
---

# Offline market-data quality procedure

1. Establish dataset provenance, licensing, symbol, units, timestamp zone, sampling interval, adjustment/corporate-action treatment, and intended use from the data owner. Do not assume exchange provenance.
2. Use only local files and the strict schema. Parse numeric text as exact Decimal and timestamps with explicit timezone offsets; normalize aware timestamps to UTC.
3. Inspect OHLC invariants, nonpositive prices, negative volume, missing cells, repeated/non-increasing timestamps, mixed symbols, and gaps only when a caller supplies an expected interval.
4. Do not sort, deduplicate, interpolate, forward-fill, infer a timeframe, fabricate a candle, or turn absence of data into zero volume. Report stable issue codes and preserve the source file.
5. A structurally clean report does not establish source authenticity, completeness, venue compatibility, survivorship-bias treatment, or fitness for backtesting. Document those as separate limitations.
6. Run tests offline with synthetic fixtures. Never fetch live data or add an online connector to pass validation.

7. For Feature 003, explicitly record source ID/URL, retrieval method, retrieval UTC and ingestion UTC. Provide `captured_at_utc` for depth when the source does not expose an event time; never substitute either ingestion or capture time for exchange time.
8. Use `scripts/market_data_pipeline.py import-local` to preserve exact raw bytes and write versioned normalized JSONL; repeat imports should reuse the same content/config identity. Keep raw, reports and exports local and never delete/replace evidence to make a report pass.
9. Use `audit` with caller-supplied known symbols, interval, expected start/end, as-of/max age and per-field precision. Missing policy is unknown and blocks replay eligibility. Do not borrow synthetic fixture values as production policy.
10. Only export candle data to Feature 002 after an eligible audit. The output remains the existing seven-column schema; it is not exchange-connected paper trading. Inspect the sidecar, hashes and warnings, and retain the audit report with any result.
11. For undocumented source semantics (trade IDs, pagination, timestamp boundaries, retention, depth atomicity or numeric units), preserve the supplied representation and record unknowns. Official docs and fixtures are not runtime access/permission evidence.

## Challenge market-eligibility boundary

- The Feature 004 disabled-pair JSON is derived from its raw user-provided list; it is not an active-market registry. The absence of a pair from it must never be treated as permission or proof of orderability.
- Require current, trusted, noncontradictory source evidence and explicit freshness/orderability/Spot states before any internal eligibility result. Missing thresholds or source provenance block. Synthetic metadata passes only in explicit test-only mode.
