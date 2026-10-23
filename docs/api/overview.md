# نمای کلی API والکس

## دامنه‌ها، نسل‌ها و provenance

- مقدمه رسمی توسعه‌دهندگان base API را `https://api.wallex.ir` معرفی می‌کند و می‌گوید بدنه درخواست‌ها JSON است. [MOD-INTRO](https://developers.wallex.ir/docs)
- در مقابل، صفحات generated و artifactهای Swagger رسمی که در این pass بررسی شد بعضی `host: api.wallex.com` و بعضی `host: api.wallex.ir` دارند. چند مثال generated به‌شکل `//api.wallex.com/...` آمده و مسیرهای بدون version prefix نیز وجود دارد. این تفاوت‌ها به‌عنوان تعارض مستندات ثبت شده‌اند؛ این مخزن هیچ میزبانی را برای اجرای درخواست انتخاب نمی‌کند. [MOD-GENERATED-GET-MARKETS](https://developers.wallex.ir/docs/generated/get-markets) · [MOD-GENERATED-GET-DEPTH](https://developers.wallex.ir/docs/generated/get-depth) · [MOD-GENERATED-POST-ACCOUNT-ORDERS](https://developers.wallex.ir/docs/generated/post-account-orders) · [MOD-SPEC-SPOT](https://developers.wallex.ir/assets/files/spot-b9d06896d1009adc9ebc69b9a5495e7e.json) · [D-013](../research/discrepancies.md)
- سند قدیمی `api-docs.wallex.ir` host `api.wallex.ir` و مسیرهایی چون `/v1`, `/v2`, `/v3` را نشان می‌دهد؛ آن را قرارداد جداگانه تاریخی/legacy نگه می‌داریم. [LEGACY-API](https://api-docs.wallex.ir/)
- WebSocket در اسناد جدید Centrifugo v2 با آدرس `wss://api.wallex.ir/connection/websocket` آمده؛ نسخه v1 در `wss://api.wallex.ir/ws` در همان اسناد deprecated توصیف شده اما تاریخ پایان پشتیبانی اعلام نشده است. تنها مؤلفه‌ای که می‌تواند اتصال عمومی باز کند، CLI اختیاری ضبط‌کننده کندل (`wallex-candle-recorder`) است که فقط کانال عمومی معاملات را با فریم‌های مستند v2 subscribe می‌کند. یک تلاش محدود در ۲۰۲۶-۱۰-۲۳ از این محیط در مرحله TLS با `ConnectionResetError` شکست خورد؛ بنابراین موفقیت اتصال، عضویت سطح کاربرد و دریافت معامله هنوز تأیید نشده است. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol)

## قالب و احراز هویت

صفحه مقدمه جدید نوع‌های `number`, `number string`, `string`, ISO-8601 `datetime` و Unix `timestamp` را شرح می‌دهد. همان صفحه می‌گوید بدنه درخواست JSON و `Content-Type: application/json` باشد. مرجع قدیمی برای برخی `PUT`, `POST`, `PATCH`ها query/body و `x-www-form-urlencoded` یا JSON را نشان می‌دهد؛ این روش‌ها را با سند جدید یکی فرض نکنید. [MOD-INTRO](https://developers.wallex.ir/docs) · [LEGACY-API](https://api-docs.wallex.ir/)

صفحات generated بررسی‌شده header `x-api-key` را برای بعضی منابع نشان می‌دهند، از جمله balance, fee, wallet و سفارش. این یک مشاهده از مستند است، نه مجوز استفاده یا قرارداد auth کامل؛ مجوزها و headerهای endpointهای دیگر حل نشده‌اند. [MOD-GENERATED-GET-ACCOUNT-BALANCES](https://developers.wallex.ir/docs/generated/get-account-balances) · [MOD-GENERATED-GET-ACCOUNT-FEES](https://developers.wallex.ir/docs/generated/get-account-fees) · [MOD-GENERATED-GET-ACCOUNT-WALLET-BY-SYMBOL](https://developers.wallex.ir/docs/generated/get-account-wallet-by-symbol) · [MOD-GENERATED-POST-ACCOUNT-ORDERS](https://developers.wallex.ir/docs/generated/post-account-orders)

## مستندات generated و API specifications

صفحه Swagger سرویس پایه لینک مستقیم به فایل JSON می‌دهد. فایل‌های Swagger/OpenAPI رسمی Spot، basic-services، OTC، Margin و trade-credit به source register افزوده شده‌اند؛ خروجی ابزار مرور در chunkهای متنی تبدیل‌شده/ناقص بود و artifactهای اصلی به‌صورت byte-for-byte ذخیره نشده‌اند. بنابراین این‌ها هنوز بررسی کامل schema یا نسخه‌بندی‌شده محسوب نمی‌شوند. [MOD-BASIC-SERVICES](https://developers.wallex.ir/docs/basic-services) · [MOD-SPEC-BASIC-SERVICES](https://developers.wallex.ir/assets/files/basic-services-89626420b5f06e4d7a2dc9206cdeb192.json) · [MOD-SPEC-SPOT](https://developers.wallex.ir/assets/files/spot-b9d06896d1009adc9ebc69b9a5495e7e.json) · [MOD-SPEC-MARGIN](https://developers.wallex.ir/assets/files/margin-c709e1f52cb44387a2e35ffd678c6dfa.json) · [MOD-SPEC-OTC](https://developers.wallex.ir/assets/files/otc-8e321a32f4509cbf103b3127bf7c9918.json) · [MOD-SPEC-TRADE-CREDIT](https://developers.wallex.ir/assets/files/trade-credit-ff5c60b5b97b77a5b2c2e4800f07729c.yaml)

## دامنه و وضعیت پژوهش

موضوعات کشف‌شده شامل Spot، market metadata، depth/trades/candles، OTC، Margin، trade credit/subaccounts، balances/fees، auth/API keys و WebSocket است. وجود URL در sitemap تنها discovery را ثابت می‌کند. در snapshot پیگیری 2026-10-21، از 115 صفحه sitemap تعداد 63 صفحه بازبینی شده، 51 صفحه `not_started` و یک URL دارای پاسخ localized not-found است؛ 5 artifact رسمی OpenAPI در وضعیت `in_progress` هستند. [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml) · [coverage matrix](../research/coverage-matrix.md)

## مرز ایمنی و قانونی

این مخزن هیچ API یا WebSocket والکس را فراخوانی نمی‌کند، credential یا حساب خصوصی ندارد، و سفارش/لغو/تغییر/انتقال/برداشت انجام نمی‌دهد. مستند endpoint مجوز، availability یا eligibility را اثبات نمی‌کند. هرگونه استفاده واقعی در آینده منوط به specification و بررسی جداگانه قرارداد/امنیت/ریسک و مشاوره مستقل و به‌روز حقوقی/انطباق متناسب با jurisdiction است؛ هیچ تضمین قانونی داده نمی‌شود. منبع Treasury/OFAC موجود در ثبت پژوهش، ریسک sanctions مهمی را مطرح می‌کند و ارزیابی کامل قانون هلند/اتحادیه اروپا یا شرایط شخصی نیست. [US-TREASURY-WALLEX-DESIGNATION](https://home.treasury.gov/news/press-releases/sb0519) · [OFAC-FAQ-1257](https://ofac.treasury.gov/faqs/1257)


## Feature 004 challenge controls (separate from Wallex API docs)

The hackathon brief and its internal offline controls are documented separately from official API contracts. The user-supplied brief is not official-source verification; no endpoint, API field, account rule or current market is inferred from the following architecture. [Feature 004 architecture](challenge-architecture.md) · [challenge knowledge base](../knowledge-base/README.md)
