# Wallex / Starcoach Agentic AI Hackathon — challenge knowledge base

**Repository scope:** Spot-only, offline policy and research support. **Current authority:** user-provided challenge attachment only. No organizer audio, official challenge page, account rules, market feed, or live order was accessed for this change. Every challenge-specific assertion below is tagged by evidence status; no user-supplied term is silently presented as an independently verified official rule.

| Evidence tag | Meaning here |
|---|---|
| `PROVIDED_BY_CHALLENGE_BRIEF` | Present in the user attachment; not independently verified. |
| `OFFICIAL_SOURCE_VERIFIED` | Independently retrieved exact official evidence. **None of the challenge terms has this status yet.** |
| `INFERRED` | Project interpretation, not an organizer rule. |
| `UNRESOLVED` | Missing or conflicting evidence; no value is assumed. |
| `REQUIRES_ORGANIZER_CONFIRMATION` | Blocked until an organizer confirms it in a traceable channel. |

The source record is `USER-WALLEX-HACKATHON-BRIEF` in the [source register](../research/source-register.yaml). The full attachment is preserved verbatim at [`docs/research/user-sources/arena_wallex_hackathon_knowledge_base_prompt.md`](../research/user-sources/arena_wallex_hackathon_knowledge_base_prompt.md), SHA-256 `da60ec1e3421f50990766b97ec611891f2d94a4226ffc64e301d343b0bebe144`. Its URL and UTC retrieval instant are `null`: this was an Arena attachment, not a public URL, and no exact UTC receive time was supplied. The list-only raw appendix is separately preserved byte-for-byte at `config/challenge/wallex_disabled_spot_pairs_raw.txt`; its SHA-256 is `48a9d12c5660929bf2044c30535864eb4f008d0580aa3e0cf75f5b528242eba0`. The two hashes cover distinct files.

## Purpose and challenge flow

- **`PROVIDED_BY_CHALLENGE_BRIEF`** — The challenge is described as part of the Starcoach Agentic AI hackathon with Wallex. Each team has three days to develop, run, and evaluate an algorithm.
- **`PROVIDED_BY_CHALLENGE_BRIEF`** — The intended system receives market data, analyses it, identifies opportunities under a defined strategy, decides buy/sell algorithmically, and automatically submits orders in the challenge environment. Every evaluated trade must be algorithmic; manual trades do not count as algorithmic performance.
- **`PROVIDED_BY_CHALLENGE_BRIEF`** — Each trade should have a durable decision explanation. UI/UX is secondary to engine/algorithm quality, outcomes, risk, speed/stability, repeatability, and technical verifiability.
- **`INFERRED`** — The repository implements safeguards and reproducibility primitives only. It does not select the strategy or make the system ready to connect to the challenge account.
- **`REQUIRES_ORGANIZER_CONFIRMATION`** — Exact start time, official cutoff, time zone, run/pause policy, account setup instructions, allowed data interfaces, and event timestamps have not been supplied in official retrievable material. The `official_start_utc` and `official_cutoff_utc` configuration values therefore remain `null`.

## Capital, account and settlement

- **`PROVIDED_BY_CHALLENGE_BRIEF`** — Initial allocation is **5,000,000 toman** for the challenge account, dedicated to a team and separate from member personal assets. Withdrawals are disabled.
- **`PROVIDED_BY_CHALLENGE_BRIEF`** — The brief describes the allocated capital as Wallex’s. It says teams do not reimburse allocated-capital losses; after judging, positive net value returns the original capital to Wallex and pays net profit to the nominated Wallex account; for negative results, Wallex recovers remaining account assets without a team shortfall payment. It says the challenge account is zeroed after final settlement.
- **`PROVIDED_BY_CHALLENGE_BRIEF`** — Settlement is expected approximately two days after the three-day challenge, subject to judging approval. The brief’s 2,000,000-toman examples are explanatory examples only; they do not replace the 5,000,000-toman baseline.
- **`REQUIRES_ORGANIZER_CONFIRMATION`** — These account-funding, ownership, loss, payout, zeroing, and timing terms need official confirmation before any challenge account is used.
- **`INFERRED`** — No deposit, withdrawal, transfer, or movement feature is implemented. The brief’s “trading-credit” label does not permit leverage, borrowing, credit multipliers, or margin.

### Return and end-state accounting

The brief supplies this formula (**`PROVIDED_BY_CHALLENGE_BRIEF`**):

```text
net_return_percent = ((final_account_value_toman - 5_000_000) / 5_000_000) * 100
```

It mentions realized P&L, fees, residual assets, and potentially unrealized P&L, while emphasizing realized result in toman rather than ending with coin inventory. The offline settlement validator keeps realized P&L, estimated unrealized P&L, fees, TMN cash and non-TMN inventory separate. It only reports final value/return when an official cutoff is verified, the snapshot is exactly at that cutoff, balances are reconciled, fees and unrealized P&L are known, and non-TMN holdings are zero. It never converts a residual token using a stale or invented price.

- **`UNRESOLVED`** — Official cutoff time, allowed conversion pairs/routes, settlement valuation policy, fees, and exact account-balance representation are absent.
- **`REQUIRES_ORGANIZER_CONFIRMATION`** — Any pre-deadline liquidation/settlement procedure and permitted TMN conversion route must be confirmed. Until then, settlement readiness fails closed.
- **`INFERRED`** — `TMN`-quoted markets are the only quote asset enabled in the current internal configuration. USDT quotes are blocked unless a separately verified, permitted, executable route valid through the official cutoff is supplied. No such route is currently evidenced.

## Markets and conduct rules

- **`PROVIDED_BY_CHALLENGE_BRIEF`** — Only challenge-permitted markets may be traded. The exact disabled pairs are retained in the raw appendix and canonical [disabled-pair JSON](../../config/challenge/wallex_disabled_spot_pairs.json).
- **`INFERRED`** — Eligibility requires valid Spot syntax, not disabled, explicitly active, orderable and enabled for the challenge in fresh, provenance-backed metadata; verified precision/minimum-order semantics; strategy approval; a supported quote/settlement path; and complete risk approval. Absence from the disabled list is **not** a tradability signal.
- **`PROVIDED_BY_CHALLENGE_BRIEF`** — Prohibited conduct includes self-trading, coordinated intra-team trades intended to distort performance, wash trading, artificial volume, market manipulation, and using excluded pairs. Manual trading must not be claimed as algorithmic performance.
- **`INFERRED`** — Do not optimize for volume or submit unnecessary orders. A market-data snapshot or synthetic fixture is not proof of current market access, orderability, or permission.
- **`REQUIRES_ORGANIZER_CONFIRMATION`** — Currentness/version/effective time of the disabled list and market eligibility state must be confirmed by the organizer. The checked-in 345-pair list is the user-provided version, not a live update.

### Disabled-pair data provenance

- Raw list: `config/challenge/wallex_disabled_spot_pairs_raw.txt` (345 supplied lines, order/case preserved).
- Machine-readable canonical list: `config/challenge/wallex_disabled_spot_pairs.json` (345 unique uppercase `BASE/QUOTE` pairs, ASCII alphanumeric syntax, lexically sorted).
- Parser result: **345 raw entries; 345 unique pairs; 0 duplicate pairs; 0 duplicate excess entries; 0 malformed entries.** The raw file is retained even when duplicates exist in any future source revision; duplicate counts are reported and a list containing duplicates is refused for runtime use until reconciled.
- Quotes present in the supplied list: `TMN`, `USDT`. Their presence does not authorize either quote. Current internal enabled quote is only `TMN` pending settlement-route validation for USDT.

## Backtest, shadow and live boundaries

- **`PROVIDED_BY_CHALLENGE_BRIEF`** — Historical backtesting and shadow testing on live observations without real orders are encouraged and can contribute to technical judging.
- **`INFERRED`** — Existing Feature 002 remains unchanged: close-observed intent is modelled at the next bar open with explicit cost inputs. No look-ahead, incomplete-candle finalization, data leakage, duplicate data, or unlogged configuration/strategy edits should be accepted.
- **`INFERRED`** — Backtest, shadow and dry-run dispatch are record-only and cannot invoke an order submitter. This feature returns a blocked result for `live`; no exchange adapter exists. A UI/config flag cannot activate live trading.
- **`REQUIRES_ORGANIZER_CONFIRMATION`** — Any future live challenge phase needs separate feature approval, current account and market contract, security/risk/compliance review, official account instructions, and explicit mode authorization. It is out of scope here.
- Synthetic fixtures remain clearly synthetic. Successful replay is not Wallex ingestion, a real fill, profitability evidence, or safety assurance.

## Decision auditability and AI

The brief says meaningful AI use earns technical consideration and says an `if/else` algorithm relabelled as AI is insufficient (**`PROVIDED_BY_CHALLENGE_BRIEF`**). It asks for structured, schema-validated output (example actions `BUY`/`SELL`/`HOLD`, confidence, horizon, observable supporting features, counter-evidence, and rationale), deterministic risk vetoes, timeouts, stale-output rejection, fallback-to-HOLD, and logging of the actual model output and context.

Current implementation provides only a **schema/logging contract**, not an AI model, provider, prompt, strategy, or signal generator. A real AI component must be a separate feature and must materially influence market interpretation/ranking/decision while remaining subordinate to market restrictions, risk, position limits, spot-only policy and cutoff. Backtests must not query a present-day model for old bars as though it represented historical model state.

Versioned events cover market/feature snapshots, AI analysis, signals, risk verdicts, order intents, simulated submission outcomes, fills/partial fills/rejections, fees, balances, realized and estimated unrealized P&L, end state, and run summary. Each record includes a stable content-derived event ID, UTC timestamp, run sequence, source references, code commit, config hash, strategy/model/prompt versions as applicable, and simulated/shadow/dry-run origin. Exchange-origin events are reserved and rejected by this feature. Secret/PII-like keys and common credential patterns are refused; do not persist raw secrets, personal information, or unreviewed prompts.

## Risk gates

The independent risk layer is strategy-neutral. It has configurable limits for per-order notional, per-asset exposure, total deployed capital, open orders, order rate, daily loss, peak drawdown, consecutive losses/errors, market-data age, AI-signal age, spread, slippage, liquidity utilization and total estimated fees/costs. It also requires reconciled account/orders, known fees, and inactive emergency stop.

- **`INFERRED`** — The order cap must be strictly below the 5,000,000-toman allocation; a single order can never consume the full baseline.
- **`UNRESOLVED`** — The brief supplies no official numeric risk values, fee schedule, order precision/minimums, data-age threshold, spread/slippage limit, order-rate cap, or AI timeout. Configuration entries are deliberately `null`; missing limits veto an order proposal. No placeholder numeric values are represented as Wallex requirements or recommendations.
- **`REQUIRES_ORGANIZER_CONFIRMATION`** — Organizers/operators must set and review every essential cap before even a separately authorized live phase.

## Performance and scoring

The brief states **300 total points**, split into **150 financial/trading** and **150 technical** (**`PROVIDED_BY_CHALLENGE_BRIEF`**). The detailed breakdown is explicitly described in the brief as a **proposed rubric**, not a verified final rubric:

| Category | Brief’s proposed allocation | Evidence status |
|---|---:|---|
| Net return, team-ranked; negative return earns zero for this item | 90 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |
| Drawdown/loss control | 30 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |
| Reasonable regular activity (not spam) | 15 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |
| Execution stability | 15 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |
| Explainable strategy logic | 40 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |
| Meaningful AI use | 35 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |
| Risk/capital management | 30 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |
| Re-execution, clean code and judge reproducibility | 25 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |
| Backtest/shadow evidence | 20 | `PROVIDED_BY_CHALLENGE_BRIEF` — proposed, unconfirmed |

The brief also mentions trade count, volume, average trade volume, final account value divided by initial capital, and execution speed as metrics. These do not supersede risk controls, net return, or technical verification; volume alone is not a success target. **`REQUIRES_ORGANIZER_CONFIRMATION`** — Obtain the final scoring rubric, tie-break rules, exact return/valuation method and activity interpretation from organizers.

## Required submissions

`PROVIDED_BY_CHALLENGE_BRIEF` says the submission should include:

1. GitHub source matching the exact code used for evaluated performance, with commit SHA and run/release identifier in logs.
2. Markdown architecture/algorithm/AI/market-tool/buy-sell/risk explanation and reproduction steps.
3. Per-decision and per-trade audit trail covering evidence, buy/sell/hold, risk verdict, intent, status/fill, fees and net P&L.
4. Approximately five-minute demo video showing operation/results and explaining outcomes; source-code display is not required. Speaking narration is preferred; a silent demonstration is better than none.
5. A reproducibility checklist matching commit, configuration, data/fixtures, model/prompt settings and run commands.

See [judge reproduction guide](judge-reproducibility.md) and [demo checklist](demo-video-checklist.md).

## Privacy, legality and prohibited actions

- **`PROVIDED_BY_CHALLENGE_BRIEF`** — Organizer-side participant information may be used to detect related accounts. That is an organizer privacy/compliance process; this repository must not collect or store team-member phone numbers, national IDs, birth dates, or other personal data.
- **`INFERRED`** — Do not store personal account/order data, keys, passwords, cookies, identity data or challenge-account records in source control, logs, fixtures, CI or reports.
- No authenticated/private-account request, live order, transfer, deposit, withdrawal or network trading was performed for this change. No challenge credentials or account data are present.

## Source and remaining confirmations

No canonical official challenge URL was included with the attachment, and this environment’s permitted outbound-host workflow did not provide an official organizer/Wallex challenge source for verification. Consequently **none** of the capital, duration, settlement, market list, scoring, account restriction, submission or demo facts is tagged `OFFICIAL_SOURCE_VERIFIED`.

Required organizer confirmations include: official event/start/end times and time zone; current disabled pairs and refresh process; account allocation/credit meaning and no-withdrawal rule; legal account entitlement; exact API/feed/auth/rate/fee/order constraints; TMN/USDT conversion and cutoff procedure; settlement details; final score rubric; data-logging/privacy policy; AI evaluation expectations; and any versioned submission/demo requirements.

**Audio review:** the available upload list contained only the written `.md` attachment. No audio was accessible, so audio review/transcription is incomplete and no audio-derived terms are claimed.
