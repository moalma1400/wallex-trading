# Public Trade Candle Recorder (data collection only)

`wallex-candle-recorder` subscribes to **new** public trades for one Wallex market and builds local OHLCV candles. It
is a forward-collection tool: it cannot reconstruct trades from before it started, it needs no API key, it never reads
account data and it never submits, modifies or cancels orders.

## Protocol (what is implemented, and why)

The recorder implements the **v2 Centrifugo public raw protocol** at:

```text
wss://api.wallex.ir/connection/websocket
```

Evidence: [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol) ·
[MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade) ·
[SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) ·
[SOCKET-MIGRATION](https://developers.wallex.ir/docs/socket-migration) (`documented`, re-read 2026-10-23).

| Step | Frame | Meaning |
| --- | --- | --- |
| connect | client → `{"id": 1, "connect": {}}` | first command after the socket opens; no token is needed for public channels |
| connect ack | server → `{"id": 1, "connect": {"client": "<uuid>", "ping": 25, "pong": true}}` | `ping` is the server heartbeat interval in seconds |
| subscribe | client → `{"id": 2, "subscribe": {"channel": "public:<SYMBOL>@trade"}}` | one command per channel |
| subscribe ack | server → `{"id": 2, "subscribe": {}}` | empty object: membership only, never a snapshot or a trade |
| trade | server → `{"push": {"channel": "public:<SYMBOL>@trade", "pub": {"data": {...}}}}` | `data` carries `isBuyOrder`, `quantity`, `price`, `timestamp` |
| heartbeat | server → `{}`; client → `{}` | the client must echo the empty object; 8 s without an answer closes with code `3012` |
| error | server → `{"id": 2, "error": {"code": 102, "message": "unknown channel"}}` | answered with the same `id`, the connection stays open |

Additional documented rules the implementation follows:

- The endpoint path must be exactly `/connection/websocket`; a trailing slash returns 404.
- One transport frame **may contain several newline-separated JSON messages**, so every frame is split before
  classification.
- Messages without an `id` that carry `push` are channel data; commands and acks carry an `id`.
- Documented request errors: `102` unknown channel, `103` permission denied, `105` already subscribed, `106` limit
  exceeded (64 channels), `107` bad request, `108` not available, `109` token expired.
- Documented close codes: `3005`, `3008`, `3012` may be retried; `3500`/`3501` are client-side faults and are **not**
  retried by this recorder.
- Trade channels keep no history and have no `offset`/sequence number: a missed trade cannot be recovered and
  duplicates cannot be detected from the wire.

### Which page says what (retrieval conflict, resolved as page structure)

The four socket pages do not contradict each other: **each page documents both generations**, and
`/docs/socket-trade` lists **version 1 (deprecated) first**, then v2 with the SDK, then v2 without it. `socket-intro`
likewise presents the v2 rules and then a `version 1 (deprecated) details` section with the 20 s/30 s heartbeat.
A retrieval that reads only the top of the page therefore sees exactly the legacy contract — which is what an
independent retrieval path reported on 2026-10-23. This register re-fetched all four pages on
`2026-10-23T13:46:00Z`, including the final chunk of `/docs/socket-trade` that earlier passes had not read, and recorded
the ordering. See `D-022` in the [discrepancy register](../research/discrepancies.md).

### Why not version 1

The previous implementation connected to `wss://api.wallex.ir/ws` (the deprecated v1 endpoint) and wrote the *logical*
v1 frame `["subscribe", {"channel": "BTCUSDT@trade"}]` as a bare text frame. The official overview documents that this
endpoint first sends an Engine.IO-style connection-information object (`sid`, `upgrades`, `pingInterval: 20000`,
`pingTimeout: 30000`) [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro), which matches the operator-collected runtime
evidence from 2026-10-23 (the `/ws` handshake in Test B). A raw text frame is not documented as a Socket.IO subscription
packet for that transport, and no trade arrived.

**This is a strong hypothesis, not an established root cause.** It explains every observation (one handshake message,
zero trades), but nothing observed proves the server ignored the frame for that reason, and a market that simply had no
trades during the window cannot be excluded from the old manifest. Only a live session can settle it.

v1 is described as deprecated and still working, but the official pages do not specify the Socket.IO packet framing a
raw client would need to use it, and the recorder would then depend on an extra client library. Version 2 is the
documented recommendation for new implementations, is plain JSON, and needs only the `websockets` dependency that the
project already declares. The recorder therefore uses v2 only and fails closed if it ever receives a v1 frame.

## Candle construction contract

- A candle bucket starts at `floor(trade_timestamp_epoch / interval_seconds) * interval_seconds` in UTC; stored
  `timestamp` values are UTC ISO-8601 with `Z`.
- `open` is the first trade price in the bucket, `high`/`low` are the extrema, `close` is the last trade price, and
  `volume` is the sum of base-asset trade `quantity` values (not quote notional).
- `trade_count` counts trades aggregated into that candle.
- **A candle is written only when a trade from a later bucket arrives.** The newest, still-open candle is never written.
- The in-progress candle is discarded at shutdown and on every disconnect; the manifest counts it in
  `discarded_partial_candles`.
- The candle JSONL file is created only when the first candle is finalized. A run that never finalizes a candle leaves
  no JSONL file behind, by design.
- No synthetic candle is created for a bucket without trades, and no candle is backfilled after a reconnect.
- `open` and `close` follow **event order** (the order this client received the trades), because the documented trade
  channel carries no `offset`/sequence number. If the venue ever delivered a reordered event inside one bucket, only
  `open`/`close` of that single bucket could be affected; `high`, `low` and `volume` are order-independent.
- **Appending to an existing recording is safe.** On start the recorder reads the last finalized candle already in the
  output file and treats that bucket as a floor: a later trade for that bucket (or any earlier one) is counted in
  `late_or_out_of_order_trades_ignored` instead of re-writing a candle. This prevents the duplicate timestamps that
  `wallex-backtest` and `wallex-data-audit` reject. A recording whose last line cannot be parsed is **not** appended to;
  the run fails with an explicit error so the operator can repair or move the file.
- A trade that belongs to an already-closed bucket is counted in `late_or_out_of_order_trades_ignored` and never
  rewrites a written candle. Trades are not deduplicated because the documented trade channel has no trade identifier
  or offset.
- Prices and quantities are parsed as `Decimal` from the documented decimal strings.
- Calendar/timezone-independent alignment is used; a timestamp expressed in any offset is normalized to UTC before
  bucketing.

Each candle line contains: `timestamp`, `open`, `high`, `low`, `close`, `volume`, `symbol`, `interval_seconds`,
`trade_count`, `source`, `source_url`. This schema is accepted by `wallex-backtest`, `wallex-data-audit` and
`wallex-paper-candles`.

## Manifest (schema 2)

The sibling file `<output>.manifest.json` is rewritten on start, on every status change, on every finalized candle and
at most every 2 seconds for counter-only updates. On a clean exit or a handled failure it ends in
`status: "failed"` or `"stopped"` with a `stop_reason`; a hard-killed process can leave the last periodic snapshot
in place.

| Field | Meaning |
| --- | --- |
| `schema_version` | `2` (schema 1 described the previous v1 attempt) |
| `protocol`, `websocket_url`, `channel` | `wallex-centrifugo-v2-raw`, the exact endpoint and `public:<SYMBOL>@trade` |
| `documentation_url`, `socket_documentation_url`, `raw_protocol_documentation_url` | the three official pages this implementation follows |
| `status` | `starting`, `connecting`, `handshaking`, `subscribed`, `reconnecting`, `failed`, `stopped` |
| `stop_reason` | `runtime_limit` and `cancelled` (Ctrl+C, status `stopped`), `interrupted`, or a failure: `reconnect_limit`, `subscription_rejected`, `protocol_error`, `fatal_close_code`, `error` |
| `subscription_status` | `not_attempted`, `pending`, `acknowledged`, `rejected` — **application-level** state, separate from the transport |
| `connection_count`, `reconnect_count` | sockets that opened successfully, and how many of those were reconnects |
| `connection_errors` | failed connection attempts or mid-stream failures |
| `gaps_possible_on_disconnect` | `true` when a failure, reconnect or fatal close may have dropped trades |
| `resumed_from_existing_output`, `previous_last_closed_candle_utc` | whether this run appended to an existing recording, and the bucket floor read from it |
| `closed_candles_written_this_run`, `last_closed_candle_utc` | finalized candle count and its bucket start |
| `transport_frames_received`, `messages_received` | WebSocket frames received, and JSON messages after splitting a frame on newlines |
| `trade_events_received`, `last_trade_at_utc` | valid trades accepted from the subscribed channel |
| `malformed_or_unmatched_messages` | **structural** failures only: non-JSON, non-text, invalid envelope, invalid price/quantity/timestamp |
| `late_or_out_of_order_trades_ignored` | trades for an already-closed bucket |
| `other_channel_publications_ignored` | publications for a different channel (never turned into candles) |
| `handshake_frames_received`, `subscription_ack_frames_received` | documented handshake and subscription acknowledgements |
| `server_ping_frames_received`, `server_pongs_sent` | documented `{}` heartbeats and the echoes sent back |
| `server_error_frames_received`, `last_server_error`, `last_subscription_error_code`, `last_subscription_error_message` | documented error frames, without credentials |
| `unknown_frames_ignored`, `legacy_v1_frames_ignored` | valid-but-unrecognized frames and deprecated v1 frames; **not** counted as malformed |
| `server_ping_interval_seconds` | the `ping` value reported by the connect acknowledgement (documented as 25) |
| `last_connection_error_type`, `last_connection_error_message`, `fatal_close_code` | most recent failure, truncated to 200 characters, no secrets |
| `discarded_partial_candles` | unfinished candles dropped at a disconnect or at shutdown (one per restart) |
| `subscription_acknowledged` | `true` once at least one **id-validated** subscribe acknowledgement arrived in this run; survives a later reconnect, while `subscription_status` describes only the current connection |
| `live_trade_received` | convenience boolean: at least one valid trade event was accepted |
| `started_at_utc`, `updated_at_utc`, `last_message_at_utc` | UTC timestamps |

A successful TCP/TLS/WebSocket handshake alone never produces `status: "subscribed"`: that status requires the
documented `{"id": 2, "subscribe": {}}` acknowledgement.

## Run it safely

```sh
python -m pip install -e ".[test]"
wallex-candle-recorder --symbol BTCTMN --interval-seconds 60 \
  --output data/recordings/BTCTMN-60s.jsonl --max-runtime-seconds 3600
```

- `--symbol` must be an exact, uppercase Wallex market name (`A-Z`, `0-9`, `_`, `-`; for example `BTCTMN` or
  `USDTTMN`). Confirm the symbol against the official markets list first; the recorder surfaces the server's
  `error 102 unknown channel` instead of silently recording nothing.
- `--interval-seconds` is 1–86400 (default 60). `--output` defaults to `data/candles.jsonl`. An existing file is
  appended to with the bucket floor described above; the manifest is replaced atomically so a concurrent reader never
  sees a half-written status.
- `--max-runtime-seconds` defaults to `0` (run until interrupted). For a bounded capture, allow **at least two
  intervals plus margin**: a candle is only finalized when the next interval produces a trade, so a 60-second capture
  with `--interval-seconds 60` can legitimately write nothing.
- `--reconnect-backoff-seconds` (default 1, exponential up to 64 s) and `--max-reconnect-attempts` (default 10) bound
  recovery. Documented fatal close codes (`>= 3500`) and a rejected subscription stop the run immediately.
- The documented heartbeat is the empty object `{}`, answered within 8 s. The client does not send WebSocket-protocol
  pings (no official page states that the v2 server answers them); instead, if **no** frame arrives for 60 s the
  connection is treated as dead and reconnected (`inferred` implementation choice, not a documented requirement).
  Acknowledgement timeouts are 15 s.
- `Ctrl+C` discards the in-progress candle, finalizes the manifest and exits with status 130.

Recordings are local diagnostic data and are not committed. Git ignores `data/recordings/`, `data/*.jsonl` and
`data/*.jsonl.manifest.json`; other `data/` content (for example fixtures or reports) stays trackable, and the
whole `data/` tree is **not** ignored.

## Deterministic tests

```sh
python -m pytest tests/test_candle_recorder.py -q
```

The suite is offline: it drives a scripted fake WebSocket and uses the exact frames quoted from the official pages.
It covers handshake/ack/heartbeat/error/unknown/legacy classification, multi-message frames, malformed payloads, wrong
symbol isolation, OHLCV aggregation and bucket alignment, finalization and partial-candle handling, late and duplicate
trades, reconnect bounds, fatal close codes, subscription rejection, manifest finalization, downstream audit
compatibility and CLI validation. **No deterministic test proves live behaviour.**

## Live verification status

`pending` — as of 2026-10-23 no live WebSocket **transport connection** to
`wss://api.wallex.ir/connection/websocket` has succeeded from this repository environment.

| Level | Status | Evidence |
| --- | --- | --- |
| Transport connection | **failed in this environment** | a bounded 8-second recorder run made 2 attempts; both ended in `ConnectionResetError` (`connection_count: 0`, `connection_errors: 2`, `subscription_status: "not_attempted"`). TCP to `api.wallex.ir:443` connects, but the TLS handshake is reset, which indicates environment egress filtering rather than a confirmed Wallex outage. |
| Application subscription | **not attempted** | no socket ever opened, so no `connect`/`subscribe` frame was sent |
| Live trade received | **none** | `trade_events_received: 0` |
| Candle finalized from live data | **none** | `closed_candles_written_this_run: 0` |

The earlier operator-collected evidence (2026-10-23) recorded a working TCP/TLS/WebSocket handshake against the
deprecated `/ws` endpoint, an Engine.IO-style handshake object, and no trade event for either the legacy frame or
`public:BTCUSDT@trade`. That evidence is consistent with the diagnosis above but does not verify the v2 path.

## Known limitations and data-quality caveats

- Collection is prospective, not historical; the recorder is not a download endpoint.
- Disconnects, reconnects and process downtime create gaps. The manifest records them, but no gap is filled.
- A bucket without trades produces no candle. This is normal market behaviour, not necessarily data loss; the audit
  tool labels such gaps `potential_gap_or_no_trades`.
- `quantity` is used as the base-asset trade size; the documentation does not restate units per market. `volume` is
  one-sided: each documented trade record is added once, so taker and maker sides are not double counted. Buy and sell
  volume is not split, and `isBuyOrder` (maker side) is deliberately not reinterpreted into aggressor-side statistics.
- A restart opens a new run: the first bucket seen after the restart stays open until a later bucket arrives, so the
  interval spanning a restart can be missing even when the market traded. The audit reports that as a potential gap;
  `resumed_from_existing_output` and `previous_last_closed_candle_utc` record the boundary.
- Trade channels have no sequence numbers, so duplicates and late trades cannot be fully resolved; late trades are
  counted, not inserted, and duplicates inside one bucket are aggregated.
- The recorder captures trades this client received. It is not an exchange-verified tick archive.
- It does not include depth, executable spread, fee tier or slippage observations, and no backtest result on a short or
  gappy dataset is evidence of profitability.
- The `{}` heartbeat echo is taken from the documented frames (25 s ping, 8 s answer window, close code `3012`).
  The 60-second silence watchdog is an implementation choice, not a documented value, and no server timing has been
  observed live from this environment.
- Frames may carry several newline-separated JSON messages: this is stated and demonstrated by the official
  raw-protocol samples (`for line in raw.split("\n")` with the comment "a frame may contain several messages"),
  so the recorder splits every frame before classification. It is a documented rule, not an added assumption.

## Unresolved questions

1. Does a live v2 session actually answer `{"id": 2, "subscribe": {"channel": "public:BTCMTN@trade"}}` with an empty
   object today, and does it emit `{}` heartbeats every 25 s? A successful run is required to confirm.
2. Which market symbols are currently listed (for example whether `BTCUSDT` exists), and does the server answer `102`
   for inactive markets? Confirm against the official markets list and the manifest's subscription fields.
3. Is the deprecated v1 endpoint still usable by a raw client, with which Socket.IO packet framing, and until when?
   The official pages describe the logical frame but not the transport framing (see `D-019`).
4. Does the v2 server emit multiple newline-separated messages in one transport frame in practice? The splitter follows
   the official sample code, but this has not been observed live.
