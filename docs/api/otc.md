# OTC / easy trade

The modern docs separate OTC/easy-trade from Spot.

- Quote endpoint `GET /v1/account/otc/price`, query parameters required: `side` (`BUY`/`SELL`) and `symbol`. Example response fields: `price`, `price_expires_at`, `ttl`, `current_time`. [OTC-PRICE](https://developers.wallex.ir/docs/otc-price)
- Create-order page documents `POST /v1/account/easy-trade/orders`; JSON/request fields `side`, `symbol`, `quantity`, `from` (required; value `otc`). Response includes `type: OTC`, fill and fee fields. Treat this as account-changing; no request was sent. [OTC-CREATE](https://developers.wallex.ir/docs/otc-create-order)
- Legacy guide instead shows quote `GET /v1/account/otc/price` and order `POST /v1/account/otc/orders` using `amount`. It has historical price/fee examples. Path/payload differences require reconciliation with current official schema; don't blend. [LEGACY-API](https://api-docs.wallex.ir/)

Exact current quote lifetime, order amount precision/notional, price protection, commission rules, failure/retry behavior, and market eligibility remain unverified.
