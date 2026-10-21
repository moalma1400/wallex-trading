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
