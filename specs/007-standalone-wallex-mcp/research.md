# Feature 007 Research: Standalone Wallex MCP Server

## Official MCP SDK

- **Package**: `mcp` on PyPI, published by Model Context Protocol (a Series of LF Projects, LLC.).
- **Latest stable**: `2.3.0` (verified 2026-10-22 via `https://pypi.org/pypi/mcp/json`).
- **License**: MIT.
- **Python requirement**: `>=3.10`. CI uses Python 3.12 — compatible.
- **Capabilities**: MCP server, MCP client, stdio, Streamable HTTP, SSE transports.
- **Key dependencies**: `pydantic>=2.12`, `httpx2>=2.10`, `jsonschema>=4.20`, `anyio`, `opentelemetry-api`, `pyjwt[crypto]`, `python-multipart`, `sse-starlette`, `starlette`, `uvicorn`.
- **Decision**: pin `mcp==2.3.0`. Do not depend on the GitHub `main` branch or undocumented APIs.

## Wallex endpoint evidence

### Implemented

`GET https://api.wallex.ir/hector/web/v1/markets`

- Verified against `MARKETS` (`https://developers.wallex.ir/docs/basic-services-markets`, reviewed 2026-10-22): response object with `markets` array, `message`, `success`; market fields include `symbol`, `base_asset`, `quote_asset`, `price`, `is_spot`, `is_otc`, `is_margin`, `is_tmn_based`, `is_usdt_based`, `amount_precision`, `price_precision`, `flags`, `volume_24h`, `change_24h`, `created_at`.
- Cross-checked against `MOD-GENERATED-GET-MARKETS` (`https://developers.wallex.ir/docs/generated/get-markets`, reviewed 2026-10-22): same path family, same field set, `x-api-key` security annotation on the generated page.
- **Auth status**: the official prose page does not state that this public endpoint requires an API key. Per constitution, public tools work with no key unless official documentation explicitly states otherwise. The generated page's `x-api-key` annotation is recorded as a discrepancy (`D-017`) and is not treated as a requirement for the public tool.

### Not implemented — official contract not verified

| Candidate | Status | Reason |
|---|---|---|
| Market depth / order book | NOT IMPLEMENTED | Prose (`DEPTH`) and generated (`MOD-GENERATED-GET-MARKET-DEPTH`) pages disagree on host (`api.wallex.ir` vs `api.wallex.com`), path versioning, and auth annotation. |
| Candle / OHLCV history | NOT IMPLEMENTED | `CANDLES` documents `/v1/udf/history`; `MOD-GENERATED-CANDLE-HISTORY` documents `https://api.wallex.com/v1/udf/history` with different requiredness and resolution sets. |
| Recent public trades | NOT IMPLEMENTED | `TRADES` and `MOD-GENERATED-GET-LATEST-TRADES` disagree on host, requiredness of `symbol`, and auth annotation. |
| Ticker observations | NOT IMPLEMENTED | No dedicated verified endpoint; ticker data is derived from the markets response in the existing Smart98 adapter, not from a standalone verified contract. |

Per constitution III and the evidence-first rule, these are not implemented until a single consistent verified contract exists. They are recorded here explicitly rather than fabricated.

## Authentication research

- Official documentation (`CREATE-KEY`, `MOD-INTRO`, `MOD-GENERATED-SPOT`) describes API-key creation and `x-api-key` header usage for private endpoints.
- No official source identifies a safe, unambiguously read-only authenticated endpoint suitable for verifying the existing `WALLEX_API_KEY` secret and its documented permissions.
- **Decision**: the authenticated read-only path is prepared but disabled. It requires a verified safe endpoint and explicit owner approval before any request is made.

## Open questions

- Does the public markets endpoint require `x-api-key` at runtime? Official prose says no; generated annotation says yes. Resolved by testing only in the gated manual path, never in CI.
- What are the exact rate limits for the public endpoint? Not documented numerically; the client applies conservative bounded retries and fails closed on repeated errors.