# Order book, trades, candles, history

- New `GET /v1/depth` returns `result.ask` and `result.bid` with `price`, `quantity`, and `sum`; documentation cautions against frequent REST depth requests due to possible rate limits. [DEPTH](https://developers.wallex.ir/docs/basic-services-depth)
- New `GET /v1/udf/history` documents `symbol`, `resolution`, `from`, `to`; its displayed parameter table marks them Optional and lists `1, 15, 60, 240, 480, 720, 1D, 2D, 3D`. Response arrays are `t`, `c`, `o`, `h`, `l`, `v`. The legacy guide instead describes `symbol`, `resolution`, `from`, `to` as required; record this difference and do not infer actual server validation. [CANDLES](https://developers.wallex.ir/docs/basic-services-candles) · [LEGACY-API](https://api-docs.wallex.ir/)
- Legacy endpoint `GET /v1/trades` uses required `symbol`; the legacy API navigation also lists `GET /v1/depth`, `GET /v2/depth/all`, and `GET /v1/udf/history`. These routes have not been matched against new documentation beyond the page above. [LEGACY-API](https://api-docs.wallex.ir/)
- New WebSocket channels are described in the intro; snapshot/history limitations are documented in more detail there. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro)

Rate limits, pagination, timestamp boundaries, maximum history windows, candle timezone alignment, and replay guarantees are not fully established in this first pass.
