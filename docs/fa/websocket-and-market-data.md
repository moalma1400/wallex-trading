# وب‌سوکت و داده‌های بازار

## نسل‌های اتصال

راهنمای والکس WebSocket نسخه ۲ بر پایه Centrifugo را در `wss://api.wallex.ir/connection/websocket` مستند می‌کند. نسخه ۱ در `wss://api.wallex.ir/ws` منسوخ‌شده توصیف شده اما همان صفحه می‌گوید هنوز کار می‌کند؛ تاریخ پایان پشتیبانی ذکر نشده است. «منسوخ» را با «خاموش» یکی نگیرید. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [MOD-SOCKET-ALL-PRICE](https://developers.wallex.ir/docs/socket-all-price) · [SOCKET-MIGRATION](https://developers.wallex.ir/docs/socket-migration)

نمونه کانال‌های نسخه ۲ شامل `public:<SYMBOL>@trade`, `public:all@price`, `public:all@fairPrice`, `orderbook:<SYMBOL>@buyDepth`, `orderbook:<SYMBOL>@sellDepth`, و `candle:<SYMBOL>@<INTERVAL>` است. نام کانال و بزرگی/کوچکی حروف در برخی کانال‌ها اهمیت دارد؛ نمونه‌ها قرارداد اجراشده توسط این پروژه نیستند. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [MOD-SOCKET-FAIR-PRICE](https://developers.wallex.ir/docs/socket-fair-price)

## رفتار پیام و بازیابی

- `all@price` فقط هنگام تغییر قیمت پیام می‌دهد؛ عضویت snapshot اولیه یا تاریخچه نمی‌دهد. قطع اتصال ممکن است موجب از دست‌رفتن پیام‌ها شود. [MOD-SOCKET-ALL-PRICE](https://developers.wallex.ir/docs/socket-all-price)
- `all@fairPrice` به‌عنوان snapshot دوره‌ای همه قیمت‌های در دسترس مستند شده است (معمولاً هر ۲۰ ثانیه و گاهی حدود ۳۵ ثانیه). در یک snapshot ممکن است نمادی وجود نداشته باشد؛ نبودن آن به معنی حذف بازار نیست. صفحه می‌گوید کانال تاریخچه ندارد. این توصیف مستند است، نه تضمین uptime بررسی‌شده. [MOD-SOCKET-FAIR-PRICE](https://developers.wallex.ir/docs/socket-fair-price)
- پیام‌های معاملات برای رویدادهای جدیدند و تاریخچه/بازیابی معاملات ازدست‌رفته هنگام قطع اتصال را ارائه نمی‌کنند. پیام‌های عمق خرید/فروش snapshot کامل‌اند، نه delta؛ عضویت نیز snapshot اولیه نمی‌فرستد. [MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade) · [MOD-SOCKET-BUY-DEPTH](https://developers.wallex.ir/docs/socket-buy-depth) · [MOD-SOCKET-SELL-DEPTH](https://developers.wallex.ir/docs/socket-sell-depth)
- کانال کندل نمونه‌های `1m`, `1h`, `1d` دارد. بدنه شبیه UDF OHLCV است؛ کندل باز با `t` یکسان می‌تواند چند بار تغییر کند و باید جایگزین همان کندل شود، نه اینکه رکورد تازه بسازد. history کانال طبق صفحه حداکثر ۱۰ پیام تا دو دقیقه نگه می‌دارد؛ تاریخچه اصلی از API UDF می‌آید. این intervalها با فهرست resolutionهای صفحه UDF کاملاً یکسان نیستند و اختلاف ثبت شده است. [MOD-SOCKET-CANDLE](https://developers.wallex.ir/docs/socket-candle) · [CANDLES](https://developers.wallex.ir/docs/basic-services-candles) · [D-014](../research/discrepancies.md)
- راهنمای پروتکل خام v2 درباره connect/subscribe، پاسخ ping، سقف کانال و کدهای خطا توضیح می‌دهد؛ برای public channel توکن لازم نیست، اما این پروژه حتی اتصال عمومی را هم باز نمی‌کند. اطلاعات ordering/replay قابل تعمیم به تضمین سرویس نیست. [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol)

## کانال‌های خصوصی

صفحه private channel رویدادهای `balanceUpdated`, `orderSaved`, `orderRemoved`, `tradeDetails` را مستند می‌کند و در v2 عضویت `private:user#<userId>` را به token وابسته می‌داند. این‌ها داده شخصی حساب هستند. هیچ account، token، cookie یا private channel در این پروژه به کار نرفته است. [MOD-SOCKET-PRIVATE-CHANNEL](https://developers.wallex.ir/docs/socket-private-channel) · [SOCKET-TOKEN](https://developers.wallex.ir/docs/socket-token)

## مرز این مخزن

هیچ اتصال زنده، API/stream token، feed adapter یا paper trading متصل به صرافی وجود ندارد. Feature 002 فقط داده محلی/ساختگی را به‌صورت آفلاین بازپخش می‌کند؛ آن را با جریان paper trading واقعی اشتباه نگیرید. مستندبودن کانال، availability، مجوز حساب، صحت داده یا قانونی‌بودن استفاده را تضمین نمی‌کند.
