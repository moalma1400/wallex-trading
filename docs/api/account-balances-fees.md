# Account balances and fees

- New docs `GET /v1/account/fee` for account fee level; response example has per-market `makerFeeRate`, `takerFeeRate`, and `recent_days_sum`. No actual current rates are included in the reviewed page. [ACCOUNT-FEE](https://developers.wallex.ir/docs/basic-services-account-fee)
- Legacy guide documents `GET /v1/account/balances`; examples distinguish `value` from `locked`, and `asset`, `faName`, `fiat`. This is legacy evidence only until a current balances page is reviewed. [LEGACY-API](https://api-docs.wallex.ir/)
- The modern sitemap lists pages for balances (`get-account-balances`, `get-account-wallet-by-symbol`), fee, card/IBAN, and sub-account balances; those individual routes are in the inventory and most remain not reviewed. [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml)

No account data was accessed. Account-specific values must not be copied into this knowledge base.
