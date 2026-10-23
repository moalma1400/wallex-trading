# Public Trade Candle Recorder (data collection only)

Wallex's official Socket Trade documentation describes the public WebSocket at `wss://api.wallex.ir/ws` and subscription message `["subscribe", {"channel":"MARKET@trade"}]`. See [official trade channel documentation](https://developers.wallex.ir/socket/trade) and [socket overview](https://developers.wallex.ir/socket).

This tool builds a **forward-collected local dataset** from incoming public trades. It is not a historical-download endpoint and cannot reconstruct trades from before collection starts. No API key is needed. It never reads account data and never submits, modifies, or cancels orders.

## Install and run

```sh
python -m pip install -e ".[test]"
wallex-candle-recorder --symbol BTCUSDT --interval-seconds 60 --output data/BTCUSDT-60s.jsonl
```

Replace `BTCUSDT` with an exact active Spot symbol verified against the official markets list. The command runs until interrupted. For a bounded capture use `--max-runtime-seconds 3600`. Intervals are 1–86400 seconds. The recorder writes a candle only after receiving a trade from a later time bucket, so it does not present an unfinished candle as complete. The last in-progress candle is intentionally discarded at stop.

Each JSONL candle includes `timestamp` (UTC bucket start), `open`, `high`, `low`, `close`, `volume`, `symbol`, `interval_seconds`, `trade_count`, and source fields. The timestamp/OHLCV schema is accepted by `wallex-backtest`. A companion `.manifest.json` records the symbol, interval, source documentation, run times, closed candle count and potential gaps. Keep the manifest with the dataset.

## Data quality caveats

- Collection is prospective, not historical. Leave it running long enough for meaningful analysis.
- WebSocket disconnects and process downtime create gaps; the manifest explicitly warns about them. Do not treat the dataset as continuous without checking timestamps.
- OHLCV is derived from trades received by this client; late/out-of-order events are not inserted into already-closed candles.
- This first version is a single-session collector. If it disconnects or exits, restart it and inspect the manifest/gaps; automatic reconnect and gap repair are not implemented.
- Trade volume is the sum of trade quantities in base-asset units, not quote notional.
- It does not include order-book depth, executable bid/ask spread, fee tier, or slippage observations.
- Do not treat a backtest on a short, gappy dataset as evidence of profitability.
