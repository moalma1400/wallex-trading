# WebSocket research notes

## Versions and public feeds

- Wallex's new channel guides describe Centrifugo v2 at `wss://api.wallex.ir/connection/websocket`; v1 at `wss://api.wallex.ir/ws` is described as deprecated, but still working, with no end-of-support date stated. Use source terminology, not an assumption that v1 is already disabled. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [MOD-SOCKET-ALL-PRICE](https://developers.wallex.ir/docs/socket-all-price) · [SOCKET-MIGRATION](https://developers.wallex.ir/docs/socket-migration)
- Public examples include `public:<SYMBOL>@trade`, `public:all@price`, `public:all@fairPrice`, `orderbook:<SYMBOL>@buyDepth`, `orderbook:<SYMBOL>@sellDepth`, and `candle:<SYMBOL>@<INTERVAL>`. Exact channel spelling/case matters. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [MOD-SOCKET-FAIR-PRICE](https://developers.wallex.ir/docs/socket-fair-price)
- `all@price` updates are sent when a market price changes and do not provide an initial price or replay missed messages. `all@fairPrice` is documented as a periodic full snapshot (typically 20 seconds, sometimes around 35 seconds); absent market keys can be temporarily missing, and no channel history is kept. These are source statements, not tested service-level guarantees. [MOD-SOCKET-ALL-PRICE](https://developers.wallex.ir/docs/socket-all-price) · [MOD-SOCKET-FAIR-PRICE](https://developers.wallex.ir/docs/socket-fair-price)
- Trade publications contain `isBuyOrder`, `quantity`, `price`, and ISO timestamp examples; new trades only, without replay after disconnect. Depth publications are complete snapshots, not deltas, and subscription does not send an initial order book. [MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade) · [MOD-SOCKET-BUY-DEPTH](https://developers.wallex.ir/docs/socket-buy-depth) · [MOD-SOCKET-SELL-DEPTH](https://developers.wallex.ir/docs/socket-sell-depth)
- Candle channels document `1m`, `1h`, and `1d`; each update carries UDF-shaped OHLCV arrays, and an open candle may be published repeatedly with the same start-time `t`, requiring replacement rather than append. Up to 10 channel-history messages for two minutes are described for synchronization; this is not a substitute for historical UDF data. [MOD-SOCKET-CANDLE](https://developers.wallex.ir/docs/socket-candle)

## Page structure and the apparent v1/v2 conflict (re-read 2026-10-23T13:46:00Z)

Each official socket page documents **both** generations on one page, and `/docs/socket-trade` lists version 1
(deprecated) **first**, then v2 with the SDK, then v2 without it. `socket-intro` presents the v2 rules and then a
version-1 detail section (20 s ping / 30 s pong, 30-minute connection lifetime, 50 subscribes). A retrieval that stops
at the top of either page therefore shows only the legacy contract. The register re-fetched all four pages on
2026-10-23T13:46:00Z and read both chunks of `socket-trade` and `socket-raw-protocol`; the apparent conflict is a
page-structure/truncation artifact, not conflicting documentation. See `D-022`.
[MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade) · [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [D-022](../research/discrepancies.md)

## v2 raw protocol frames (re-read 2026-10-23)

Documented, not runtime-verified. Source: [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol) and [MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade).

- Endpoint: exactly `wss://api.wallex.ir/connection/websocket` (a trailing slash returns 404). JSON in text frames. Every command carries a unique numeric `id`; the answer uses the same `id`. Messages without `id` that carry `push` are channel data.
- Connect: `{"id": 1, "connect": {}}` → `{"id": 1, "connect": {"client": "<uuid>", "ping": 25, "pong": true}}`. Public channels need no token.
- Subscribe: `{"id": 2, "subscribe": {"channel": "public:<SYMBOL>@trade"}}` → `{"id": 2, "subscribe": {}}`. The acknowledgement is empty: no snapshot, no `offset`/`epoch`/`recoverable` fields.
- Publication: `{"push": {"channel": "public:<SYMBOL>@trade", "pub": {"data": {"isBuyOrder": true, "quantity": "...", "price": "...", "timestamp": "..."}}}}`. Channel data always arrives in `push.pub.data`; `push.channel` separates channels on one connection.
- Heartbeat: the server sends an empty object `{}` every 25 seconds and the client must echo `{}` within 8 seconds or the connection closes with code `3012`. This is an **application-level** frame; it is not a WebSocket-protocol ping.
- Errors are answered per `id` without closing the connection: `102` unknown channel (for example a wrong namespace), `103` permission denied (channel name without `:`), `105` already subscribed, `106` limit exceeded (64 channels per connection), `107` bad request, `108` not available, `109` token expired. Close codes `3005`/`3008`/`3012` may be retried; `3500`/`3501` are client-side faults.
- One transport frame may contain several newline-separated JSON messages. This is **documented and demonstrated** in the official Python sample (`# یک فریم ممکن است چند پیام داشته باشد` / `for line in raw.split("\n")`) and the Go sample (`strings.Split(string(raw), "\n")`), both re-read on 2026-10-23. Documented reconnects resend `connect` and then `subscribe`; no non-candle channel keeps history, so missed messages are lost.

### Version 1 (deprecated) framing caveat

The v1 page documents the logical subscription frame `["subscribe", {"channel": "MARKET@trade"}]` and the two-element
trade envelope `["MARKET@trade", {...}]`, while the socket overview states that the first message after connecting to
`wss://api.wallex.ir/ws` is a connection-information object with `sid`, `upgrades`, `pingInterval: 20000` and
`pingTimeout: 30000`. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade)

That object is Engine.IO/Socket.IO shaped, so the deprecated endpoint's transport is a Socket.IO session and a raw
text frame is not by itself a subscription packet. The official pages do not specify which Socket.IO framing a
non-SDK client must use. This is recorded as `D-019`; it is not resolved, and v1 is not used by this repository's
recorder.

## Private channels and raw-protocol notes

- The private page documents `balanceUpdated`, `orderSaved`, `orderRemoved`, and `tradeDetails`; v2 private membership is supplied through a token-bound `private:user#<userId>` channel. These payloads are private account information. No account, token, or private channel was used. [MOD-SOCKET-PRIVATE-CHANNEL](https://developers.wallex.ir/docs/socket-private-channel) · [SOCKET-TOKEN](https://developers.wallex.ir/docs/socket-token)
- Raw v2 protocol documentation describes `connect`/`subscribe`, empty success acknowledgments, server ping/pong behavior, up to 64 channels per connection, and error/close codes. It says data other than candle history cannot be recovered after disconnect; candle history is narrowly limited. [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol)
- The documentation URLs cited by the earlier recorder implementation, `https://developers.wallex.ir/socket/trade` and `https://developers.wallex.ir/socket`, returned the site's localized not-found body on 2026-10-23. No HTTP status was exposed, so no removal reason is inferred. [LEGACY-SOCKET-TRADE-PATH](https://developers.wallex.ir/socket/trade) · [LEGACY-SOCKET-PATH](https://developers.wallex.ir/socket)

## Boundary

The only component in this repository that opens a public WebSocket is the opt-in
[candle recorder](../agent/CANDLE-RECORDER.md) CLI; every other component, test and validator remains offline. The recorder
implements the documented v2 frames above, but no live transport connection has succeeded from this environment, so
application-level subscription success, live trade receipt and live candle finalization are `pending`, not verified.
Page review is source documentation only; ordering, runtime uptime, auth availability and actual data quality remain
unverified for both generations. Current source coverage and unresolved reliability questions are in the
[register](../research/source-register.yaml) and [open questions](../research/unresolved-questions.md).
