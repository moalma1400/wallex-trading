# پرسش‌های حل‌نشده

این فهرست خروجی research pass است؛ پاسخ به پرسش‌های سیاستی/حسابی را از کاربر یا مرجع رسمی بگیرید، نه از حدس. پرسش‌های ثبت‌شده برای کاربر به معنی پیش‌نیاز این feature مستنداتی نیستند.

## برای تکمیل مستندات رسمی

1. برای ۸۸ صفحه sitemap جدید که وضعیت `not_started` دارند، محتوای واقعی هر صفحه، endpointها، payloadها، permissions، enums، rate limits، schemaهای Swagger و ارجاعاتش چیست؟ (فهرست کامل در ماتریس)
2. آیا صفحه‌های جدید `generated/*` اسناد مستقلی هستند یا نسخه‌های تولیدشده از schema؟ version و changelog رسمی/API release notes کجاست؟
3. آیا صفحات راهنمای صرافی/Help Center، FAQ، Terms، محدودیت‌های دسترسی، notices و اختلال سرویس از طریق ناوبری رسمی در دسترس‌اند؟ صفحه fee help با URL کشف‌شده 404 می‌دهد؛ لینک جاری جایگزین چیست؟
4. آیا جدول commission روی `https://wallex.ir/commission` مشکل نمایش/دسترسی دارد یا عمداً خالی است؟ نرخ‌های جاری Spot برای user level/market و تاریخ مؤثرشان کجا منتشر می‌شود؟ پیشنهاد ۰٫۱٪ در مقاله رسمی چه زمان/شرایطی داشته و آیا هنوز فعال است؟
5. مسیر API جاری market-list کدام است (`/hector/web/v1/markets` یا `/v1/markets`) و قرارداد رسمی symbol precision، `stepSize`, `tickSize`, `minQty`, `maxQty`, `minNotional` چیست؟
6. روش current authentication، headerها، key expiry/revocation، permissions به تفکیک endpoint، تعداد کلید، IP allowlist و الزامات subaccount کدام‌اند؟ آیا `X-API-Key` همچنان جاری است؟
7. کدام enumهای کامل، وضعیت‌های نهایی، transitionهای order، fillهای partial، رفتار client IDs، idempotency/retry، pagination، زمان‌بندی و reconciliation مستند شده‌اند؟
8. مستند جاری برای maker/taker fee formula، commission asset، tierهای حساب، pair exceptions، Market protection/partial fill، quote TTL و rate limits همه endpointها چیست؟
9. برای WebSocket، schema همه channelها، ordering، snapshots، replay/recovery، نگهداشت تاریخچه، reconnect behavior، token expiration/refresh و taxonomy رویدادهای private کدام صفحه‌ها هستند؟
10. برای Margin/اعتبار معاملاتی، شرایط بهره/کارمزد، liquidation/warning logic، مدت اعتبار، extension، cross-product order/account boundaries و transfer automation چه اسناد کامل و تاریخ‌داری وجود دارد؟
11. آیا Wallex برای توقف API، نگهداری، تغییر قراردادها یا محدودیت جغرافیایی/کاربری منابع رسمی/اعلان‌های قابل پیگیری دارد؟
12. آیا sitemap pathهایی که فقط در sitemap آمده‌اند هنوز reachable هستند؟ (باید با تکمیل هر صفحه/coverage review بررسی شود؛ پژوهش این pass آدرس‌ها را فراخوانی نکرد.)

## ریسک حقوقی / compliance

13. منبع OFAC رسمی اعلام می‌کند Wallex در ۲ ژوئن ۲۰۲۶ designated شده و FAQ 1257 می‌گوید اشخاص غیرآمریکایی ممکن است در صورت معامله با آن با ریسک تحریم مواجه شوند. این پروژه قوانین هلند/اتحادیه اروپا، وضعیت شخصی/حقوقی کاربر، بانک/پرداخت‌گر، یا مجاز بودن هر فعالیت را بررسی نکرده است. قبل از هرگونه استفاده، بررسی مستقل و به‌روز با مشاور حقوقی/انطباق لازم است. [US-TREASURY-WALLEX-DESIGNATION](https://home.treasury.gov/news/press-releases/sb0519) · [OFAC-FAQ-1257](https://ofac.treasury.gov/faqs/1257)

## تصمیم‌های آتی نیازمند نظر مالک پروژه

- هدف آتی پروژه و روش استفاده: مطالعه/دستی، decision support، paper research، یا اتوماسیون؟ (هیچ‌کدام در این feature انتخاب نشده‌اند.)
- بازارهای هدف، دارایی‌ها، بازه زمانی و ریسک‌پذیری؟ عمداً تعیین نشده‌اند.
- معماری اجرا و میزان مجوز API؟ عمداً تعیین نشده‌اند.
- انتخاب license؟ هنوز انتخاب نشده.
- آیا پس از تکمیل inventory باید feature جداگانه‌ای برای ارزیابی حقوقی/دسترسی و قابلیت‌های بازار (بدون اجرای سفارش) ساخته شود؟

### Additional findings from 2026-10-21 follow-up review

14. What is the canonical per-service REST host and exact path/version where official overview, generated API pages and Swagger artifacts disagree between `api.wallex.ir` and `api.wallex.com`, or show leading `//`? No endpoint was called; `D-013` retains the evidence and uncertainty.
15. Which candle resolutions are available for historical UDF data versus live WebSocket channels, and what are their boundary/timezone guarantees? The two pages expose different lists; see `D-014`.
16. Can the official OpenAPI/Swagger artifacts be retrieved as complete original bytes with version/date/checksum so the repository can preserve and validate them locally? Current page-reader responses are transformed and chunked; five artifact records are `in_progress`, not full captures.
17. What is the complete schema/authentication/permissions and lifecycle contract for every generated Spot, account, Margin, OTC, trade-credit, and private WebSocket operation? The current review leaves 51 sitemap pages `not_started`; one sitemap URL returned localized not-found content, and its replacement/status is unknown.
18. Do Smart98 public docs or a reviewed user-supplied interface contract exist? None was verified in this checkout, so no adapter or endpoint has been invented.
19. Which UDF-history field requiredness and resolution set is canonical? The basic page marks fields Optional; generated `candle-history` and the legacy reference mark them Required, and the modern pages show different resolution examples. See `D-008` and `D-015`; no runtime call is permitted.
20. Does the sitemap-listed `/docs/weekly` have a replacement or is it retired? The page reader returned a localized not-found body without an HTTP status; the source is `blocked`/`inaccessible` and no reason is inferred.
