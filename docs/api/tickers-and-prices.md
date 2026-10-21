# Tickers and prices

The legacy reference describes market statistics within `GET /v1/markets` and a global crypto statistics endpoint `GET /v1/currencies/stats`. Examples include bid/ask/last prices, 24h/7d changes and volume; examples include old dated values. [LEGACY-API](https://api-docs.wallex.ir/)

The modern sitemap contains pages for `public:all@price` and `public:all@fairPrice` WebSocket channels, but only `socket-intro` was reviewed in this pass for the names and public channel classification. Payload contracts and semantics for individual price channels remain not reviewed. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml)

Do not treat market statistics or examples as execution prices, guarantees, or current values.
