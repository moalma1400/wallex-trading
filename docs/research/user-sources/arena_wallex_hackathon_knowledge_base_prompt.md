# Arena Task: Add the Wallex Agentic AI Hackathon Rules to `wallex-trading` Knowledge Base

## Role and objective

Work in the existing repository `https://github.com/moalma1400/wallex-trading`. This is a **spot-only algorithmic trading project for the Wallex / Starcoach Agentic AI hackathon**, not a bug-bounty project and not a long-term investment portfolio. Add the complete challenge rules below to the repository as a structured, searchable, testable Knowledge Base and propagate the rules into relevant contracts, configuration, tests, skills, risk controls, backtesting/shadow-testing workflows, and operator documentation.

This is an implementation task, not just a request to write a summary. Inspect the actual repository and existing Spec Kit / Feature 001 / Feature 002 work before changing anything. Continue the current existing PR/branch if it is still the intended branch. **Do not create a new repository or PR, do not merge the PR, do not push to `main`, do not change repository visibility, and do not bypass permissions.** First report the actual branch, HEAD SHA, worktree status, and open-PR context available to you. Preserve unrelated changes.

The previously reported Feature 002 baseline was commit `357c0b51ab7bbdc0f6ef7525aafe38bfe9914edd` on existing PR #1, but verify the real repository state instead of assuming it is still current.

## Mandatory operating constraints

1. **Spot only; no leverage.** No margin, borrowing, leveraged products, short selling, derivatives, futures, or credit/leverage multipliers. The challenge may call the provisioned account a “trading-credit challenge account”; that does not authorize leverage. The engine must model ordinary spot inventory and cash only.
2. Do not use manual trading to generate evaluated performance. The algorithm must decide and submit all assessed orders. Manual actions may be used only for non-trading administration and must never be represented as algorithmic performance.
3. Do not implement or enable withdrawals, transfers, deposits, or any fund movement. Do not try to bypass the challenge account's disabled-withdrawal restriction.
4. Do not perform self-trading, coordinated intra-team trades, wash trading, artificial volume generation, market manipulation, or trading in excluded pairs.
5. Do not make authenticated/private-account requests or submit live orders as part of this repository change. No API keys, passwords, session cookies, personal identity data, or real account/order data in source control, logs, fixtures, CI, or reports.
6. Keep network trading **disabled by default and fail-closed**. This change is Knowledge Base + offline implementation/tests. No live Wallex requests are required to complete it. Public-document inspection is permitted only if available in this environment and within the existing workflow; do not send orders.
7. Do not invent Wallex endpoint paths, fields, error semantics, rate limits, fees, trading rules, AI requirements, or challenge terms. Tag statements as `PROVIDED_BY_CHALLENGE_BRIEF`, `OFFICIAL_SOURCE_VERIFIED`, `INFERRED`, `UNRESOLVED`, or `REQUIRES_ORGANIZER_CONFIRMATION`. Keep legacy docs separate from current docs.
8. Do not claim a strategy is profitable from synthetic or historical backtest results alone. Optimize for measurable, repeatable, risk-controlled behavior rather than trade volume or a lucky single trade.
9. Do not store team-member phone numbers, national IDs, dates of birth, or other personal information in this repo. The brief says organizers should provide participant data to Wallex to help detect related accounts; treat that as an organizer-side privacy/compliance process, not an instruction to collect or commit PII.
10. If the uploaded audio file is available in your environment, inspect/transcribe it with tools that are actually available and reconcile it with the written brief below. If it is not accessible or transcription is not supported, clearly mark audio review as incomplete; do not claim to have reviewed it. The embedded written brief is the primary source for this task.

## Required Knowledge Base deliverables

Create or update, using existing repo conventions wherever possible:

- `docs/knowledge-base/wallex-agentic-ai-hackathon.md`: authoritative internal summary of challenge rules, scoring rubric, timeline, capital, settlement, required submissions, operational constraints, and evidence/provenance.
- `docs/knowledge-base/wallex-hackathon-market-restrictions.md`: human-readable market restrictions and how to maintain/check them.
- A machine-readable canonical disabled-market list under the project's existing config/data conventions, e.g. `config/challenge/wallex_disabled_spot_pairs.json` (do not create duplicate sources of truth). Normalize each pair to uppercase `BASE/QUOTE`, validate syntax, sort deterministically, deduplicate for runtime use, and retain a raw-source appendix/file that preserves the supplied list verbatim for audit. Report duplicate entries rather than silently losing that evidence.
- A small policy/config model for challenge mode: `spot_only=true`, `leverage_enabled=false`, `margin_enabled=false`, `short_selling_enabled=false`, `withdrawals_enabled=false`, `manual_trading_counts=false`, `live_trading_enabled_by_default=false`, `require_algorithmic_decision_log=true`, `require_end_state_tmn=true` (or equivalent names consistent with the existing architecture).
- Tests that fail closed on disabled markets, malformed pairs, unknown market state, attempts to use non-spot/leverage/short/margin modes, and unsafe end-of-challenge inventory.
- Update existing project overview, architecture, risk docs, quickstart, roadmap, Persian Knowledge Base if present, source register, skills, Feature spec/plan/tasks/checklists, and relevant agent instructions without duplicating the entire detailed challenge text in every file. Link to the canonical Knowledge Base page instead.
- A practical judge/reproducibility guide and demo-video checklist.
- A source/provenance entry for the user-provided challenge brief. If a public official source is available, cite and record its canonical URL, retrieval date, title, and status; do not silently present user-supplied text as independently verified official policy.

Do not blindly create new files when an equivalent page already exists. Inspect conventions, consolidate duplicate knowledge bases, and avoid conflicting sources of truth. Use the existing Spec Kit workflow and add/update the next feature specification/plan/tasks/checklist as appropriate.

## Challenge facts that must be preserved

### Purpose and duration

- The challenge is part of the Starcoach Agentic AI hackathon with Wallex.
- Each participating team has three days to develop, run, and evaluate its algorithm.
- The system must receive market data, analyze it, identify trading opportunities under a defined strategy, make buy/sell decisions algorithmically, and automatically submit orders through Wallex in the challenge environment.
- UI/UX is not a primary evaluation criterion. The engine, algorithm logic, trading outcomes, risk control, speed/stability, repeatability, and technical verifiability matter more.
- All scored trades must be algorithmic; manual trades do not count as valid challenge performance.
- Every trade needs a durable decision log explaining the signal/evidence and why the algorithm chose to buy, sell, or hold.

### Capital and challenge account

- Wallex allocates a dedicated challenge account per team, funded with **5,000,000 toman** for the challenge. The account is separate from members' personal assets and cannot withdraw funds.
- The starting capital belongs to Wallex. Teams are not required to reimburse the loss of this allocated capital. After judging, if the account's final value is higher than the original capital, original capital is returned to Wallex and the net profit is paid to the team's nominated Wallex account. For negative results, Wallex recovers only the remaining account assets; the team does not owe the shortfall. After final settlement, the challenge account is zeroed.
- The brief gives illustrative settlement examples using 2,000,000 toman as a teaching example; those examples do not override the challenge's 5,000,000-toman baseline.
- Settlement is expected about two days after the three-day challenge, subject to judging approval.
- Do not assume or code a right to withdraw, transfer, use the funds outside the contest, or treat the credit account as leverage.

### Return calculation and final asset state

The stated net return formula is:

`net_return_percent = ((final_account_value_toman - 5_000_000) / 5_000_000) * 100`

The evaluation considers realized trading P&L, trading fees, residual assets, and potentially unrealized P&L on open positions. However, the brief explicitly emphasizes that the strategy/system should be evaluated on **realized result in toman**, not on ending with coin inventory whose value may move after the contest. Therefore:

- Implement a configurable pre-deadline liquidation/settlement procedure and an end-state validator.
- Before the official end time, close open spot positions and convert any non-TMN residual balances to TMN only if the conversion route is documented, allowed, and executable with the remaining time and risk budget.
- Never fabricate a conversion route or silently value an unliquidated token at a stale price. If residual balances cannot safely be converted, flag the run as not settlement-ready and record a transparent valuation caveat.
- Include fees and slippage in the accounting. Use decimal-safe monetary arithmetic. Store timezone-aware timestamps and normalize internal event timestamps to UTC.
- Maintain separate realized P&L, unrealized P&L, fees, cash/TMN balance, non-TMN inventory, and total estimated account value. Clearly distinguish official challenge valuation from an internal estimate.
- Consider prioritizing TMN-quoted spot pairs for the initial challenge strategy because they simplify realizing the end-state in toman. USDT-quoted pairs must not be enabled unless the system validates a permitted, documented path for converting residual value back to TMN before the deadline.

### Markets and prohibited behavior

- Only markets permitted for the challenge credit account may be traded. The exact disabled pair list from the supplied brief is included below.
- At runtime, a pair is tradable only when all gates pass: it is a valid spot pair; it is not in the disabled list; the exchange/challenge market metadata confirms it is active and orderable; the strategy allows it; and risk limits allow the proposed order. A pair's absence from the disabled list alone is not proof of runtime availability.
- Build a deterministic market eligibility function, with clear reasons for rejection. Fail closed on unknown, missing, stale, or contradictory market state.
- Explicitly prohibit self-trading, coordinated intra-team trading intended to distort performance, wash trading, artificial volumes, market manipulation, and manual trading claimed as algorithm performance.
- Do not use trading volume alone as a success metric. No unnecessary orders just to look active.

### Backtesting and shadow testing

- Backtesting on historical data and shadow testing on live market observations without submitting real orders are encouraged and can contribute to technical judging.
- Preserve the existing Feature 002 next-bar-open replay timing and explicit fees/costs unless a documented correctness defect is identified; any change must include a regression test and explain the methodological impact.
- Prevent look-ahead bias, data leakage, duplicate candles/trades, use of incomplete current candles as final values, and unrecorded changes of strategy/config.
- Shadow mode must never forward intents to the live order adapter. Its isolation must be automated and tested.
- Record data source, retrieval/fixture identity, symbol/interval, time range, schema version, strategy version, code commit, config hash, model/provider/model-version (if AI is involved), prompts or prompt-template version where appropriate, market-data freshness, fees, slippage assumptions, and outputs.
- Label all synthetic fixtures as synthetic. Do not claim real Wallex ingestion or execution unless those occurred and are evidenced.

### AI use and decision auditability

Technical judging awards points for meaningful use of AI; an `if/else` system relabeled as “AI” is insufficient. Design an AI component that materially influences market interpretation, regime classification, candidate ranking, signal quality, or buy/sell/hold decisions, while retaining strict deterministic safety gates.

- Use a structured, schema-validated AI output (for example: `BUY`, `SELL`, `HOLD`, confidence, horizon, supporting observable features, counter-evidence, and concise rationale). Choose the exact contract based on existing architecture and model capabilities.
- AI must not be able to override risk limits, market restrictions, position limits, account restrictions, the official end time, or spot-only policy.
- Avoid putting a slow/unbounded LLM call in a high-frequency order path. Define and document timeouts, stale-output rejection, fallback-to-HOLD behavior, rate/cost limits, and deterministic risk vetoes.
- Do not fabricate explanations after the trade. Persist the actual model output, exact feature snapshot/data references, model and prompt versions, action chosen, risk-gate verdict, order intent, exchange response/IDs if live execution is later separately authorized, and final fill/rejection state. Redact secrets and private user data.
- Create replayable decision logs so reviewers can reconstruct the data available at decision time and explain why the system acted. Record `HOLD` decisions and rejected order intents when material to auditability.
- Backtests must not silently call a current LLM for old historical bars as if it represented the model state at that time. Define explicit inference/replay rules, version metadata, and limits.

### Risk controls and safety architecture

The strategy must be separated from an independent risk engine. Implement and test configurable controls, at minimum:

- maximum notional per order; maximum exposure per asset; maximum total deployed capital; maximum open orders; maximum trade count/order rate where appropriate; minimum order value and precision validation from verified market metadata;
- maximum daily loss and maximum peak-to-trough drawdown stop; cooldown after repeated losses/errors; stale-market-data rejection; spread/slippage/liquidity checks; fee-aware entry/exit checks;
- limit on AI signal age and failure rate; model timeout/fallback-to-HOLD;
- duplicate-order/idempotency handling; reconciliation for order status and partial fills; bounded retry behavior only when retry semantics are safe and documented;
- circuit breaker on exchange/API errors, inconsistent balances, unexpected open orders, stale data, account value discrepancies, or disabled market detection;
- shutdown/emergency stop, end-of-challenge flattening/settlement checks, and a fail-closed mode.

Do not assume official limit values that were not supplied. Set conservative configurable defaults only when the code requires them, explain them as internal defaults, and do not market them as official Wallex requirements. Missing essential risk configuration must block order submission. Never use the full account balance in one order.

### Performance and judging rubric

The brief states a total of 300 points, split into financial/trading performance (150) and technical quality (150). The following detailed breakdown was described as a **proposed scoring rubric**; preserve that status and do not mislabel it as a confirmed official final rubric:

**Financial / trading performance — 150 points**
- Final net return percentage: 90 points; ranked among teams, and teams with negative returns receive no points for this item.
- Drawdown/loss control: 30 points; smaller drawdown is better.
- Algorithm activity: 15 points; regular and reasonable participation during the three-day period, not spam volume.
- Execution stability: 15 points; few errors, correct orders, no prolonged downtime.

**Technical quality / reproducibility — 150 points**
- Strategy logic and ability to explain buy/sell decisions: 40 points.
- Genuine, meaningful AI use: 35 points.
- Risk and capital management: 30 points.
- Re-execution, clean code, instructions, and judge reproducibility: 25 points.
- Backtesting and shadow testing evidence: 20 points.

Other metrics explicitly mentioned in the brief: number of trades, trading volume, average trade volume, final account value divided by initial capital (net return), and speed of algorithm execution. They supplement—not replace—net return, risk control, and technical confirmation. Positive returns alone are insufficient for winning if the algorithm cannot pass technical review.

### Required submission artifacts

- Source code in GitHub must exactly match the code/version used to generate challenge performance. Provide commit SHA and release/run identifier in the decision/trade logs.
- A Markdown document in the repo explaining architecture, core algorithm logic, how AI and Wallex tools are used, buy/sell conditions, capital/risk management, and how to rerun/evaluate the results.
- Per-trade/per-decision audit logs showing the observed signal and the reason for buy/sell/hold; include evidence references and risk-gate results.
- An approximately five-minute demo video is mandatory. It should show project operation/results and explain the outcome; source code does not need to be shown. Speaking narration is preferred, although a silent output demo is preferable to no video.
- Prepare a checklist so the same tagged commit, configuration, fixtures, model settings, and run commands can be used to reproduce results. A profit report without inspectable code and reproducible logic is insufficient.

## Disabled market pairs: raw supplied list

Treat every `BASE/QUOTE` pair below as disabled in the challenge credit account according to the user-provided brief. Preserve this exact input in the provenance/raw annex before canonicalizing it. Validate and report duplicates. The list is versioned challenge input, not a guarantee that all other pairs will necessarily be active at runtime.

```text
A/TMN
G/TMN
T/TMN
W/TMN
X/TMN
2Z/TMN
A/USDT
G/USDT
IO/TMN
OP/TMN
T/USDT
W/USDT
X/USDT
2Z/USDT
AMP/TMN
APT/TMN
ATH/TMN
BAT/TMN
BIO/TMN
C98/TMN
CAT/TMN
CHR/TMN
CRV/TMN
CVC/TMN
CVX/TMN
EDU/TMN
ENS/TMN
FET/TMN
FLR/TMN
GLM/TMN
GMT/TMN
GNO/TMN
GRT/TMN
HOT/TMN
ICP/TMN
ILV/TMN
INJ/TMN
IO/USDT
JST/TMN
JTO/TMN
JUP/TMN
KAS/TMN
KCS/TMN
KNC/TMN
LPT/TMN
LRC/TMN
MDT/TMN
MET/TMN
MMT/TMN
MNT/TMN
MTL/TMN
NFT/TMN
NMR/TMN
NOT/TMN
OMG/TMN
ONE/TMN
OP/USDT
PYR/TMN
QNT/TMN
RAY/TMN
REQ/TMN
RLC/TMN
RPL/TMN
RSR/TMN
SFP/TMN
SKL/TMN
SKY/TMN
SLP/TMN
SNX/TMN
SSV/TMN
TAO/TMN
TIA/TMN
TON/TMN
TRB/TMN
TWT/TMN
UMA/TMN
WIF/TMN
WIN/TMN
WOO/TMN
XMR/TMN
XPL/TMN
XTZ/TMN
YGG/TMN
ZEC/TMN
ZEN/TMN
ZIL/TMN
ZRO/TMN
ZRX/TMN
AERO/TMN
AEVO/TMN
AIOZ/TMN
ALGO/TMN
AMP/USDT
ANKR/TMN
API3/TMN
APT/USDT
ARKM/TMN
ATH/USDT
AVNT/TMN
BAND/TMN
BANK/TMN
BAT/USDT
BICO/TMN
BIO/USDT
BLUR/TMN
BOME/TMN
BONK/TMN
BTTC/TMN
C98/USDT
CATI/TMN
CAT/USDT
CELR/TMN
CGPT/TMN
CHR/USDT
COMP/TMN
CRV/USDT
CTSI/TMN
CVC/USDT
CVX/USDT
DASH/TMN
DEXE/TMN
DOGS/TMN
EDU/USDT
ENS/USDT
FET/USDT
FLOW/TMN
FLR/USDT
FRAX/TMN
GLM/USDT
GMT/USDT
GNO/USDT
GRAM/TMN
GRT/USDT
HOT/USDT
ICP/USDT
ILV/USDT
INJ/USDT
JST/USDT
JTO/USDT
JUP/USDT
KAIA/TMN
KAS/USDT
KCS/USDT
KITE/TMN
KMNO/TMN
KNC/USDT
LPT/USDT
LRC/USDT
MASK/TMN
MDT/USDT
MEME/TMN
MET/USDT
MMT/USDT
MNT/USDT
MOVE/TMN
MTL/USDT
NEAR/TMN
NEXO/TMN
NFT/USDT
NMR/USDT
NOT/USDT
OMG/USDT
ONDO/TMN
ONE/USDT
ORAI/TMN
ORCA/TMN
OSMO/TMN
PAXG/TMN
PNUT/TMN
POLS/TMN
PYR/USDT
PYTH/TMN
QNT/USDT
RAY/USDT
REQ/USDT
RLC/USDT
RPL/USDT
RSR/USDT
RUNE/TMN
SAFE/TMN
SFP/USDT
SKL/USDT
SKY/USDT
SLP/USDT
SNX/USDT
SOON/TMN
SSV/USDT
STRK/TMN
TAO/USDT
TIA/USDT
TON/USDT
TRAC/TMN
TRB/USDT
TWT/USDT
UMA/USDT
USDS/TMN
WBTC/TMN
WIF/USDT
WIN/USDT
WOO/USDT
XMR/USDT
XPL/USDT
XTZ/USDT
YFI/USDT
YGG/USDT
ZEC/USDT
ZEN/USDT
ZETA/TMN
ZIL/USDT
ZORA/TMN
ZRO/USDT
ZRX/USDT
AAPLX/TMN
AERO/USDT
AEVO/USDT
AIOZ/USDT
AIXBT/TMN
ALGO/USDT
AMZNX/TMN
ANKR/USDT
API3/USDT
ARKM/USDT
ASTER/TMN
AUDIO/TMN
AVNT/USDT
BAND/USDT
BANK/USDT
BICO/USDT
BLUR/USDT
BOME/USDT
BONK/USDT
BTTC/USDT
CATI/USDT
CELR/USDT
CGPT/USDT
COINX/TMN
COMP/USDT
CTSI/USDT
CYBER/TMN
DASH/USDT
DEXE/USDT
DOGS/USDT
ETHFI/TMN
FLOW/USDT
FRAX/USDT
GRAM/USDT
HMSTR/TMN
HOODX/TMN
JASMY/TMN
KAIA/USDT
KAITO/TMN
KITE/USDT
KMNO/USDT
LAYER/TMN
LINEA/TMN
MAGIC/TMN
MAJOR/TMN
MASK/USDT
MEME/USDT
METAX/TMN
METIS/TMN
MOVE/USDT
NEAR/USDT
NEIRO/TMN
NEXO/USDT
NVDAX/TMN
ONDO/USDT
ORAI/USDT
ORCA/USDT
OSMO/USDT
PAXG/USDT
PIXEL/TMN
PNUT/USDT
POLS/USDT
PROVE/TMN
PYTH/USDT
RUNE/USDT
SAFE/USDT
SENSO/TMN
SOON/USDT
STRK/USDT
SUPER/TMN
SYRUP/TMN
TOSHI/TMN
TRAC/USDT
TSLAX/TMN
TURBO/TMN
UNGON/TMN
USDS/USDT
WAVES/TMN
WBTC/USDT
ZETA/USDT
ZORA/USDT
AAPLX/USDT
AIXBT/USDT
AMZNX/USDT
ASTER/USDT
AUDIO/USDT
BANANA/TMN
COINX/USDT
CYBER/USDT
EIGEN/USDT
ETHFI/USDT
GIGGLE/TMN
HMSTR/USDT
HOODX/USDT
JASMY/USDT
KAITO/USDT
LAYER/USDT
LINEA/USDT
MAGIC/USDT
MAJOR/USDT
MEMEFI/TMN
METAX/USDT
METIS/USDT
MORPHO/TMN
NEIRO/USDT
NVDAX/USDT
PENDLE/TMN
PIXEL/USDT
PPLTON/TMN
PROVE/USDT
RENDER/TMN
SAHARA/TMN
SENSO/USDT
SUPER/USDT
SYRUP/USDT
TOSHI/USDT
TSLAX/USDT
TURBO/USDT
UNGON/USDT
WAVES/USDT
BANANA/USDT
GIGGLE/USDT
MEMEFI/USDT
MORPHO/USDT
PENDLE/USDT
PEOPLE/USDT
PPLTON/USDT
RENDER/USDT
SAHARA/USDT
VIRTUAL/TMN
VIRTUAL/USDT
1BBABYDOGE/TMN
1BBABYDOGE/USDT
```

## Required implementation behavior and testing

### Market eligibility

Create one source of truth for market restrictions. Implement something like `is_challenge_spot_market_allowed(pair, market_metadata, challenge_config, now)` (adapt the name to repo conventions). It must:

- normalize and validate `BASE/QUOTE` syntax without silently guessing symbols;
- reject pairs in the canonical disabled list;
- reject markets that are not explicitly confirmed active/orderable by current trusted metadata/config;
- reject non-spot instruments and any leverage/margin/borrow/short mode;
- reject stale or contradictory metadata and missing config;
- return a machine-readable decision with reason codes, not only a Boolean;
- be easy to test without network access.

Add tests covering at least: a known disabled pair, a valid pair explicitly enabled by fixtures, a pair missing from market metadata, malformed pairs, lowercase/whitespace normalization rules, duplicate list entries, unsupported quote asset, stale market metadata, leverage/margin/short mode attempts, and contradictory active/disabled status. Ensure tests do not infer that “not listed as disabled” automatically means tradable.

### Decision and trade audit logs

Define a versioned event schema for at least: market snapshot/feature references, AI analysis response, proposed signal, risk checks, order intent, order submission result when separately authorized, fill/partial fill/rejection, fees, balances, realized P&L, end-state liquidation, and run summary. Distinguish simulated/shadow events from actual exchange events. Use stable IDs, UTC timestamps, code/config/model versions, and references sufficient for replay. Prevent log entries from leaking keys, authentication headers, personal data, or secrets.

A judge must be able to answer for every executed order: what the system knew at decision time, what the AI contributed, what the strategy proposed, which risk checks passed/failed, why the order was allowed, what it filled, what fees it incurred, and its net P&L contribution.

### Backtest / shadow / live isolation

- Ensure Backtest and Shadow modes cannot submit actual orders by construction, not just via a UI flag.
- Keep the current live adapter disabled by default; require explicit future feature/authorization, challenge account configuration, safety review, and mode verification before any separate live phase. Do not implement or enable live execution as part of this task.
- Add an explicit dry-run mode and tests proving it never calls the order-submission adapter.
- Test that a strategy cannot bypass risk checks or the disabled-market list.
- Verify final TMN settlement readiness from positions/balances and the official cutoff configuration. If the official cutoff or required conversion route is unknown, fail closed and report the unresolved assumption.

### Repository checks

Run the project's actual checks and report exact commands and exit statuses. At minimum, where relevant:

- full unit test suite;
- static type/lint checks used by the repo;
- compile/import checks;
- source-register/schema validation;
- Markdown local-link/citation validation;
- disabled market list parser/schema tests, counts, and duplicate report;
- `git diff --check`;
- selfcheck/Spec Kit checks already used in the repo.

Do not merely state “tests pass.” Include captured evidence/log paths when the project has an artifact convention. Do not claim checks not run.

## Suggested order of work

1. Inspect repo/branch/PR, read Feature 001/002 specs and conventions, identify existing Knowledge Base/source register/skills/config/test locations.
2. Create provenance-backed challenge KB and persist the full disabled pair list in raw and canonical form. Parse the list mechanically; report total raw entries, unique pairs, duplicate pairs, and any malformed entries.
3. Add challenge config/market eligibility and spot-only mode contracts, tests, and risk/end-state checks.
4. Add structured decision-log contract, judge reproducibility guide, backtest/shadow/live isolation tests, and demo-video checklist.
5. Update Spec Kit artifacts, repo skills, architecture, roadmap, Persian documentation where present, and source register without creating redundant copies of the same policy.
6. Run and capture all checks; review diffs for accidental secrets, PII, fabricated docs, and conflicting sources.
7. Commit changes on the authorized existing PR branch only, if permitted. Do not merge. Push only to the existing branch if access permits and doing so follows the repo workflow.

## Final response required from Arena

Report:

- actual branch, before/after commit SHAs, worktree status, and existing PR link/state;
- exact created/changed files and why;
- whether the audio was actually accessible/transcribed;
- source/provenance and which rules still need official confirmation;
- raw disabled-pair count, unique count, duplicates, malformed entries, and test coverage;
- exact test/check commands with pass/fail and exit codes;
- any unresolved issue or caveat, especially official cutoff time, market metadata freshness, end-of-challenge TMN conversion routes, API semantics, fees, and final scoring-rubric status;
- explicit confirmation that no private-account request, live order, transfer, withdrawal, credential use, or network trading was performed;
- recommended next feature based on the actual project state.

## Source brief (facts supplied by the user)

The challenge description in this prompt is provided by the user and should be recorded as user-supplied challenge material until verified against official organizer/Wallex sources. Officially verify, if possible, the rules for the 5,000,000-toman capital, three-day duration, dedicated account and withdrawal restriction, settlement, eligible/disabled markets, return definition, submission/demo requirements, scoring rubric, and any official end time. Record conflicts and ask for organizer confirmation through documentation, not by inventing a resolution.
