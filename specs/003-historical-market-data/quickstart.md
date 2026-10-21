# Quickstart — Historical Market Data (local fixtures only)

This feature currently supports local import only. It does not download Wallex history. Synthetic fixtures are clearly marked and are not Wallex market data.

```bash
python3 scripts/market_data_pipeline.py import-local \
  --file tests/fixtures/synthetic_ohlcv.csv \
  --root .local-market-data \
  --record-type candles \
  --source-id SYNTHETIC-FIXTURE \
  --source-url https://example.invalid/synthetic_ohlcv.csv \
  --retrieval-method local_synthetic_fixture \
  --retrieved-at-utc 2026-01-01T00:03:00Z \
  --ingested-at-utc 2026-01-01T00:03:01Z \
  --symbol SYNTHETIC_XYZ \
  --interval-seconds 60
```

Both source retrieval and local ingestion timestamps are explicit; provide fixed values for reproducible imports. The original file is stored by SHA-256 under `raw/sha256/`; normalized JSONL and a manifest are placed under a content-derived dataset ID. Repeating the same import identity returns the existing dataset; source rows are not silently sorted/dropped/deduplicated.

Audit with the exact validation policy that applies to this synthetic example:

```bash
python3 scripts/market_data_pipeline.py audit \
  --root .local-market-data \
  --dataset-id DATASET_ID \
  --known-symbol SYNTHETIC_XYZ \
  --expected-interval-seconds 60 \
  --expected-start 2026-01-01T00:00:00Z \
  --expected-end 2026-01-01T00:02:00Z \
  --as-of 2026-01-01T00:03:00Z \
  --max-age-seconds 120 \
  --max-decimal-places price=4 \
  --max-decimal-places quantity=4 \
  --replay-export .local-market-data/exports/bars.csv
```

The example also attempts a gated Feature 002 replay export. Audit emits a JSON summary, CSV issue list and Markdown report; local outputs under `.local-market-data/` are git-ignored. Replay export is blocked unless the explicit policy is complete and the audit passes. See implementation CLI help for exact file paths. Do not reuse example timestamps or policy values as recommendations.
