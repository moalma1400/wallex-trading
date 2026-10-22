# پرسش‌های حل‌نشده

این فهرست خروجی research pass است؛ پاسخ به پرسش‌های سیاستی/حسابی را از کاربر یا مرجع رسمی بگیرید، نه از حدس. پرسش‌های ثبت‌شده برای کاربر به معنی پیش‌نیاز این feature مستنداتی نیستند.

## برای تکمیل مستندات رسمی

1. برای ۵۱ صفحه sitemap که وضعیت `not_started` دارند، محتوای واقعی هر صفحه، endpointها، payloadها، permissions، enums، rate limits، schemaهای Swagger و ارجاعاتش چیست؟ (فهرست کامل در ماتریس؛ شمارش snapshot رسمی در 2026-10-21)
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

13. منبع OFAC رسمی اعلام می‌کند Wallex در ۲ ژوئن ۲۰۲۶ designated شده و FAQ 1257 می‌گوید اشخاص غیرآمریکایی ممکن است در صورت معامله با آن با ریسک تحریم مواجه شوند. این پروژه قوانین فرانسه/اتحادیه اروپا یا هر حوزه قضایی مرتبط، وضعیت شخصی/حقوقی کاربر، بانک/پرداخت‌گر، یا مجاز بودن هر فعالیت را بررسی نکرده است؛ موقعیت تقریبی کاربر جای بررسی شخص/نهاد و شرایط واقعی را نمی‌گیرد. قبل از هرگونه استفاده، بررسی مستقل و به‌روز با مشاور حقوقی/انطباق لازم است. [US-TREASURY-WALLEX-DESIGNATION](https://home.treasury.gov/news/press-releases/sb0519) · [OFAC-FAQ-1257](https://ofac.treasury.gov/faqs/1257)

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
18. Smart98 is the intended organizational AI Agent platform and mandatory mediator per user project context, but what versioned contract, transport, auth, tool catalog, schemas, error/timeouts/logging, and Wallex MCP/API compatibility are actually supported? A user message dated 2026-10-22 reports an operator-supplied evidence report describing live read-only public-market-data invocations, but the report body is absent; only the aggregate operator claim is recorded. The repository contains an injected parser/provider seam in `src/mcp_adapter/`, not a verified Smart98 transport. See the dated [Feature 005 evidence review](feature-005-smart98-evidence-review-2026-10-22.md) and checklist below.
19. Which UDF-history field requiredness and resolution set is canonical? The basic page marks fields Optional; generated `candle-history` and the legacy reference mark them Required, and the modern pages show different resolution examples. See `D-008` and `D-015`; no runtime call is permitted.
20. Does the sitemap-listed `/docs/weekly` have a replacement or is it retired? The page reader returned a localized not-found body without an HTTP status; the source is `blocked`/`inaccessible` and no reason is inferred.


### Smart98-mediated Wallex access — evidence needed (tool-level findings remain `UNKNOWN`)

The user's project context identifies Smart98 as the intended organizational AI Agent platform and mandatory mediator; that is a requirement, not technical capability evidence. No Smart98 product documentation or runtime contract exists in this checkout. The Arena connector lookup returned `unsupported`, which does not establish that Smart98 itself is unavailable. A 2026-10-22 user message reports that an operator supplied a Smart98-generated report describing live, read-only public Wallex market-data invocations. The report body/attachment is unavailable; its [intake note](user-sources/smart98_mcp_report_notice_2026-10-22.md) preserves only the aggregate claim. Arena did not invoke or independently verify any tool. The original report's exact `UNKNOWN`, `UNVERIFIED`, `PARTIAL`, and `NOT_AVAILABLE` findings cannot be transcribed until its body is supplied.

1. What is the canonical Smart98 product/version and owner-approved documentation location? What environment, supported deployment model, network/egress boundary, and service identity apply? The source/version is `UNKNOWN` in the available notice.
2. Which MCP transports and versions does Smart98 support? How are MCP servers registered, reviewed, enabled, versioned, disabled, and isolated? What demonstrates compatibility with a specifically identified Wallex MCP release?
3. What exact tool identifiers and versioned input/output schemas were invoked, with sanitized full request/response or exact error? No specific Spot market-metadata, candle, depth, trade, or ticker capability is individually evidenced by the available notice.
4. How are tools discovered and allow-listed for a particular agent/workflow? Can the platform enforce separate least-privilege groups for public market-data reads, account-sensitive reads, and state-changing tools? Per-tool permissions and side effects remain `UNVERIFIED`.
5. What exact authentication/delegation model is used? Who holds Wallex credentials, how are they scoped/rotated/revoked, and what proof establishes that secrets never enter model context, prompts, repository, tool output, or logs?
6. What are the exact Smart98/upstream rate limits, timeout budgets, retry, cancellation, partial-output, and error-propagation semantics? The user says the report notes these gaps, but the original wording and any values/statuses are unavailable.
7. What pagination, truncation, streaming/WebSocket, ordering, replay, and reconnect behavior is supported? The report's exact `NOT_AVAILABLE` versus `UNKNOWN` findings are not supplied; the historical capability matrix is not current proof.
8. What are the candle input time units, inclusive/exclusive range bounds, resolution set, maximum history, gaps/partial-candle behavior, pagination, and source-event timestamp semantics? These remain `UNKNOWN`.
9. Which request/response metadata is logged (actor, tool, version, timestamps, provenance, policy decision, result, errors)? What retention, redaction, access, and audit-export controls apply?
10. Does Smart98 officially approve and support the exact Wallex API/MCP integration and read-only tool scopes, and what separate non-production test plan verifies it without private or state-changing actions? No production probe or new MCP configuration is authorized here.

Until the original sanitized report and authoritative contracts are supplied and reviewed, transport compatibility, tool discovery, schemas, authentication, error propagation, timeouts, logging, permissions, rate limits, pagination/streaming, candle range semantics, and Smart98-to-Wallex reachability remain `UNKNOWN` or `UNVERIFIED`. Direct Wallex application access is not an acceptable fallback.

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


## Feature 005 — Smart98-mediated public Spot market data (2026-10-22 status)

The bounded public, read-only Spot market-data scope is recorded in constitution v1.2.0 and `AGENTS.md`; it is **not** authorization for direct Wallex calls, private-account reads, new MCP setup, or state-changing actions. T003 is open/blocked pending the original Smart98 evidence report and authoritative source/version, schema, permission, and mediation evidence. The user-provided report notice supplies only an aggregate operator-reported invocation claim; Arena did not independently invoke the tools. T004 security/privacy/risk/compliance review and T005 architecture inventory are recorded in [the dated review](feature-005-smart98-evidence-review-2026-10-22.md); neither review passes unresolved permissions or legal gates.

1. What canonical Smart98 documentation and version define the mediation interface, transport, authentication/secret boundary, tool catalog/schemas, permissions, and error/timeout behavior?
2. Which exact tools are confirmed public/read-only Spot market data, and what source/version, exact input/output schemas, side effects, and per-tool permissions establish this? The current report body is missing.
3. What are the timestamp units/meaning, decimal representations, freshness/provenance fields, candle range/completeness/truncation/pagination semantics, depth/trade limits, streaming availability, rate limits, timeout/retry behavior, and exact `UNKNOWN`/`UNVERIFIED`/`PARTIAL`/`NOT_AVAILABLE` findings?
4. What current official organizer rules, competition window, dedicated-account permissions, current allowed Spot list, risk limits, reconciliation requirements, and explicit owner activation decision govern any future live workflow?
5. What current qualified jurisdiction-specific legal/compliance review is required for the relevant person/entity, exchange, counterparties, and payment rails? No legality or eligibility conclusion is inferred here.

**Current decision state:** public-market-data adapter implementation remains gated by T003–T006; the pre-existing parser/provider code is not proof that those gates passed. T004 and T005 reviews are recorded; T006–T008 remain open. T009's offline suite/validator run and T010's evidence/documentation updates are recorded in `tasks.md` and the dated review. Private reads, orders, cancellations, transfers, deposits, withdrawals, wallet actions, OTC execution, Margin, leverage, borrowing, shorts, derivatives, and direct Wallex calls remain prohibited. See [Feature 005 spec](../../specs/005-smart98-mediated-public-market-data/spec.md), [plan](../../specs/005-smart98-mediated-public-market-data/plan.md), [tasks](../../specs/005-smart98-mediated-public-market-data/tasks.md), and [T003–T005 review](feature-005-smart98-evidence-review-2026-10-22.md).
