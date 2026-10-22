# Research — Offline Strategy-Neutral Research Kernel

**Research date**: 2026-10-21<br>
**Status**: Decisions for the offline kernel; no Wallex contract is inferred.

## Environment and tools

- Python 3.11.2 is installed; no `pyproject.toml`, `requirements.txt`, `src/`, `tests/`, or CI configuration existed at inspection time. The source validators are standard-library scripts.
- `python3 -m unittest` is available through the interpreter; use it rather than adding a dependency/test framework.
- Installed Spec Kit CLI is v1.2.2; `gh release list --repo github/spec-kit` reported v1.2.2 as Latest (released 2026-10-19). Generic integration and templates are preserved. The generated feature-creation script would create/switch to `002-offline-research-kernel`, which conflicts with Arena's fixed branch, so its dry-run was used only to verify the feature directory name; directory/artifacts are created manually from repository templates.

## Source contract observations from documentation review

The following are statements visible in official docs, not runtime tests:

- The developer overview says the base is `https://api.wallex.ir`, but inspected generated Swagger material for Spot/basic services states host `api.wallex.com`; generated endpoint examples also expose leading `//api.wallex.com` and root `/depth/all`. These conflicts are recorded in Feature 001. No host is selected for code, and no endpoint is called. [MOD-INTRO](https://developers.wallex.ir/docs) · [MOD-GENERATED-SPOT](https://developers.wallex.ir/docs/generated/spot) · [MOD-BASIC-SERVICES](https://developers.wallex.ir/docs/basic-services) · [MOD-GENERATED-GET-DEPTH](https://developers.wallex.ir/docs/generated/get-depth)
- Official WebSocket channel guides recommend Centrifugo v2 over a legacy v1 described as deprecated; the new endpoint is `wss://api.wallex.ir/connection/websocket`. Candle pages describe replacing a candle by its `t` timestamp and only limited history (up to 10 messages over 2 minutes); other channels do not replay data missed during disconnect. No client is implemented. [MOD-SOCKET-ALL-PRICE](https://developers.wallex.ir/docs/socket-all-price) · [MOD-SOCKET-CANDLE](https://developers.wallex.ir/docs/socket-candle) · [MOD-SOCKET-RAW-PROTOCOL](https://developers.wallex.ir/docs/socket-raw-protocol)
- The generated fee and account-balance pages describe API-key-protected account information; the fee endpoint schema returns account-specific maker/taker rate fields but no live values are queried here. [MOD-GENERATED-GET-ACCOUNT-FEES](https://developers.wallex.ir/docs/generated/get-account-fees) · [MOD-GENERATED-GET-ACCOUNT-BALANCES](https://developers.wallex.ir/docs/generated/get-account-balances)

The API-spec artifacts were inspected through the page reader, which returned transformed/truncated chunks. Exact response bodies, hashes, publisher release/version, and complete offline copies were not available to preserve in this environment; records are explicitly not described as byte-for-byte downloads.

## Design decisions

1. **Offline only**: accept local CSV and in-memory signals; do not add `requests`, HTTP, WebSocket, exchange SDK, credential, or database dependencies.
2. **Decimals and UTC**: parse numeric strings directly to `Decimal`; reject NaN/infinity and naive times; normalize aware timestamps to UTC.
3. **Strict data quality**: reject malformed OHLC relationships, negative volume, duplicate/non-increasing timestamps, mixed symbols, and explicitly configured gaps. Never sort, deduplicate, impute, or fill automatically. When no interval is supplied, cadence completeness stays unknown.
4. **Strategy-neutral and mediated integration boundary**: replay consumes caller-provided `TargetExposure` at an observation candle close; no signal generator/strategy exists in this feature. The user identifies Smart98 as the intended mandatory mediator for future Wallex API/MCP access, but no Smart98 interface is verified. A provider-neutral, read-only internal `MarketDataPort` is a documentation proposal only; any adapter must use a verified Smart98-mediated interface, never direct Wallex access, and requires separate contract/security/compliance review.
5. **Causal timing**: a close-observed target can only be filled at the following candle open, with explicit modeled slippage. A signal without a following candle is invalid rather than filled on its own close.
6. **Explicit assumptions**: initial cash, quote-currency name, commission rate, slippage rate, and maximum Spot exposure have no defaults. These generic values are not Wallex fees or risk advice.
7. **Fail-closed Spot controls**: target exposure must be between zero and a caller-supplied cap no greater than 100%; no shorting, leverage, margin, or silent clamping. Fees/slippage and insufficient cash are visible in fills/ledger.
8. **No profitability claim**: performance outputs are accounting calculations under a simple candle-open fill model and cannot establish real execution, data quality, expected returns, or strategy profitability.

## Deferred / unknown

- User's market, quote currency, interval, strategy, initial capital, cost assumptions, and acceptable risk.
- Dataset provenance/licensing and any Smart98 interface details.
- Actual Wallex API host, operation availability, auth, market precision, fees, latency, order-book depth, partial fills, rate limits, and account eligibility.
- Jurisdiction-specific legal/compliance outcome. Treasury/OFAC material recorded in Feature 001 signals significant sanctions risk; it is not a complete assessment of Netherlands/EU law or any person's circumstances. No exchange use is authorized.
