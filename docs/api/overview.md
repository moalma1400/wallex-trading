# نمای کلی API

## دامنه‌ها و نسخه‌ها

- مستند توسعه‌دهندگان فعلی می‌گوید APIها از `https://api.wallex.ir` ارائه می‌شوند و JSON برمی‌گردانند؛ APIهای دارای اطلاعات شخصی یا امکان تراکنش با API key و سازوکارهای امنیتی محافظت می‌شوند. [MOD-INTRO](https://developers.wallex.ir/docs)
- مرجع قدیمی نیز `https://api.wallex.ir` را معرفی می‌کند و مسیرهایی از جمله `/v1/...` و `/v2/depth/all` را فهرست می‌کند. آن را شاهد تاریخی/قدیمی نگه می‌داریم و با اسناد جدید یکی فرض نمی‌کنیم. [LEGACY-API](https://api-docs.wallex.ir/)
- نقشه سایت عمومی مستندات توسعه‌دهندگان، دسته‌های Spot، OTC، Margin، اعتبار معاملاتی، سرویس‌های پایه و WebSocket را فهرست می‌کند. فهرست URLها و وضعیت هر صفحه در [ثبت منبع](../research/source-register.yaml) است. [MOD-SITEMAP](https://developers.wallex.ir/sitemap.xml)

## قراردادهای داده و درخواست

صفحه مقدمه جدید نوع‌هایی مانند `number`, `number string`, `string`, ISO-8601 `datetime` و Unix `timestamp` را شرح می‌دهد. همان صفحه می‌گوید بدنه درخواست باید JSON باشد و `Content-Type: application/json` در header قرار گیرد. [MOD-INTRO](https://developers.wallex.ir/docs)

مرجع قدیمی برای `PUT`, `POST`, `PATCH` امکان ارسال پارامتر در query یا body و دو قالب `x-www-form-urlencoded` یا `application/json` را ذکر می‌کند. این اختلاف مهم است؛ برای درخواست جدید، دستور مدرن را مبنا بگیرید ولی endpoint خاص را از همان صفحه خود endpoint تأیید کنید. [LEGACY-API](https://api-docs.wallex.ir/)

## دامنه مستندات

موضوعات کشف‌شده شامل بازار و market metadata، order book، trades و candles، spot سفارش‌ها، OTC quote/order، Margin و اعتبار معاملاتی، account balances/fees، احراز هویت/کلیدها و WebSocket است. وجود صفحه در sitemap تنها کشف URL را اثبات می‌کند؛ صفحه‌های `not_started` هنوز بررسی محتوایی نشده‌اند. وال‌گیت در مرجع قدیمی دارای مسیرهای جداگانه است و به‌عنوان محصول/فروشگاه غیرمعاملاتی این feature خارج از خلاصه‌های معامله قرار می‌گیرد.

## احتیاط

این مخزن endpointها را برای اجرا فراخوانی نمی‌کند و اعتبار کلید API را نمی‌سازد یا نمی‌آزماید. مستند بودن endpoint مجوز استفاده یا تغییر حساب نیست.
