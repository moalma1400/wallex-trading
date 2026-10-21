# Spot orders

### Create

`POST /v1/account/orders`; documented JSON fields: `price` (String, required), `quantity` (String, required), `side` (`BUY`/`SELL`, required), `symbol` (String, required), `type` (`LIMIT`, `MARKET`, `STOP_LIMIT`, `STOP_MARKET`, required), `stop_Price` (conditional for stop order types), and `client_id` (optional unique string). Documentation says HTTP `201` on success and a limit of 20 create-order requests per 10 seconds. Note exact case `stop_Price` and `client_id` from the page; confirm these against the official current schema before implementation. [SPOT-CREATE](https://developers.wallex.ir/docs/spot-create-order)

### Order types

The user guide explains Limit, Market, Stop Limit, and Stop Market. It states Market may execute across several prices and describes an auto-cancel condition for insufficient book depth or 2% last-trade price movement. [SPOT-TYPES](https://developers.wallex.ir/docs/spot-types)

### Cancellation and listing

New cancel guide: `DELETE /v1/account/orders/{client_id}`. Active orders: `GET /v1/account/openOrders`, query filters `symbol`, `page`, `per_page`. Order history: `GET /v1/account/orders`, query filters `from`, `to`, `page`, `per_page`, `type`, `side`, `market`. These are endpoint-document statements; don't call them in this project. [SPOT-CANCEL](https://developers.wallex.ir/docs/spot-cancel-order) · [SPOT-ACTIVE](https://developers.wallex.ir/docs/spot-active-orders) · [SPOT-ORDERS](https://developers.wallex.ir/docs/spot-order-list)

### Response & unresolved behavior

Documented response fields include order IDs, original/executed quantities and sums, percentage, `status`, `active`, `fills`, fee amounts/assets/coefficient, and timestamps. The pages do not provide a complete authoritative status enumeration, state machine, idempotency/retry semantics, pagination defaults, or consistency/reconciliation guarantee. [SPOT-CREATE](https://developers.wallex.ir/docs/spot-create-order) · [SPOT-ORDERS](https://developers.wallex.ir/docs/spot-order-list)
