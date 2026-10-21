# Margin and trading credit

## Margin

Official guide states Margin supports collateral/credit and long/short positions and warns it is high risk. Reviewed create-position API: `POST /margin-trade/v1/positions`, JSON fields `collateral`, `market`, `open_price`, `risk_coef`, `side` (`long`/`short`), optional `stop_loss`, `take_profit`. Response example fields include `liquidity_price`, `interest`, `loan`, `max_age`, `state`, `profit`. These are field names, not an operating or risk model. [MARGIN-INTRO](https://developers.wallex.ir/docs/margin-intro) · [MARGIN-OPEN](https://developers.wallex.ir/docs/margin-open-position)

Other sitemap-listed Margin docs cover active markets, calculate loan, dry-run, collateral edit, positions, close, SL/TP, and types. They are in the inventory but not yet individually reviewed. [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml)

## Trading credit

Intro says credit accounts are separate, each with separate wallet, API key and order history. The docs sitemap lists package, subaccount, balance, wallet connection, transfer/history and other credit APIs; account-changing operations are not covered in detail or invoked here. [CREDIT-INTRO](https://developers.wallex.ir/docs/trade-credit-intro) · [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml)

No strategy or risk controls for these products are designed in this feature.
