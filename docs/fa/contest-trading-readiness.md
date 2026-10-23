# گزارش آمادگی معاملات مسابقه‌ای — Wallex Trading Agent

**تاریخ**: 2026-10-23 (UTC)
**شاخه**: `feat/contest-trading-readiness` (ساخته‌شده از `main`)
**SHA پایه**: `6cddedb0f1bf5ced78587266094440ccd504e4e5`
**حالت اجرا**: `OFFLINE` / `PAPER` (هیچ سفارش واقعی ارسال نشده است)

این گزارش فارسی‌محور است؛ شناسه‌های API انگلیسی بدون تغییر حفظ شده‌اند.

---

## 1. مخزن و شاخه

| آیتم | مقدار |
|---|---|
| شاخه پایه | `main` |
| SHA شاخه پایه | `6cddedb0f1bf5ced78587266094440ccd504e4e5` (مرج PR #27 در 2026-10-23T18:15:17Z) |
| شاخه کاری | `feat/contest-trading-readiness` |
| وضعیت CI پایه | ✅ هر دو run «Validate repository (Python 3.12)» روی PR #27 موفق |

CI روی `main` شامل: نصب وابستگی‌ها، `validate_sources.py`، `validate_doc_links.py`، `compileall`، کل مجموعه تست آفلاین، ساخت بسته (build)، و `git diff --check` است — همه موفق.

## 2. اتصال MCP (واقعی، این نشست)

| MCP | ابزار | نتیجه |
|---|---|---|
| Wallex MCP | `wallex_basic_get_markets` | ✅ ۲۰+ بازار بازگشت (USDTTMN، BTCTMN، ETHTMN، SOLTMN، …) |
| Wallex MCP | `wallex_basic_get_market_depth` | ✅ سفارش‌بوک ۵۰ سطح ask/bid (USDTTMN و BTCTMN و SOLTMN) |
| Wallex MCP | `wallex_basic_candle_history` | ✅ شمع‌های ۱ ساعته USDTTMN (تایم‌استمپ Unix) |
| Wallex MCP | `wallex_basic_get_latest_trades` | ✅ آخرین معاملات با `isBuyOrder` و ISO-8601 |
| CoinGecko MCP | `simple.price.get` | ✅ قیمت ۶ ارز + تغییر ۲۴ساعته + market cap + `last_updated_at` |

هر دو MCP مستقل تأیید شدند؛ هیچ ابزار تغییردهنده‌ی وضعیت (سفارش، لغو، انتقال، برداشت) فراخوانده نشد.

## 3. قوانین رسمی مسابقه

- **وضعیت: UNVERIFIED (تأییدنشده از منبع رسمی).**
- تنظیمات `config/challenge/wallex_hackathon_policy.json` برچسب `PROVIDED_BY_CHALLENGE_BRIEF` دارد؛ `official_start_utc` و `official_cutoff_utc` برابر `null` هستند.
- مبلغ `initial_capital_tmn: "5000000"` صرفاً مبلغ گزارش‌شده است، **نه اثبات تأمین سرمایه یا مجوز معامله**. `initial_capital_semantics` این را صریح می‌گوید.
- لیست جفت‌های غیرمجاز (deny-list) در مخزن وجود دارد، اما **فقدان در deny-list هرگز مجوز نیست** (absence is never authorization).
- استراتژی، بازار، کارمزد، یا آستانه ریسک از طرف سیستم انتخاب نشده است.

## 4. وضعیت تازگی داده

| نماد | آخرین مشاهده (UTC) | منبع |
|---|---|---|
| USDTTMN | 2026-10-23T17:47–17:49Z | Wallex MCP (depth/trades/candles) |
| BTCTMN | 2026-10-23T17:49:56Z | Wallex MCP (trades/depth) |
| ETHTMN | 2026-10-23T17:49:04Z | Wallex MCP (trades) |
| SOLTMN | 2026-10-23T17:49:56Z | Wallex MCP (depth) |
| BTC/ETH/SOL/BNB/XRP/USDT | `last_updated_at` 1792777633–1792777646 | CoinGecko MCP |

شکاف واقعی ۱۰ ساعته در سری شمع USDTTMN مشاهده شد (که در پاسخ زنده‌ی API هم وجود دارد) — ابزار data-audit آن را به‌درستی REVIEW/گپ علامت زد و شبیه‌سازی فقط با زیرمجموعه‌ی پیوسته ادامه یافت.

## 5. تست‌ها (اجرای محلی در sandbox)

دستور پایه: `PYTHONPATH=src:. python3 -m pytest tests/ -q`

| ناحیه | فایل تست | نتیجه |
|---|---|---|
| MCP سرور مستقل | `test_wallex_mcp.py` | ✅ ۱۸ تست |
| سیاست اجرا (Feature 008) | `test_execution_policy.py` | ✅ ۲۱ تست |
| کلاینت live spot | `test_live_spot.py` | ✅ ۱۵ تست |
| کارگزار کاغذی | `test_paper_trading.py` | ✅ ۱۷ تست |
| کیفیت داده | `test_data_quality.py` | ✅ ۹ تست |
| بک‌تست | `test_backtest.py` | ✅ ۵ تست |
| عامل مستقل (shadow) | `test_autonomous_agent.py` | ✅ ۶ تست |
| CoinGecko MCP | `test_coingecko_mcp.py` | ✅ ۱۶ تست |

**مجموع: ۱۰۷ تست موفق / ۰ شکست** (پس از `compileall` و نصب وابستگی‌ها با mirror-PyPI).
نتیجه‌ی کل CI روی `main` نیز مستقل تأیید شده است.

## 6. اجرای کاغذی با داده‌ی واقعی (PAPER)

- **داده**: ۱۰ شمع ساعتی واقعی USDTTMN از Wallex MCP (2026-10-23T08:00Z تا 17:00Z)، تأیید کیفیت = `OK` (۰ خطا، ۰ گپ).
- **دستور**: `python3 -m wallex_agent.paper_candle_cli --input ... --symbol USDTTMN --initial-cash 5000000 --fee-bps 5 --slippage-bps 5 --max-order-notional 1000000 --lookback-bars 3 --entry-return-bps 20 --exit-return-bps 0 --audit-input-data --expected-interval-seconds 3600`
- **استراتژی (فقط برای اعتبارسنجی فنی)**: `long-only-threshold-momentum-next-open-v1` — سیگنال از closeهای قبل؛ اجرای مجازی در open شمع بعد.
- **نتیجه**: ۶ سیگنال، همه HOLD (مومنتوم ۳ساعته منفی: از ۴.۶- تا ۱۴۳- bps؛ زیر آستانه‌ی ۲۰+ bps). **۰ پر شدن، ۰ سفارش**؛ موجودی مجازی ثابت: **۵,۰۰۰,۰۰۰ TMN**؛ `order_submission_attempted: false`؛ `live_trading_enabled: false`.
- این صفر-سفارش نتیجه‌ی واقعی بازار نزولی است، نه پرش از مرحله؛ هیچ پر شدن جعلی ثبت نشد.

## 7. مفروضات استراتژی و محدودیت‌ها

- استراتژی بالا صرفاً «خط پایه برای اعتبارسنجی تکنیکال» است؛ **توصیه‌ی سودآوری نیست**.
- بدون مدل عمق دفتر، صف، پر شدن جزئی، یا اجرای درون شمعی.
- موجودی باز در پایان با قیمت آخر مارک می‌شود، نه به‌صورت تسویه‌ی اجباری.

## 8. کارمزد و لغزش

- مقادیر فقط **مفروضات شبیه‌سازی برچسب‌گذاری‌شده**: fee=5 bps و slippage=5 bps در هر طرف.
- `wallex_hackathon_policy.json` → `financial_assumptions.trading_fee_tier_or_rates: null` و `spread_cost: null`؛ **کارمزد رسمی تأییدنشده است**.

## 9. وضعیت سیاست ریسک

- `risk_limits` در policy فعلاً **همه `null`** و `configuration_status: REQUIRES_USER_AND_ORGANIZER_REVIEW`.
- `src/wallex_mcp/execution_policy.py` هیچ پیش‌فرضی نمی‌سازد: `RiskLimits.from_mapping` بدون هر ۹ حد صریح خطا می‌دهد و `validate_order_intent` بدون داده‌ی تازه، تأیید بازار، تطبیق حساب، و allowlist صریح، هر دستوری را مسدود می‌کند. ✅ fail-closed تأیید شد.

## 10. حالت اجرا

`OFFLINE` / `PAPER` — تمام مسیرهای اجرا در مخزن (shadow runner, backtest CLI, paper CLI) هیچ خروجی شبکه‌ای معاملاتی ندارند؛ `dispatch_order_intent` فقط «نیت» ثبت می‌کند و `submit_order` هرگز فراخوانده نمی‌شود.

## 11. آیا سفارش واقعی ارسال شد؟

**خیر (NO).** هیچ ابزار تغییردهنده‌ی وضعیت فراخوانده نشد؛ هیچ کلید API، موجودی خصوصی، یا داده‌ی حساب خوانده یا نمایش داده نشد.

## 12. گلوگاه‌های باقی‌مانده (blockers) و شواهد لازم

1. **قوانین رسمی مسابقه**: URL رسمی + زمان شروع/پایان تأییدشده — نیازمند تأیید برگزارکننده.
2. **universe بازار مجاز**: allowlist صریح جفت‌ها (فقدان در deny-list کافی نیست).
3. **مبلغ واقعی سرمایه و مالکیت حساب**: تأیید مستقل ۵,۰۰۰,۰۰۰ TMN.
4. **کارمزد/لغزش/حداقل نوتینال رسمی**: نرخ‌های تأییدشده.
5. **حدود ریسک عددی**: مقادیر صریح تاییدشده در code (فعلاً null).
6. **قرارداد ابزار/میانجی سفارش Smart98 یا Wallex**: نام ابزار + contract تأییدشده (الان `NOT IMPLEMENTED — official contract not verified`).
7. **کلید API با حداقل مجوزها**: فقط در محیط محافظت‌شده (GitHub Environment `wallex-readonly`)؛ هرگز در مخزن/لاگ.

## 13. دستورهای راه‌اندازی و توقف حالت تأییدشده

- مشاهده‌ی shadow: `python3 -m wallex_agent.runner --quote-asset TMN --once` (یا بدون `--once` برای دوره‌ای؛ توقف با Ctrl+C).
- بک‌تست آفلاین: `python3 -m wallex_agent.backtest_cli --input <candles.jsonl> --initial-cash 5000000 --fee-bps-per-side 5 --slippage-bps-per-side 5` (تزریق هزینه‌ی صریح لازم است).
- شبیه‌سازی کاغذی (شمع): `python3 -m wallex_agent.paper_candle_cli --input <candles.jsonl> --symbol USDTTMN --initial-cash 5000000 --max-order-notional 1000000 --audit-input-data --expected-interval-seconds 3600`
- کارگزار کاغذی JSONL: `python3 -m wallex_agent.paper_trading_cli --input <events.jsonl> --initial-cash 5000000 --max-order-notional 1000000`
- **Live**: خاموش مگر در صورت فعال‌سازی صریح؛ هیچ دستوری برای live ارائه نمی‌شود تا گلوگاه‌های بالا رفع شوند.

## 14. بازیابی و توقف اضطراری (kill-switch)

- هر خطای داده/اتصال/وضعیت نامعلوم سفارش → ثبت به‌عنوان `OrderOutcomeUnknown` و «reconcile قبل از هر retry»؛ **هرگز auto-retry برای POST**.
- متغیرهای صریحی که باید به‌درستی تنظیم شوند و هرگز در مخزن قرار نگیرند:
  `WALLEX_API_KEY`، `WALLEX_LIVE_TRADING_ACK=I_UNDERSTAND_REAL_ORDERS`، `WALLEX_LIVE_ALLOWED_SYMBOLS`، `WALLEX_LIVE_QUOTE_ASSET`، `WALLEX_LIVE_MAX_ORDER_NOTIONAL`.
- توقف اضطراری: فعال‌کردن `emergency_stop_active=true` در policy (طبق `LiveActivationPolicy` تمام سفارش‌ها را می‌بندد)، توقف فرآیند runner، و قطع دسترسی کلید.
- بازیابی: بازتأیید موجودی/سفارش‌های باز با `get_order(client_id)` و خروجی‌های audit پیش از هر اقدام جدید.

## 15. جمع‌بندی

- ✅ جمع‌آوری داده‌ی واقعی (Wallex + CoinGecko) و ذخیره/audit شمع.
- ✅ پاس کامل ۱۰۷ تست آفلاین + CI سبز روی main.
- ✅ اجرای کاغذی انتها-به-انتها با داده‌ی واقعی (۰ پر شدن صادقانه در بازار نزولی).
- ⛔ فعال‌سازی live و مجوز بازار رسمی: **BLOCKED** — شواهد گلوگاه‌های بالا موردنیاز است.