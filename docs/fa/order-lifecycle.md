# چرخه سفارش

## ثبت و انواع

صفحه مدرن Spot برای ثبت سفارش `POST /v1/account/orders` معرفی می‌کند. بدنه JSON شامل `price`, `quantity`, `side`, `symbol`, `type` است؛ `stop_Price` برای `STOP_LIMIT` و `STOP_MARKET` مشروط و `client_id` اختیاری معرفی شده است. صفحه همچنین پاسخ HTTP `201` و حداکثر ۲۰ درخواست ثبت سفارش در هر ۱۰ ثانیه را ذکر می‌کند. این محدودیت فقط به همان صفحه/endpoint نسبت داده می‌شود. [SPOT-CREATE](https://developers.wallex.ir/docs/spot-create-order)

انواع `LIMIT`, `MARKET`, `STOP_LIMIT`, `STOP_MARKET` مستند شده‌اند. صفحه Market می‌گوید اجرا با بهترین قیمت موجود می‌تواند چند قیمت داشته باشد و اگر حجم از order book بیشتر باشد یا باعث جابه‌جایی ۲٪ قیمت آخرین معامله شود سفارش Market خودکار لغو می‌شود. قاعده گزارش‌شده را برای همه جفت‌ها/شرایط تعمیم ندهید؛ جزئیات فنی و applicability بیشتر نیازمند تأیید است. [SPOT-TYPES](https://developers.wallex.ir/docs/spot-types)

## وضعیت، اجرا و لغو

پاسخ سفارش شامل فیلدهایی مانند `active`, `clientOrderId`, `executedPercent`, `executedPrice`, `executedQty`, `executedSum`, `fee`, `fills`, `origQty`, `status`, `type`, `updated_at` است. صفحه لیست سفارش‌ها نمونه enumهای `NEW`, `FILLED`, `CANCELED` را می‌آورد، اما فهرست کامل حالات و transitionها را مشخص نمی‌کند. [SPOT-CREATE](https://developers.wallex.ir/docs/spot-create-order) · [SPOT-ORDERS](https://developers.wallex.ir/docs/spot-order-list)

صفحه prose برای لغو سفارش ناتمام `DELETE /v1/account/orders/{client_id}` را معرفی می‌کند؛ مرجع قدیمی `DELETE /v1/account/orders?clientOrderId=...` را دارد. generated page دیگری `DELETE //api.wallex.com/v1/account/orders` با body اجباری JSON شامل `clientOrderId` و header مستندشده `x-api-key` نشان می‌دهد. این host، route و شناسه متفاوت را با هم ادغام نکنید؛ رفتار runtime و قرارداد canonical نامعلوم است. لغو سفارش حساب‌تغییردهنده است و در این پروژه هرگز فراخوانی نمی‌شود. [SPOT-CANCEL](https://developers.wallex.ir/docs/spot-cancel-order) · [LEGACY-API](https://api-docs.wallex.ir/) · [MOD-GENERATED-DELETE-ACCOUNT-ORDERS](https://developers.wallex.ir/docs/generated/delete-account-orders) · [D-016](../research/discrepancies.md)

## ابهام‌های اجرایی

پوشش پرشدن جزئی، ترتیب eventها، idempotency در timeout، وضعیت‌های نهایی/غیرنهایی، reconcile بعد از قطع ارتباط، رفتار لغو هم‌زمان با fill، و جزئیات تطبیق میان `client_id` و `clientOrderId` هنوز نیاز به بررسی منابع اختصاصی دارد.
