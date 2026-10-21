# Spot order status and cancellation

The new documentation describes order detail/list fields including `clientOrderId`, `status`, `active`, `executedPercent`, `executedQty`, `executedPrice`, `executedSum`, and fill-level fee fields. The list page gives `NEW`, `FILLED`, and `CANCELED` as examples; it is not a complete enum list. [SPOT-ORDERS](https://developers.wallex.ir/docs/spot-order-list)

Active query: `GET /v1/account/openOrders`; history: `GET /v1/account/orders`; cancellation: `DELETE /v1/account/orders/{client_id}`. Legacy cancellation is `DELETE /v1/account/orders?clientOrderId=...`; the path/query mismatch is recorded in the discrepancy register. [SPOT-ACTIVE](https://developers.wallex.ir/docs/spot-active-orders) · [SPOT-ORDERS](https://developers.wallex.ir/docs/spot-order-list) · [SPOT-CANCEL](https://developers.wallex.ir/docs/spot-cancel-order) · [LEGACY-API](https://api-docs.wallex.ir/)

A generated page separately documents `DELETE //api.wallex.com/v1/account/orders` with a required JSON body field `clientOrderId` and `x-api-key` authorization. This differs from the prose path `DELETE /v1/account/orders/{client_id}` and the legacy query form. Preserve these as separate documented claims; the actual host, canonical route, identifier, auth, availability, and runtime behavior remain unresolved (D-003, D-013, D-016). [MOD-GENERATED-DELETE-ACCOUNT-ORDERS](https://developers.wallex.ir/docs/generated/delete-account-orders)

Cancellation is account-changing and was not executed. The docs do not establish race behavior, partial-fill cancellation guarantees, or the full terminal status set.
