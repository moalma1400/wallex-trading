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
