# مفاهیم و انواع معامله

## Spot

راهنمای Spot می‌گوید سفارش‌ها پس از ورود به order book و تطبیق با سفارش سمت مخالف معامله می‌شوند. معامله Spot ممکن است با اکانت اصلی یا اکانت اعتبار معاملاتی باشد؛ صفحه مستندات می‌گوید برای اکانت اعتباری باید API key همان اکانت و header `sub-account-client-id` استفاده شود. [SPOT-INTRO](https://developers.wallex.ir/docs/spot-intro)

انواع سفارش ذکرشده در صفحه Spot عبارت‌اند از `LIMIT`, `MARKET`, `STOP_LIMIT`, `STOP_MARKET`. جزئیات رفتار و محدودیت گزارش‌شده برای Market در صفحه اختصاصی آمده است و نباید به همه بازارها تعمیم داده شود. [SPOT-TYPES](https://developers.wallex.ir/docs/spot-types)

## معامله آنی / OTC

والکس برای معامله آنی اسناد جداگانه دارد؛ قیمت از طریق quote API گرفته می‌شود و صفحه مدرن پاسخ شامل `price`, `price_expires_at`, `ttl`, `current_time` را نمونه‌سازی می‌کند. زمان اعتبار باید از quote جاری بررسی شود؛ مقدار ثابت از نمونه استنباط نمی‌شود. [OTC-PRICE](https://developers.wallex.ir/docs/otc-price)

## معامله تعهدی / Margin

صفحه رسمی Margin آن را روشی با اعتبار و موقعیت Long/Short معرفی می‌کند و صراحتاً ریسک بالای این نوع معامله و امکان ضرر قابل‌توجه را گوشزد می‌کند. صفحه API باز کردن موقعیت path `POST /margin-trade/v1/positions` و فیلدهایی مانند `collateral`, `market`, `open_price`, `risk_coef`, `side`, `stop_loss`, `take_profit` را مستند می‌کند. وجود فیلد به‌معنی توصیه به استفاده یا مجاز بودن در حساب خاص نیست. [MARGIN-INTRO](https://developers.wallex.ir/docs/margin-intro) · [MARGIN-OPEN](https://developers.wallex.ir/docs/margin-open-position)

## اعتبار معاملاتی

راهنمای اعتبار معاملاتی توضیح می‌دهد هر اکانت اعتبار معاملاتی از اکانت اصلی و سایر اکانت‌ها جداست و کیف پول، API key و تاریخچه سفارش مستقل دارد. محصول و شرایط دقیق باید از صفحات جاری و حساب خود تأیید شوند. [CREDIT-INTRO](https://developers.wallex.ir/docs/trade-credit-intro)

## مرزبندی شواهد

صفحه اصلی و مقدمه توسعه‌دهندگان وجود این حوزه‌ها را معرفی می‌کنند؛ جزئیات endpointهای هر کدام تنها پس از بررسی صفحه اختصاصی قابل درج است. [WALLEX-HOME](https://wallex.ir/) · [MOD-INTRO](https://developers.wallex.ir/docs)
