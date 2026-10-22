## اتصال مستقل دادهٔ بازار (بدون Smart98 / Olive / MCP)

کد src/wallex_research/public_market_data.py یک مسیر Python مستقل برای snapshotهای عمومی فراهم می‌کند. این کد هیچ‌گاه به شبکه وصل نمی‌شود مگر آنکه --network صریحاً داده شود؛ تست‌ها از transport ساختگی استفاده می‌کنند.

### CoinGecko

    PYTHONPATH=src:. python -m wallex_research.public_market_data --network --out-dir reports/public-market-data coingecko-price --ids bitcoin,ethereum --vs usd

در صورت نیاز، Demo API key را در environment با نام COINGECKO_DEMO_API_KEY بدهید؛ کلید در URL یا فایل snapshot نوشته نمی‌شود. سهمیه و شرایط پلن API را رعایت کنید.

### Wallex

اسناد رسمی فعلی در [دفتر اختلاف‌ها](../research/discrepancies.md) اختلاف‌هایی درباره host، مسیر market list و مشخصات احراز هویت نشان می‌دهند. به همین دلیل کد عمداً host/path را حدس نمی‌زند. ابتدا قرارداد دقیق را بررسی و سپس تنظیم کنید:

    export WALLEX_API_BASE_URL="https://<verified-host>"
    export WALLEX_MARKETS_PATH="<verified-relative-path>"
    PYTHONPATH=src:. python -m wallex_research.public_market_data --network wallex-markets

مقادیر داخل <...> جای‌نگهدار هستند. تا وقتی مسیر تأیید و اجرای دستی انجام نشده، اتصال زندهٔ Wallex تأییدشده نیست. این پیاده‌سازی فقط GET خواندنی دارد و endpointهای حساب، سفارش، انتقال یا برداشت ندارد.

### GitHub Actions

Workflow در .github/workflows/public-market-data.yml هر دو ساعت زمان‌بندی شده، ولی تنها وقتی اجرا می‌شود که Repository Variable با نام ENABLE_PUBLIC_MARKET_DATA=true باشد. Wallex علاوه بر آن به دو Variable بالا نیاز دارد؛ در غیر این صورت skip می‌شود و میزبان جایگزین حدس زده نمی‌شود. snapshotها به‌عنوان artifact نگهداری می‌شوند، نه commit در مخزن. زمان‌بندی تضمین نمی‌کند اجرا دقیقاً در دقیقهٔ مقرر آغاز شود.

تست آفلاین:

    PYTHONPATH=src:. python -m unittest discover -s tests -p 'test_public_market_data.py' -v
