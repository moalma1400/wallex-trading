# Feature 003 acceptance checklist

## Local data contracts and storage
- [x] Versioned records use `Decimal`, timezone-aware UTC, source/retrieval/ingestion provenance and raw SHA-256.
- [x] Explicit capture time for depth is separate from event and ingestion time.
- [x] Local CSV candle and documented JSON shape imports are strict; duplicate JSON keys, naive timestamps and malformed records fail closed.
- [x] Raw bytes are retained separately from deterministic normalized JSONL and manifests; identity is content/config based and reimport is idempotent.
- [x] No row is silently sorted/deduplicated, no gap is interpolated, and no remote/provider implementation exists.
- [x] Market metadata, public trade, fair-price, book snapshot and one-sided depth examples are synthetic-only and preserve decimal strings.
- [x] Future read-only provider is a protocol only.

## Quality and replay boundaries
- [x] Audit checks structural validity, duplicates/conflicts, order/gaps, symbol/interval/range/freshness/precision policy, and raw/normalized integrity.
- [x] Reports include reproducibility metadata/fingerprints in JSON, issue CSV and Markdown.
- [x] Missing replay policies remain unknown and prevent replay-eligible status; invalid/incomplete data cannot pass silently.
- [x] Replay export is candle-only, gated, uses the unchanged Feature 002 seven-column CSV schema, and rejects conflicting existing outputs.
- [x] Feature 002 replay timing/cost implementation is unchanged and compatibility is tested.

## Evidence and validation
- [x] Official source URLs/status and material discrepancies are recorded; no endpoint, socket, key, account, or private data was accessed.
- [x] The basic-services and Spot Swagger assets' available reader chunks were reviewed for market-data relevance; the reader output is transformed, not byte-exact. No source bytes/checksums are fabricated.
- [ ] Remaining Margin, OTC and Trade Credit artifact chunks and true byte-level archives/checksums remain incomplete; these are not required for this Spot-only local implementation.
- [x] Final repository test suite, offline source/link validators, compilation, whitespace and heuristic secret review: see [validation record](../research.md#validation-record).
- [ ] Commit/push only to the fixed session branch; PR #1 stays open and unmerged.

## Limitations

No current runtime availability, authentication, entitlement, numerical rate limit, pagination, complete historical retention, Wallex-data provenance, fee value, symbol suitability, strategy performance, profitability, or live-trading safety is asserted.
