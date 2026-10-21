# WebSocket

## Current-looking guide

- URL: `wss://api.wallex.ir/connection/websocket`; documented Centrifugo protocol v2. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro)
- Public channels include `public:<SYMBOL>@trade`, `public:all@price`, `public:all@fairPrice`, `orderbook:<SYMBOL>@buyDepth`, `orderbook:<SYMBOL>@sellDepth`, and `candle:<SYMBOL>@<INTERVAL>`; private channel is `private:user#<userId>`. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro)
- SDK client examples use `Centrifuge`; public feeds do not require a token. Private events use token refresh and server-side channel membership. An active connection supports up to 64 channels. [SOCKET-CONNECTION](https://developers.wallex.ir/docs/socket-connection)
- Except candle channels, no history/snapshot is described; dropped intervals are not replayed. Candle channel history is limited to ten messages over two minutes. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro)
- Migration docs contrast legacy Socket.IO URL `wss://api.wallex.ir/ws`, legacy channels, and Centrifugo channel namespace/message format. [SOCKET-MIGRATION](https://developers.wallex.ir/docs/socket-migration)

This is documentary summary only; no live connection was opened. Channel payload schemas, event order, recovery guarantees, token expiration/refresh behavior, and private event taxonomy need additional page-level review.
