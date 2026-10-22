# Data Model — Historical Market Data

Schema version `1.0` is a local canonical format, not a Wallex API schema. Raw input bytes remain separately stored. Monetary/quantity values serialize as decimal text. All datetimes are timezone-aware UTC internally; `event_timestamp` is optional only where the source provides none, while `captured_at_utc`/`ingested_at_utc` are explicitly different concepts.

## Shared provenance

`Provenance` records `source_id`, exact `source_url` or explicitly synthetic URL, `retrieval_method`, `retrieved_at_utc`, raw file SHA-256, and schema/code version. These are caller assertions, not remotely verified facts. Each dataset manifest separately stores immutable raw filename/hash, normalized filename/hash, record count, source/time range when known, symbol/interval, and dataset identity.

## Versioned records

- `MarketMetadataRecord`: `symbol`, `base_asset`, `quote_asset`; optional source-present `is_spot`, `is_otc`, `is_margin`, `price_precision`, and `amount_precision`. `precision` labels are copied, not interpreted as exchange tick sizes. Volatile price/stats remain in raw source, not static metadata.
- `CandleRecord`: `symbol`, `interval_seconds`, start `timestamp_utc`, `open/high/low/close/volume: Decimal`, provenance. Positive OHLC, nonnegative volume and OHLC consistency are required. `to_replay_candle()` produces Feature 002's unchanged `Candle`.
- `PublicTradeRecord`: `symbol`, event timestamp, positive Decimal `price` and `quantity`, optional source-present `isBuyOrder` and `sum`. There is no invented exchange trade ID; identical values can represent separate trades.
- `FairPriceSnapshotRecord`: event `ts` and non-empty `prices: {symbol: Decimal}` from the documented `public:all@fairPrice` full-snapshot form. Missing symbols remain absent, not zero. It is not a last-trade ticker.
- `OrderBookSnapshotRecord`: caller capture time plus `bids`/`asks` of Decimal price/quantity; used for a single REST response whose fields are documented. `OrderBookSideSnapshotRecord` retains one WebSocket side and capture time; source docs describe each message as a full side snapshot, not delta. No cross-channel atomicity/sequence is assumed.

## Import identity and dedupe

The dataset ID is SHA-256 over canonical identity metadata including raw SHA-256, record type/input format, source ID/URL, retrieval method, symbol, interval, explicit depth capture time when applicable, code version and schema version. Retrieval timestamp is retained in the first manifest but excluded from identity so re-importing identical bytes does not create another dataset. Raw and normalized record duplicates remain preserved.

Audit logical keys:

- Candle: `(symbol, interval_seconds, timestamp_utc)`; same-key divergent OHLCV is a conflict; exact duplicate is still reported.
- Market metadata: `symbol` within one captured dataset; differing values are a conflict, not a silent update.
- Trade: source `trade_id` if a future documented schema supplies one; current fallback hashes `(symbol, timestamp, price, quantity, isBuyOrder, sum)`. This may collide for genuinely distinct same-valued trades and is only a warning key.
- Fair-price snapshot: event timestamp; depth snapshot/side: `(symbol, capture timestamp, side)`. These keys do not imply exchange-side uniqueness.

## Audit policy/report

`AuditPolicy` explicitly supplies expected interval/range, as-of UTC and max age, known symbols, and maximum decimal places by field. Without a policy the report still lists findings but marks the corresponding condition unknown and `replay_eligible=false`. Reports include errors/warnings, raw/normalized hashes, source and retrieval method, retrieval/ingestion/capture times, range, record count, config, schema/code version and suitability. Outputs are deterministic JSON, CSV issue rows and Markdown. No price interpolation or record sorting/removal is permitted.
