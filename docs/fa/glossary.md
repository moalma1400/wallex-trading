# واژه‌نامه

| اصطلاح | معنی در این پایگاه دانش | شاهد |
|---|---|---|
| `symbol` / market | شناسه بازار، مانند `BTCUSDT` در مثال مستندات؛ نمونه به معنی بازار جاری نیست | [MARKETS](https://developers.wallex.ir/docs/basic-services-markets) |
| `base_asset` / `quote_asset` | در نمونه بازار، دارایی معامله‌شونده و دارایی قیمت‌گذار | [MARKETS](https://developers.wallex.ir/docs/basic-services-markets) |
| Spot | سفارش در order book و تطبیق با سمت مخالف | [SPOT-INTRO](https://developers.wallex.ir/docs/spot-intro) |
| OTC / معامله آنی | جریان quote و سفارش جدا از spot order book | [OTC-PRICE](https://developers.wallex.ir/docs/otc-price) · [OTC-CREATE](https://developers.wallex.ir/docs/otc-create-order) |
| Maker / Taker | فیلدهای نرخ/ضریب کارمزد که مستندات API نام می‌برند؛ تعریف دقیق اجرا/طبقه‌بندی باید تأیید شود | [ACCOUNT-FEE](https://developers.wallex.ir/docs/basic-services-account-fee) |
| `stepSize`, `tickSize`, `minQty`, `minNotional` | فیلدهای محدودیت بازار در مرجع legacy؛ مقدارهای ثابتِ جاری از آنها استنباط نمی‌شود | [LEGACY-API](https://api-docs.wallex.ir/) |
| `clientOrderId` / `client_id` | نام‌های مشابه شناسه سفارش در مسیرهای جدید/قدیمی؛ یکسان بودن قراردادها نیازمند بررسی | [SPOT-CREATE](https://developers.wallex.ir/docs/spot-create-order) · [LEGACY-API](https://api-docs.wallex.ir/) |
| Margin / معامله تعهدی | موقعیت اعتباری Long/Short؛ با ریسک بالای اعلام‌شده | [MARGIN-INTRO](https://developers.wallex.ir/docs/margin-intro) |
| اعتبار معاملاتی | اکانت جدا با کیف پول و API key اختصاصی، طبق معرفی رسمی | [CREDIT-INTRO](https://developers.wallex.ir/docs/trade-credit-intro) |
| Centrifugo v2 | قرارداد WebSocket جدید معرفی‌شده توسط مستندات؛ v1 Socket.IO منسوخ‌شده نامیده می‌شود | [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) |
