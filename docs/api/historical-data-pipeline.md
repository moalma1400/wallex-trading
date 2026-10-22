# Local historical-market-data pipeline

Feature 003 adds an offline import, audit, and gated export path. It accepts caller-supplied local CSV/JSON only; its provider seam is a typing `Protocol`, not a network implementation. It performs no HTTP, WebSocket, credential, account, order, transfer, or withdrawal operation. See [Feature 003 specification](../../specs/003-historical-market-data/spec.md), [local dataset contract](../../specs/003-historical-market-data/contracts/local-dataset.md), and [quickstart](../../specs/003-historical-market-data/quickstart.md).

## Data lifecycle

1. Caller provides source ID/URL, retrieval method, explicit timezone-aware retrieval and ingestion timestamps, plus symbol/interval or a distinct depth capture time where needed.
2. Original bytes are retained unchanged under a SHA-256 content path. JSON floats are parsed as `Decimal`; naive times, duplicate JSON keys, invalid values and unsupported shapes fail closed.
3. Strict versioned records are stored separately as deterministic JSONL with provenance. Reimport identity is content/config based and excludes re-import time; source rows are not sorted, deleted, deduplicated, or interpolated.
4. `audit` evaluates the retained dataset against caller-supplied expectations for symbol set, interval, start/end, as-of/max age, and precision. Missing policies are reported as unknown. JSON, issue CSV, and Markdown reports carry dataset/source/config/time and byte fingerprints.
5. Feature 002 CSV export is candle-only and refuses to proceed unless replay eligibility passes. Output is the unchanged seven-column candle schema and includes a sidecar. Existing different output files are never overwritten.

## Canonical coverage and known limitations

Records cover candle OHLCV, market metadata, public trades, fair-price snapshots, REST order-book snapshots, and one-sided WebSocket-style depth snapshots. Fair-price is not last-trade ticker data; an incremental all-price stream is not normalized to a complete snapshot. Missing exchange event timestamps remain missing; depth capture and local ingestion timestamps are distinct. The public trade documentation reviewed here does not establish a stable trade identifier; content-based duplicate keys can collide.

Official docs describe basic and generated REST interfaces differently in host, required fields, security annotations, and some numeric types. Candle resolution lists also differ; polling warnings are qualitative only; no numeric limit, pagination rule, completeness window, boundary rule, or runtime availability is assumed. Exact URLs and unknowns are in [research](../../specs/003-historical-market-data/research.md), the [source register](../research/source-register.yaml), and [discrepancies](../research/discrepancies.md). No API request or live stream was made. OpenAPI reader chunks are transformed, not archived bytes; no checksum is claimed.

A clean audit establishes conformance only to the selected explicit local policy. It does not establish source authenticity, venue permission, data completeness beyond declared bounds, strategy quality, profitability, or live-trading safety.
