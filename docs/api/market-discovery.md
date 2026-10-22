# Market discovery

### New developer guide

- `GET /hector/web/v1/markets` is documented for markets metadata. Example properties include `symbol`, `base_asset`, `quote_asset`, `is_spot`, `is_otc`, `is_margin`, `is_tmn_based`, `is_usdt_based`, `amount_precision`, and `price_precision`; the page does not provide immutable per-symbol values. [MARKETS](https://developers.wallex.ir/docs/basic-services-markets)
- Spot active markets are documented at the same path; page says `is_spot=true` indicates Spot trading. [SPOT-MARKETS](https://developers.wallex.ir/docs/spot-active-markets)
- Separate product docs may describe product-specific active-market pages; their sitemap entries have not all been reviewed. [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml)

### Legacy reference

The legacy API reference documents `GET /v1/markets`, symbol metadata including `baseAsset`, `quoteAsset`, `stepSize`, `tickSize`, `minQty`, `maxQty`, `minNotional`; examples are historical and should not be treated as current restrictions. [LEGACY-API](https://api-docs.wallex.ir/)

The new and old responses differ in names and documented routes. Do not merge field names or infer a guaranteed one-to-one mapping.
