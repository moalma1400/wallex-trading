# وب‌سوکت و داده بازار

مستند WebSocket جدید، Centrifugo-based version 2 را در `wss://api.wallex.ir/connection/websocket` معرفی می‌کند و آن را برای پیاده‌سازی جدید پیشنهاد می‌کند. Version 1 در `wss://api.wallex.ir/ws` منسوخ‌شده اما هنوز پشتیبانی‌شده توصیف شده است. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro)

کانال‌های عمومی نمونه شامل `public:<SYMBOL>@trade`, `public:all@price`, `public:all@fairPrice`, `orderbook:<SYMBOL>@buyDepth`, `orderbook:<SYMBOL>@sellDepth`, و `candle:<SYMBOL>@<INTERVAL>` است. کانال خصوصی `private:user#<userId>` به احراز هویت نیاز دارد. فرمت و صلاحیت دقیق هر کانال باید در صفحه اختصاصی‌اش بررسی شود. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro)

مستند می‌گوید به‌جز candle، کانال‌ها snapshot/history ندارند؛ subscription خالی است و قطع اتصال باعث از دست‌رفتن پیام‌های بین قطعی می‌شود. کانال candle حداکثر ۱۰ پیام تا دو دقیقه نگه می‌دارد. این شرط مهم برای آتی reconciliation است؛ تضمین کلی ordering/replay برای دیگر کانال‌ها مستند نشده است. [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [SOCKET-CONNECTION](https://developers.wallex.ir/docs/socket-connection)

صفحه اتصال SDK رسمی `Centrifuge` را نشان می‌دهد؛ سقف ۶۴ کانال در یک اتصال را اعلام می‌کند. برای کانال private، token در claim `channels` قرار می‌گیرد و server خودکار عضو می‌کند؛ مثال توکن از cookie session استفاده می‌کند و به هیچ وجه در این پروژه اجرا نشده است. [SOCKET-CONNECTION](https://developers.wallex.ir/docs/socket-connection)

مرجع قدیمی Socket.IO (`socket.io-client` نسخه `v2.5.0` یا سازگار) و کانال‌های مانند `SYMBOL@trade` و `SYMBOL@buyDepth` را توضیح می‌دهد. این قرارداد با namespace و envelope نسخه جدید متفاوت است؛ مستند جدید خود v1 را legacy می‌نامد و migration guide نگاشت ارائه می‌دهد. برای سیستم جدید، قراردادها را مخلوط نکنید. [LEGACY-API](https://api-docs.wallex.ir/) · [SOCKET-MIGRATION](https://developers.wallex.ir/docs/socket-migration)
