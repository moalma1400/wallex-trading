# Challenge-control and Feature 005 architecture (offline / gated)

This documents repository contracts and evidence boundaries, not live Wallex behavior. Feature 004 challenge facts come from `USER-WALLEX-HACKATHON-BRIEF` and are not independently official-verified. Feature 005 is limited to verified public, read-only Spot market data through Smart98 after its evidence gates pass; live execution remains disabled. See the [canonical KB](../knowledge-base/wallex-agentic-ai-hackathon.md) and [dated Feature 005 evidence review](../research/feature-005-smart98-evidence-review-2026-10-22.md).

## Local control path

```text
local metadata + raw-list registry + policy config
            │
            ▼
 is_challenge_spot_market_allowed(...) ── machine-readable reasons
            │ requires explicit config, strategy approval, and a separate
            │ successful risk verdict; metadata must be trusted/current
            ▼
 validate_market_order_amounts(...) ── precision/minimum checks
            │
            ▼
 evaluate_challenge_risk(...) ── configured independent caps and state
            │
            ▼
 DecisionEvent / DecisionAuditLog ── local JSONL, deterministic IDs
            │
            └── dispatch_order_intent(backtest|shadow|dry_run): record-only
                dispatch_order_intent(live): LIVE_EXECUTION_NOT_IMPLEMENTED
```

There is no submitter. `MarketRequest.risk_approved` must be supplied from the separately evaluated risk verdict; false denies. `MarketRequest.algorithmic_decision` must explicitly be true; manual trading intents are denied. `ChallengeModePolicy.explicit_configuration` is false for a bare in-memory default and is set only by loading the checked-in schema-validated offline policy. This prevents accidental authorization by a permissive default object.

## Component contracts

- `config/challenge/wallex_disabled_spot_pairs_raw.txt` is the verbatim user-provided appendix; JSON is derived and hash-checked. Runtime registry refuses duplicates, malformed entries, count/hash mismatch or noncanonical list. It never asserts that a non-disabled pair is available.
- `src/wallex_research/challenge.py` parses pair syntax, enforces the Spot-only policy, requires explicit trusted metadata state (`active`, `orderable`, `is_spot`, `challenge_enabled`), source/time/freshness, supported quote, strategy and risk approvals, and verified precision/minimum-order semantics. Decisions are pure and local; each block has a stable reason code.
- `src/wallex_research/challenge_risk.py` evaluates explicit independent per-order/asset/deployment, loss/drawdown, order-rate, freshness, spread/slippage/liquidity/cost, reconciliation and emergency-stop gates. All checked-in numeric limits are unset. `load_challenge_risk_limits` returns all limits as missing unless configuration status is explicitly `REVIEWED_INTERNAL` and evidence status is supplied; an unreviewed numeric edit cannot activate a cap.
- `src/wallex_research/challenge_execution.py` records offline intent only. The `submit_order` injection seam exists only to prove it is never called in tests. Live is blocked even if a caller attempts to enable the default.
- `src/wallex_research/decision_log.py` provides a versioned event contract and local append-only JSONL writer. It binds code/config/strategy/source and model/prompt provenance, requires typed event payloads, and refuses exchange-origin events, sensitive keys and obvious secrets. It is not connected to an LLM or exchange.
- `src/wallex_research/challenge_settlement.py` reports readiness only from an exact cutoff with source ID/HTTPS URL/SHA-256, reconciled balances, separately provenance-backed official valuation, known fees, known zero unrealized P&L and TMN-only inventory. Internal estimates are explicitly labeled and do not produce a settlement-ready value. A synthetic test-only mode is warned and cannot authorize operations. It does not liquidate, convert assets, retrieve balances or assign stale/invented token values.

## Feature 005 — Smart98-mediated public Spot market data

> **Scope and status:** Feature 005 permits only a bounded public, read-only Spot market-data adapter after its evidence and review gates pass. Private-account reads and all state-changing actions remain outside scope. Tests, replay, shadow, dry-run, and CI remain offline. No direct Wallex call or direct-access fallback is allowed.
>
> **Evidence boundary (2026-10-22):** the user reports that an operator supplied a Smart98-generated report titled “Feature 005 Task T003 — MCP Tool Evidence Report,” dated 2026-10-22, describing live read-only public market-data invocations. The report body/attachment is absent. This is an aggregate operator report only; Arena did not invoke or independently verify the tools. Exact tool IDs, schemas, payloads, versions, permissions, and per-tool statuses remain unknown. See the [evidence intake and T004/T005 review](../research/feature-005-smart98-evidence-review-2026-10-22.md) and [user-provided report notice](../research/user-sources/smart98_mcp_report_notice_2026-10-22.md).

### Integration layers and evidence status

| Layer | Repository evidence | Status / boundary |
|---|---|---|
| Wallex public documentation | Registered official pages cover market metadata, Spot markets, candles, depth, public trades, and fair-price documentation. Example pages: [MARKETS](https://developers.wallex.ir/docs/basic-services-markets), [SPOT-MARKETS](https://developers.wallex.ir/docs/spot-active-markets), [CANDLES](https://developers.wallex.ir/docs/basic-services-candles), [DEPTH](https://developers.wallex.ir/docs/basic-services-depth), [TRADES](https://developers.wallex.ir/docs/basic-services-latest-trades), [MOD-SOCKET-FAIR-PRICE](https://developers.wallex.ir/docs/socket-fair-price). | Documentary claims only; schemas/hosts differ in places and the pages do not prove runtime availability, Smart98 compatibility, account permission, or challenge eligibility. |
| Wallex MCP source/tool catalog | No canonical publisher/repository, release, source version, or authoritative tool schema is registered in `docs/research/source-register.yaml`. | **UNKNOWN.** The operator report notice does not supply the original report or its source/version. |
| Smart98 platform and mediation | Project context designates Smart98 as the mandatory mediator; no product contract, admin documentation, transport/auth specification, or log/secret-boundary proof is in the repository. | Role is a user-provided requirement. Technical interface, permissions, credential isolation, egress, versioning, and error semantics remain **UNKNOWN**. |
| Existing `src/mcp_adapter/` code | `Smart98MCPProvider` and parsers use an injected invoker seam; no actual Smart98 client/transport or production wiring is included. | Local implementation and synthetic tests only; its identifiers and parser expectations are not proof of external tool contracts. |
| Offline `src/wallex_research/` domain | Local normalized records, provenance, data-quality, challenge eligibility/risk, replay, and event logging exist. | Reusable local architecture; no remote data provider or live execution path. |

### Existing parser/provider interface (code contract, not MCP evidence)

`src/mcp_adapter/__init__.py` defines `MarketDataProvider` with `get_markets`, `get_candles`, `get_order_book`, `get_recent_trades`, and `get_ticker`, alongside `MarketMeta`, provider-local `Candle`, `Ticker`, `OrderBook`, `PublicTrade`, and `DataSource.MCP_SMART98`. `src/mcp_adapter/provider.py` contains these code-level tool constants:

| Code constant | Identifier in checked-in code | Local call/shape expectation (unverified) |
|---|---|---|
| `TOOL_MARKETS` | `wallex_basic_get_markets` | No arguments; parser accepts optional `success`/`result` envelope and expects `markets`. |
| `TOOL_CANDLES` | `wallex_basic_candle_history` | Sends `symbol`, `resolution`, `from`, `to`; expects UDF-like `s`, `t`, `o`, `h`, `l`, `c`, `v`. Code interprets `t` as Unix seconds and checks response timestamps against the requested range. |
| `TOOL_DEPTH` | `wallex_basic_get_market_depth` | Sends `symbol`; expects `ask`/`bid` arrays of objects with `price` and `quantity`. |
| `TOOL_TRADES` | `wallex_basic_get_latest_trades` | Sends `symbol`; expects `latestTrades` entries with `symbol`, `price`, `quantity`, `isBuyOrder`, and ISO-8601 `timestamp`. |

These identifiers are **from local code**, not from the missing operator report. The tests patch `_call_mcp` and use `tests/fixtures/mcp_responses.py`; they do not establish production invocation. `get_markets` uses the Basic markets identifier and relies on a separate gate for Spot eligibility. No OTC, Margin, private-account, or state-changing method is exposed by this provider class.

The local parser is strict about decimal-compatible values, timestamps, array lengths, OHLC consistency, candle ordering/gaps, trade fields, and book ordering/crossing. Limits remain: `MCPTimeout` is declared but no timeout/retry/pagination behavior is wired; `check_staleness` is not enforced end-to-end; receipt time is not event time; source/tool version and common provenance are incomplete; candle query boundary semantics and resolution mapping are not upstream-verified. `get_candles` currently accepts an event exactly at `to`, but this is only an implementation behavior, not evidence of the upstream contract.

**Price-reference warning:** `fair_price` is not an executable bid/ask quote. Do not use it for execution-price, spread, fill, or order-limit assumptions. `parse_ticker_from_market` currently maps `fair_price.bid`/`fair_price.ask` to local fields named `Ticker.bid`/`Ticker.ask`; treat that mapping as a pre-use issue, not proof of an executable quote. The official fair-price page documents a periodic snapshot, not an executable quote or service-level guarantee. [MOD-SOCKET-FAIR-PRICE](https://developers.wallex.ir/docs/socket-fair-price)

### Reusable data, eligibility, and replay components

- `src/wallex_research/historical.py` contains versioned local `Provenance`, `DatasetContext`, `CandleRecord`, `MarketMetadataRecord`, `PublicTradeRecord`, `FairPriceSnapshotRecord`, `OrderBookSnapshotRecord`, and `OrderBookSideSnapshotRecord` types, plus `HistoricalDataRequest` and a local/future-history `HistoricalDataProvider` protocol. `SCHEMA_VERSION` is `1.0`; this protocol is not a Smart98 transport or general live market-data port.
- `src/wallex_research/dataset_store.py`, `src/wallex_research/historical_quality.py`, and `scripts/market_data_pipeline.py` preserve local raw bytes/hashes, create normalized records, audit explicit caller policies, and gate candle export. No network fetch is implemented.
- `config/challenge/wallex_disabled_spot_pairs_raw.txt` and `config/challenge/wallex_disabled_spot_pairs.json` provide a hash-bound, user-provided exclusion list (345 entries); this is not an allowlist. `src/wallex_research/challenge.py` revalidates it and fail-closes on disabled, unknown, stale/future, contradictory, non-Spot, non-orderable, or unsupported market evidence and on unverified precision/minimum semantics.
- `src/mcp_adapter/eligibility.py` has a separate, smaller hard-coded deny list. It is not canonical and must not be used as an authorization source or second market registry. Risky or disabled markets must be handled conservatively; absence from exclusions never authorizes a market.
- `src/wallex_research/replay.py::run_replay` consumes caller-supplied `TargetExposure` and remains local/causal (next-bar-open); it is not a feed or strategy. `src/wallex_research/challenge_execution.py::dispatch_order_intent` records offline intents and blocks LIVE with `LIVE_EXECUTION_NOT_IMPLEMENTED`. `src/wallex_research/decision_log.py` writes local validated events and rejects exchange-origin events.
- `tests/test_mcp_adapter.py`, `tests/test_historical_data.py`, `tests/test_challenge.py`, and `tests/test_replay.py` exercise synthetic/local behavior. `scripts/validate_sources.py` and `scripts/validate_doc_links.py` are offline structural/local-link validators; CI compiles and runs offline tests without Wallex/Smart98 credentials or requests.

### Provider-neutral contract and open gates

There is no implemented, genuinely provider-neutral live `MarketDataPort`. The existing `MarketDataProvider` is a useful method-shape reference but resides in an MCP-labelled package and its types tag data `MCP_SMART98`. The existing history protocol is intentionally local/historical and narrower. A T006 contract may reuse the normalized `src/wallex_research/historical.py` records and challenge eligibility boundary; it must not introduce a parallel data framework or turn parser assumptions into facts. Keep provenance, source-event time versus capture time, completeness, freshness policy, exact decimal encoding, error semantics, pagination, and source/version explicit. Until verified, unknown values fail closed.

The current challenge config sets `execution_scope` to `offline_only`; freshness, official cutoff, market authorization, and numeric risk limits remain unresolved/null. `MarketEligibilityGate` cannot authorize challenge trading, and a positive parser/filter result is not account permission.

### Access classes and activation boundary

1. **Public read-only Spot market data:** only a specifically verified Smart98-mediated tool with exact schema, permission scope, provenance, freshness, completeness, and market eligibility may be considered. The present report notice identifies no individual tool.
2. **OTC and Margin:** separate product scopes; not interchangeable with Spot and not part of the Feature 005 adapter. Historical capability-matrix rows are not current permission evidence.
3. **Private/account reads:** balances, account fees/wallets, private orders, positions, and account transaction data remain disabled and were not accessed.
4. **State-changing operations:** orders, cancellations, transfers, deposits, withdrawals, wallet actions, and OTC/Margin execution remain prohibited. Tool presence is not permission. There is no order submitter in the local architecture.
5. **Shadow/backtest/dry-run/CI:** remain offline and cannot submit orders. Public operator-reported data access does not change this boundary.

Credentials and private/account data must never enter prompts, repository files, fixtures, tests, or logs. Wallex's official key-creation page describes account selection and Read/Trade/Withdrawal permission choices, but does not establish this project's or a challenge account's permissions. [CREATE-KEY](https://developers.wallex.ir/docs/create-api-key)

### Evidence still required before T003/T006/T007

- The original sanitized Smart98 report, exact tool IDs, request parameters and output shapes, event/retrieval timestamps and timezone/units, decimal forms, source/version, and tool-by-tool read/write permissions.
- Smart98 and upstream rate limits, timeouts, retries/cancellation, partial-result/error propagation, pagination/truncation/streaming, candle history/range semantics, and completeness guarantees.
- Authentication and secret custody/isolation, logging/redaction/retention, tool allowlisting, and an explicit Smart98 approval/compatibility statement for the exact integration.
- Official organizer rules/window, dedicated-account permissions, allowed Spot markets, deterministic risk limits/reconciliation, and a current qualified jurisdiction/compliance review before any real exchange use.

The exact evidence request and all unresolved fields are tracked in [the T003–T005 review](../research/feature-005-smart98-evidence-review-2026-10-22.md) and [unresolved questions](../research/unresolved-questions.md). No MCP was installed/configured; no credentials, private reads, production requests, or state-changing actions were used in this review.

Feature 002's next-bar-open/cost contract is unchanged. No strategy, live data ingestion, order execution, current-market eligibility, settlement authority, profitability, or legal authorization is established by this architecture or its tests.
