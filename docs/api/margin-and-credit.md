# Margin and trading credit

## Margin

Official guide states Margin supports collateral/credit and long/short positions and warns it is high risk. Reviewed create-position API: `POST /margin-trade/v1/positions`, JSON fields `collateral`, `market`, `open_price`, `risk_coef`, `side` (`long`/`short`), optional `stop_loss`, `take_profit`. Response example fields include `liquidity_price`, `interest`, `loan`, `max_age`, `state`, `profit`. These are field names, not an operating or risk model. [MARGIN-INTRO](https://developers.wallex.ir/docs/margin-intro) · [MARGIN-OPEN](https://developers.wallex.ir/docs/margin-open-position)

Other sitemap-listed Margin docs cover active markets, calculate loan, dry-run, collateral edit, positions, close, SL/TP, and types. They are in the inventory but not yet individually reviewed. [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml)

## Trading credit

`CREDIT-INTRO` says credit accounts are separate, each with separate wallet, API key and order history. The reviewed `CREDIT-TYPES` page summary describes general-plan entry-asset/credit terminology, a 30-day term, daily credit fee, warning/liquidation levels, wallet connection and automatic-transfer claims. The docs sitemap lists additional package, subaccount, balance, transfer/history and other credit APIs; account-changing operations are not covered in detail or invoked here. This evidence does **not** establish the user excerpt's exact 5,000,000-Toman amount, three-day term, example fee, exact liquidation/no-return outcome, full permission mapping, eligible-market list, or applicability to Starcoach. [CREDIT-INTRO](https://developers.wallex.ir/docs/trade-credit-intro) · [CREDIT-TYPES](https://developers.wallex.ir/docs/trade-credit-types) · [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml)

A credit account/financing arrangement does not itself authorize margin, leverage, shorting, futures, or every Spot market. This project remains offline and Spot-only. See the [user-supplied plan excerpt provenance and hackathon reconciliation](../knowledge-base/wallex-credit-plan-reconciliation.md); its missing market list and corrupted permissions table are not reconstructed.

No strategy or risk controls for these products are designed in this feature.
