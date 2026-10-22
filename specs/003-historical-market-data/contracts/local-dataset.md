# Local Dataset Contract

## Supported input formats

- Candle CSV: exact header `symbol,timestamp,open,high,low,close,volume`; decimals are text; timestamps require explicit UTC offset. Symbol and interval seconds are mandatory import context because neither column necessarily establishes interval.
- Candle JSON: UDF history payload with aligned `t/o/h/l/c/v` arrays, or an array of canonical candle records. UDF timestamps are Unix seconds; symbol and interval remain mandatory caller context.
- Other JSON records: documented market metadata (`result.markets`), public trades (`result.latestTrades`), fair-price snapshots (`ts`, `prices`), REST depth (`result.ask`, `result.bid`), or one-sided documented WebSocket depth publications. The importer does not fetch any of these.
- JSON float tokens are parsed as `Decimal`. Duplicate JSON object keys, non-finite decimals, extra/missing required fields, and invalid record type fail closed. Unknown raw fields remain in the immutable source file.

## Storage

Raw source bytes are preserved exactly under `raw/sha256/<hash>` (the original filename and extension remain in the manifest). Each content-derived dataset directory contains deterministic `records.jsonl` and `manifest.json`. Existing files are verified against their hashes; conflicting content fails rather than overwriting raw or normalized data. The normalized export uses schema version `1.0`; hashes use SHA-256 over exact bytes.

## Replay compatibility

Only candle datasets may be replay-exported. The export uses exactly Feature 002's seven CSV columns and keeps a sidecar manifest with the source dataset ID and audit report ID. The audit policy must supply expected symbol registry, interval, expected start/end timestamps, as-of time, max age and max decimal scales. This proves only conformance to caller policies, not Wallex authenticity, completeness beyond declared bounds, or suitability/profitability.
