# Research — Historical Market Data and Data Quality

**Research date**: 2026-10-21
**Status**: Public documentation re-reviewed; no endpoint or socket used.

## Relevant official evidence

- Basic market page documents `/hector/web/v1/markets` with `symbol`, `base_asset`, `quote_asset`, product flags, `amount_precision`, `price_precision`, current price and 24h/7d fields. It does not explain precision semantics or guarantee current market state. The generated markets page shows `https://api.wallex.com/hector/web/v1/markets` and an `x-api-key` scheme, while introductory docs say `.ir`; no use is selected. [MARKETS](https://developers.wallex.ir/docs/basic-services-markets) · [MOD-GENERATED-GET-MARKETS](https://developers.wallex.ir/docs/generated/get-markets) · [MOD-INTRO](https://developers.wallex.ir/docs)
- Basic candle guide documents `GET /v1/udf/history`, optional `symbol/resolution/from/to`, Unix seconds and UDF arrays. Generated candle-history marks all four required, gives a different resolution example set and `.com` host, with `x-api-key` text. No endpoint-specific pagination/maximum lookback, inclusivity, timezone bucket alignment or actual requiredness is established. [CANDLES](https://developers.wallex.ir/docs/basic-services-candles) · [MOD-GENERATED-CANDLE-HISTORY](https://developers.wallex.ir/docs/generated/candle-history) · [D-015](../../docs/research/discrepancies.md)
- Basic latest-trades prose warns frequent REST polling can encounter rate limits; it describes `symbol` as optional, while generated GET-latest-trades marks it required and documents `quantity`, `price`, `sum`, `isBuyOrder`, ISO `timestamp` and `x-api-key`. No numerical rate limit, pagination, trade ID or retention window is confirmed. [TRADES](https://developers.wallex.ir/docs/basic-services-latest-trades) · [MOD-GENERATED-GET-LATEST-TRADES](https://developers.wallex.ir/docs/generated/get-latest-trades)
- Basic depth prose similarly warns frequent REST depth requests may encounter rate limits but gives no numeric ceiling. It documents `ask`/`bid` arrays with `price`, `quantity`, `sum`; generated depth requires `symbol` and shows numeric `price`/`quantity` plus string `sum`, `.com` host and `x-api-key`. All-markets depth has another path without `/v2`; legacy lists `/v2/depth/all`. [DEPTH](https://developers.wallex.ir/docs/basic-services-depth) · [MOD-GENERATED-GET-MARKET-DEPTH](https://developers.wallex.ir/docs/generated/get-market-depth) · [MOD-GENERATED-GET-DEPTH](https://developers.wallex.ir/docs/generated/get-depth) · [LEGACY-API](https://api-docs.wallex.ir/) · [D-013](../../docs/research/discrepancies.md)
- `public:all@price` is an incremental change feed with no initial snapshot, no replay and no source event timestamp. `public:all@fairPrice` is a periodic full snapshot with `ts` and `prices`; absent market keys can be temporarily omitted. It is a fair-price series, not last trade. [MOD-SOCKET-ALL-PRICE](https://developers.wallex.ir/docs/socket-all-price) · [MOD-SOCKET-FAIR-PRICE](https://developers.wallex.ir/docs/socket-fair-price)
- Public WebSocket trades describe new trades with string decimal `quantity`/`price`, `isBuyOrder`, ISO timestamp; no history is retained and reconnect does not replay. The flag is preserved verbatim; the canonical model does not reinterpret it as aggressor side. [MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade)
- WebSocket buy/sell depth pages say each publication is a complete side snapshot rather than a delta, no initial state is sent on subscription, and no history/reconnect recovery is available. Price/quantity/sum appear as JSON numbers. Do not combine side channels into an atomic two-sided book absent same-capture proof. [MOD-SOCKET-BUY-DEPTH](https://developers.wallex.ir/docs/socket-buy-depth) · [MOD-SOCKET-SELL-DEPTH](https://developers.wallex.ir/docs/socket-sell-depth)
- Candle WebSocket updates repeat the same candle start-time `t` as the bar develops, replace/upsert by timestamp, and document 1m/1h/1d examples, limited 10-message/two-minute history and API history resync after reconnect. No live feed is implemented. [MOD-SOCKET-CANDLE](https://developers.wallex.ir/docs/socket-candle)

## Specification artifact investigation

The official page reader returned chunked, transformed excerpts for the five linked JSON/YAML Swagger/OpenAPI assets. Basic-services and Spot market-data portions were revisited, including schemas for markets/trades/depth/UDF; those returned extracts are not the original downloaded bytes. The tool does not expose a byte-preserving download or checksum operation, and outbound shell access does not include the Wallex docs host. No fake raw archive or checksum is created. Keep all five source-register assets `in_progress` until exact bytes can be retrieved and hashed. The remaining Margin/OTC/trade-credit portions are outside this Feature's historical Spot pipeline and stay unimplemented.

## Local design decisions

- Local file source only; caller supplies source identity, retrieval method/time, symbol, interval and audit policy. We do not infer exchange provenance from the filename.
- CSV OHLCV and JSON fixtures are normalized into a versioned canonical schema. Raw bytes are immutable, content-addressed and hashed; normalized output is a separate deterministic derivative.
- Reimport identity is content/config based and excludes later ingestion time to avoid duplicate dataset rows. Individual source duplicate records are retained and flagged.
- Replay readiness is stricter than structural validity: policy must explicitly bind expected symbol(s), interval, expected range, as-of freshness ceiling and max decimal scales. No bounds means unknown, not clean.
- Existing Feature 002 replay implementation, next-bar open timing, explicit cost inputs and seven-column candle CSV loader remain unchanged.
- A future read-only provider interface is a Protocol only. No client, endpoint URL, request scheduler or websocket is supplied.

## Validation record — 2026-10-21

All commands below are offline/local; no Wallex endpoint, WebSocket, account, credential, or remote fixture was accessed.

- Baseline at existing commit `357c0b51ab7bbdc0f6ef7525aafe38bfe9914edd` was extracted with `git archive` into a temporary directory and tested with `PYTHONPATH=<temporary>/src python3 -m unittest discover -s <temporary>/tests -v`: **PASS, 16 existing tests**. This preserves an untouched baseline without switching branches.
- `PYTHONPATH=src python3 -m unittest discover -s tests -v`: **PASS, 28 tests** (the 16 existing tests plus 12 Feature 003 pipeline tests).
- `python3 scripts/validate_sources.py`: **PASS**, 132 records, 132 unique source IDs and URLs; `reviewed=70`, `not_started=51`, `in_progress=5`, `blocked=6`.
- `python3 scripts/validate_doc_links.py`: **PASS**, 106 local relative Markdown links and 245 source citations resolve; external links were not network-tested.
- `python3 -m py_compile scripts/validate_sources.py scripts/validate_doc_links.py scripts/check_market_data.py scripts/market_data_pipeline.py src/wallex_research/*.py tests/test_*.py`: **PASS**.
- `python3 scripts/check_market_data.py tests/fixtures/synthetic_ohlcv.csv --interval-seconds 60`: **PASS**, 3 synthetic rows are structurally valid only; provenance/completeness/exchange compatibility are not established.
- Manual CLI smoke: local `import-local`, explicit-policy `audit`, JSON report output, and successful gated seven-column replay CSV export: **PASS**. Temporary data was removed after the run.
- Secret-pattern scan for common GitHub tokens, AWS access-key IDs, and private-key headers: **no matches** (heuristic, not proof of secret absence).

`git diff --cached --check`: **PASS**. The staged diff was reviewed for scope and credential-like content; the heuristic secret-pattern scan reported no matches. The five official API-spec artifacts remain `in_progress`; transformed reader chunks do not establish byte-exact provenance or checksums.
