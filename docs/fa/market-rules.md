# بازارها و قواعد نماد

مستند مدرن سرویس پایه مسیر `GET /hector/web/v1/markets` را برای فهرست بازارها نشان می‌دهد. نمونه ساختار شامل `symbol`, `base_asset`, `quote_asset`, داده‌های آماری و booleanهایی مانند `is_spot`, `is_otc`, `is_margin`, `is_tmn_based`, `is_usdt_based` است. صفحه Spot نیز همین مسیر را برای بازارهای فعال معرفی می‌کند و `is_spot=true` را نشانه فعال بودن در Spot می‌داند. نمونه ساختار، مقدار جاری هر بازار را نمی‌دهد. [MARKETS](https://developers.wallex.ir/docs/basic-services-markets) · [SPOT-MARKETS](https://developers.wallex.ir/docs/spot-active-markets)

مرجع قدیمی `GET /v1/markets` را با `baseAsset`, `quoteAsset`, `baseAssetPrecision`, `quotePrecision`, `stepSize`, `tickSize`, `minQty`, `maxQty`, `minNotional` توصیف می‌کند. نمونه‌های همان مرجع قدیمی‌اند؛ هیچ مقدار حداقل یا دقت از آنها به‌عنوان مقدار امروز استفاده نمی‌شود. [LEGACY-API](https://api-docs.wallex.ir/)

تا زمانی که اسناد دقیق و جاری برای یک بازار را بررسی نکرده‌ایم، موارد زیر نامعلوم‌اند: محدودیت‌های دقیق هر بازار، دقت عددی در کاربرد واقعی، وضعیت جهت خرید/فروش، تفاوت بازار/نوع معامله، و زمان به‌روزرسانی این metadata. ابتدا API رسمی را فقط برای طراحی آتی مستند کنید؛ این پروژه برای آزمایش API آن را اجرا نمی‌کند.


## داده تاریخی محلی

Feature 003، metadata نماد را از فایل محلیِ ارائه‌شده کاربر می‌پذیرد و مقادیر `price_precision`/`amount_precision` مستند را به قانون اجرایی تبدیل نمی‌کند. سقف precision، نمادهای شناخته‌شده، فاصله، بازه و freshness باید برای هر audit صریح تعیین شوند. اختلاف host، ساختار و security note بین صفحه‌های رسمی همچنان باز است؛ هیچ endpointی فراخوانی نشده است. [MARKETS](https://developers.wallex.ir/docs/basic-services-markets) · [MOD-GENERATED-GET-MARKETS](https://developers.wallex.ir/docs/generated/get-markets) · [Feature 003](../../specs/003-historical-market-data/spec.md) · [D-017](../research/discrepancies.md)
