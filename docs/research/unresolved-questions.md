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

## Credit-plan / Starcoach reconciliation — added 2026-10-21

The excerpt source `USER-WALLEX-CREDIT-PLAN-EXCERPT` is user-supplied and unverified; see [`wallex-credit-plan-reconciliation.md`](../knowledge-base/wallex-credit-plan-reconciliation.md). The underlying source was reported as Persian, but only an English bullet summary was supplied. Its exact URL, publication/retrieval date, eligible-market list, and readable account-permission table are unknown. Existing official sources support generic credit-account separation (`CREDIT-INTRO`) and a general 30-day plan with daily fee/warning/liquidation levels (`CREDIT-TYPES`), but not the exact excerpt amounts/claims or Starcoach applicability.

1. Is the Starcoach allocation implemented through the exact general credit plan in the excerpt, or a separate grant/product/account? What official URL/version and effective terms govern?
2. Is the 5,000,000-Toman amount credit principal, grant, or another allocation? Are principal, deficit, fee, or any other amount a team/member liability?
3. Does the plan fee apply during the three-day hackathon? If so, confirm exact rate, accrual base/day count, cap, stop/expiry rules, waivers, other fees, and settlement priority. The excerpt's 600,000/30-day example is not a challenge rate.
4. Do the plan warning and liquidation terms apply? Confirm threshold, valuation, sale mechanics/route, fees, residual asset handling, post-liquidation debt or return, and whether special hackathon terms supersede them.
5. Supply the readable original account-permission matrix, including account-specific trading/API/bot/deposit/withdrawal/transfer permissions.
6. Supply the exact effective Spot-market allow/deny list and explain how it relates to the separate 345-pair user-provided exclusion list. No market may be inferred from either list's absence.
7. Confirm level-one/new-account trading fee tier and current maker/taker values or hackathon exceptions.
8. Confirm sequence for expiry, early stop, Instant Sell, credit repayment, credit fee, tournament capital recovery, profit payout, remaining assets, final valuation and account zeroing.

Until authoritative, traceable hackathon-specific evidence resolves these questions, treat all such values/permissions as `UNKNOWN`; no credit-fee/liquidation/settlement model is implemented, and offline results must disclose that limitation.

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
18. Smart98 is the intended organizational AI Agent platform and mandatory mediator per user project context, but what versioned contract, transport, auth, tool catalog, schemas, error/timeouts/logging, and Wallex MCP/API compatibility are actually supported? See the expanded Smart98 evidence checklist below; no adapter or endpoint has been invented.
19. Which UDF-history field requiredness and resolution set is canonical? The basic page marks fields Optional; generated `candle-history` and the legacy reference mark them Required, and the modern pages show different resolution examples. See `D-008` and `D-015`; no runtime call is permitted.
20. Does the sitemap-listed `/docs/weekly` have a replacement or is it retired? The page reader returned a localized not-found body without an HTTP status; the source is `blocked`/`inaccessible` and no reason is inferred.


### Smart98-mediated Wallex access — evidence needed (all presently `UNKNOWN`)

The current user context identifies Smart98's role as an organizational AI Agent platform and mandatory mediation layer, but that is not a technical capability confirmation. No Smart98 documentation or runtime contract exists in this checkout; the Arena connector lookup returned `unsupported`, so this session could not inspect platform tools. Do not interpret that as evidence the platform itself is unavailable.

1. What is the canonical Smart98 product/version and owner-approved documentation location? What environment, supported deployment model, network/egress boundary, and service identity apply?
2. Which MCP transports and versions does Smart98 support? How are MCP servers registered, reviewed, enabled, versioned, disabled, and isolated? What demonstrates compatibility with a specifically identified Wallex MCP release?
3. How are tools discovered and allow-listed for a particular agent/workflow? Can the platform enforce separate least-privilege groups for public market-data reads, account-sensitive reads, and state-changing tools?
4. What exact authentication/delegation model is used? Who holds Wallex credentials, how are they scoped/rotated/revoked, and what proof establishes that secrets never enter model context, prompts, repository, tool output, or logs?
5. Where are tool descriptions and versioned input/output schemas documented? How are schema validation, provenance, untrusted output, sensitive-field redaction, and model-visible result shaping handled?
6. What are error, timeout, retry, cancellation, rate-limit, partial-output, and idempotency semantics? How do tool failures propagate to the agent and deterministic application without being misreported as successful data/actions?
7. Which request/response metadata is logged (actor, tool, version, timestamps, provenance, policy decision, result, errors)? What retention, redaction, access, and audit-export controls apply?
8. For Wallex MCP specifically: provide canonical publisher/repository/URL, release/version, source/license, transport, tool inventory, schemas, auth, permissions, side effects, upstream service, limits, and security/disclosure contact. No authoritative Wallex MCP source is registered today.
9. Does Smart98 officially approve and support the identified Wallex API/MCP integration, and exactly which **read-only market data** tool(s) may be exposed to shadow workflows? No access is allowed based only on an MCP/tool being listed or present.
10. What separate non-production certification/test plan can prove the exact Smart98-to-Wallex route while excluding account actions and production requests? This documentation task does not perform that test.

Until evidence is supplied and reviewed, transport compatibility, tool discovery, schemas, authentication, error propagation, timeouts, logging, permissions, and Smart98-to-Wallex reachability remain `UNKNOWN`. Direct Wallex application access is not an acceptable fallback.

## Wallex / Starcoach hackathon (Feature 004) — organizer confirmation required

These are separate from the official API documentation gaps above. The written attachment is user-provided evidence; do not infer answers from market-data docs.

1. What are the official challenge start, end/cutoff timestamps and timezone, and any pause/resume or late-order policy?
2. Is the attached disabled Spot-pair list the current version for this challenge account? What signed/versioned source and effective time govern future changes, and what exact market state/orderability fields should be trusted?
3. Confirm the 5,000,000-TMN allocation, account ownership, credit meaning (not leverage), no-withdrawal restriction, loss liability, profit payout, account-zeroing process, and eligibility/access terms.
4. Which public market-data and permitted challenge-account interfaces, authentication, order fields, rate limits, error/retry/idempotency, partial-fill and reconciliation semantics are specifically approved? What precision/minimum-order rules apply? No endpoint or field should be guessed.
5. What are applicable fee/commission schedules and allowed slippage/cost assumptions? What are the official freshness constraints for metadata/market data and any AI output?
6. Which final pre-cutoff inventory treatment is expected? Is a specific TMN conversion route permitted, executable before cutoff, and how are residual assets and official settlement valuation treated?
7. Confirm exact realized/unrealized P&L, fee, cutoff snapshot and final-value formula, approximate two-day settlement and zeroing mechanics.
8. Is the detailed 150/150 sub-rubric still only proposed? What is the final rubric, ranking method, tie-break and activity/volume interpretation?
9. Confirm submission repository, exact run/log artifacts, video duration/format and any AI disclosure/model replay requirements. What participant privacy handling is expected? This repository must not collect member PII.
10. Can the original audio or raw ASR transcript be supplied to verify the inline cleaned working transcript? The Persian transcript is now archived as `USER-WALLEX-HACKATHON-AUDIO-TRANSCRIPT`, but no audio binary is available; wording, speaker identity/affiliation, the 00:03:33-to-00:03:54 gap, prize amount(s), MCP claim, and demo consequences remain unverified.

Until traceable answers are supplied, cutoff, market currentness, API/account permissions, fees, risk thresholds, conversion routes and final scoring stay unresolved; related code remains fail-closed and live execution absent.


## Feature 005 — Smart98-mediated public Spot market data (proposal, 2026-10-22)

The owner authorized preparing a governance amendment proposal. This is not acceptance of the amendment and does not override the current offline-only constitution or AGENTS.md.

1. Which exact constitution and AGENTS.md amendment will be accepted, and who reviews/accepts it? Until accepted, the existing offline-only boundary remains binding.
2. What canonical Smart98 documentation and version define the supported mediation interface, transport, auth, tool catalog, tool schemas, permissions, error/timeout behavior, and secret isolation?
3. Which tools are confirmed strictly public/read-only? Tool names or marketing examples are insufficient; inspect schemas and side effects without invoking any write-capable tool.
4. What are the precise timestamp units, retrieval timestamps, candle completeness/truncation and pagination semantics, depth limits, recent-trade limits, symbol naming, and rate/error behavior?
5. What current, independent jurisdiction/compliance review is required before any real Wallex use? This proposal does not determine legality or eligibility.
6. Does the owner approve implementation after the governance and contract evidence gates pass? The present approval covers preparing this proposal only.

**Current decision state:** constitution amendment not accepted; AGENTS.md amendment not accepted; adapter implementation not authorized; network/runtime testing not authorized; all private and state-changing capabilities remain prohibited. See [Feature 005 spec](../../specs/005-smart98-mediated-public-market-data/spec.md), [plan](../../specs/005-smart98-mediated-public-market-data/plan.md), [tasks](../../specs/005-smart98-mediated-public-market-data/tasks.md), and [governance amendment proposal](../../specs/005-smart98-mediated-public-market-data/governance-amendment-proposal.md).

## پرسش‌های WebSocket عمومی و ضبط‌کننده کندل — 2026-10-23

1. آیا یک اتصال زنده به `wss://api.wallex.ir/connection/websocket` امروز به `{"id": 2, "subscribe": {"channel": "public:<SYMBOL>@trade"}}` با شیء خالی پاسخ می‌دهد و سپس پیام `push` می‌فرستد؟ تلاش محدود ۲۰۲۶-۱۰-۲۳ از این محیط حتی در مرحله TLS شکست خورد (`ConnectionResetError`)، پس این پرسش `pending` است و هیچ سطحی از موفقیت زنده ادعا نمی‌شود. [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol) · [CANDLE-RECORDER](../agent/CANDLE-RECORDER.md)
2. فاصله واقعی تپش قلب `{}` و واکنش دقیق سرور به نبود پاسخ چیست؟ مستند ۲۵ ثانیه و ۸ ثانیه می‌گوید؛ مشاهده زنده در دست نیست. [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol)
3. آیا سرور v2 به ping سطح پروتکل وب‌سوکت هم پاسخ می‌دهد؟ ضبط‌کننده به همین دلیل ping وب‌سوکت نمی‌فرستد و به تپش مستند `{}` و آستانه ۶۰ ثانیه سکوت تکیه می‌کند؛ این آستانه یک انتخاب پیاده‌سازی است، نه عدد مستند.
4. آیا در عمل یک فریم انتقال چند پیام JSON جداشده با newline دارد؟ نمونه‌های رسمی split روی `\n` را نشان می‌دهند؛ این رفتار در اجرا مشاهده نشده است.
5. کدام نمادها اکنون فعال‌اند و آیا نمادی مانند `BTCUSDT` وجود دارد؟ ضبط‌کننده خطای مستند `102 unknown channel` را در manifest ثبت می‌کند، اما فهرست معتبر باید از صفحه رسمی بازارها تأیید شود؛ از نبود یک نماد در شواهد، هیچ استنتاجی درباره فعال‌بودن آن نمی‌شود. [MOD-SOCKET-TRADE](https://developers.wallex.ir/docs/socket-trade)
6. آیا نسخه ۱ (`wss://api.wallex.ir/ws`) هنوز برای کلاینت خام قابل استفاده است، با کدام framing پکت Socket.IO، و تا چه زمانی؟ صفحه رسمی فقط فریم منطقی را می‌گوید و handshake مشاهده‌شده Engine.IO است (`D-019`). [SOCKET-INTRO](https://developers.wallex.ir/docs/socket-intro) · [D-019](discrepancies.md)
7. آیا مسیرهای `/socket/trade` و `/socket` با redirect یا وضعیت HTTP مشخصی به صفحات `/docs/...` منتقل شده‌اند؟ خواننده صفحه هیچ وضعیت HTTP افشا نکرد (`D-020`). [LEGACY-SOCKET-TRADE-PATH](https://developers.wallex.ir/socket/trade) · [LEGACY-SOCKET-PATH](https://developers.wallex.ir/socket)
8. آیا سرور `subscribe` را پیش از پاسخ `connect` می‌پذیرد یا رد می‌کند؟ صفحه رسمی ترتیب را گام‌به‌گام می‌نویسد اما نمونه‌ی کامل خودش هر دو فریم را پشت‌سرهم و بدون انتظار می‌فرستد (`D-023`)؛ ضبط‌کننده اکنون محافظه‌کارانه منتظر پاسخ معتبر `connect` می‌ماند. تفاوت رفتاری دو حالت فقط با مشاهده‌ی زنده روشن می‌شود. [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol) · [D-023](discrepancies.md)
