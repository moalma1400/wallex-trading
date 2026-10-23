# Standalone Wallex MCP operator guide

This repository-owned MCP server runs independently of Smart98 over MCP stdio.
It connects directly to the official Wallex API from Python code. It does not
reuse Smart98's private connector and does not require Smart98 to be running.

## Install and run

Use Python 3.12 for CI (package metadata supports Python 3.10+).

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
wallex-mcp
# or: python -m wallex_mcp.server
```

Configure the MCP host to launch `wallex-mcp` using this virtual environment.
MCP protocol messages use stdout; diagnostics use stderr.

## Tools and default behavior

With no live-trading configuration, the server exposes only
`wallex_get_markets` for public Spot market metadata. It does not send an API
key for that public request. The documented public endpoint is
`GET https://api.wallex.ir/hector/web/v1/markets` ([official active Spot markets](https://developers.wallex.ir/spot/activemarket)).

Optional read-only account tools are exposed only when the operator sets
`WALLEX_API_KEY` and `WALLEX_ENABLE_ACCOUNT_READONLY=1`:
- `wallex_get_balances` — `GET /v1/account/balances`
- `wallex_get_open_orders` — `GET /v1/account/openOrders`

References: [main account balances](https://developers.wallex.ir/basicservices/mainaccountwallet),
[active orders](https://developers.wallex.ir/spot/activeorders).

## Explicit opt-in live Spot trading

**Live order placement is disabled by default.** The two additional tools below
are registered only when all explicit environment settings are present and
valid. The same key is used only inside this local MCP process and never placed
in a tool argument, model prompt, source file, or log.

Required environment variables, supplied by the operator's secret manager:

- `WALLEX_API_KEY`: Wallex API key. Prefer least privilege consistent with the intended Spot operations.
- `WALLEX_ENABLE_LIVE_TRADING=1`: enables live write tools.
- `WALLEX_LIVE_TRADING_ACK=I_UNDERSTAND_REAL_ORDERS`: explicit operator acknowledgment.
- `WALLEX_LIVE_ALLOWED_SYMBOLS`: comma-separated exact symbol allowlist, e.g. `BTCUSDT` (example only; verify the actual market and contest rules before configuring).
- `WALLEX_LIVE_QUOTE_ASSET`: one explicit quote asset, e.g. `USDT` (example only).
- `WALLEX_LIVE_MAX_ORDER_NOTIONAL`: mandatory maximum order notional in the configured quote asset; no default is provided.
- `WALLEX_LIVE_FEE_BUFFER_BPS`: optional integer reserve in basis points; defaults to 100 bps (1%). This is a safety reserve, not a claim about the actual fee schedule.

When enabled, these tools are registered:
- `wallex_live_place_limit_order(symbol, side, quantity, price, client_id?)`: performs public-market and account-balance preflight, validates Spot status, exact symbol allowlist, quote asset, decimal precision, available funds and maximum notional, then submits one LIMIT order.
- `wallex_live_get_order(client_id)`: looks up an order by its client order ID, especially for reconciliation after an ambiguous submission.

The documented order API is `POST /v1/account/orders`, with a JSON body and
`x-api-key` header ([official Spot order creation](https://developers.wallex.ir/spot/createorder)).
Order details are available through `GET /v1/account/orders/{client_id}`
([official order detail](https://developers.wallex.ir/spot/singleorderdetail)).
The implementation deliberately exposes no market-order, cancel, transfer,
deposit, withdrawal, or margin tool.

### Write-safety contract

- Each order submission is attempted **once only**. There is no automatic POST retry.
- A timeout, server-side 5xx, malformed success response, or uncertain result raises
  `OrderOutcomeUnknown`. Reconcile using the same `client_id` before considering
  any further submission. Never generate a replacement order automatically.
- The client rejects symbols outside the explicit allowlist, non-Spot markets,
  wrong quote assets, invalid decimal values/precision, orders over the configured
  notional cap, and insufficient available balances after the fee reserve.
- The code does not choose a trading strategy, determine whether an order is
  profitable, or infer contest rules. It is an execution tool, not an autonomous
  strategy. Contest eligibility, minimum order sizes, actual fees, account scope,
  and market rules must be verified independently.
- No live call has been performed by repository tests or this documentation.
  Tests use synthetic keys and a fake HTTP transport only.

## API-call / credit discipline

A live order tool call performs a public market metadata read, an authenticated
balance read, and at most one order POST. A separate order lookup is needed for
reconciliation. No polling loop or market-history scan is run. GET calls follow
the existing read-client retry policy; write requests are never retried. Exchange
rate limits still apply; avoid repeated tool calls and do not treat API rate
limits as a budget guarantee.

## Offline validation

```sh
python scripts/validate_sources.py
python scripts/validate_doc_links.py
python -m compileall -q src tests scripts
python -m pytest -v
git diff --check
```

All tests must use fake HTTP transport and must not require real credentials or
make production requests. The normal GitHub Actions workflow runs offline tests.

## Security

- Never paste API keys into chat, commit them, or put them in tool arguments.
- Keep the key in the local MCP host's secret/environment manager.
- Do not enable live trading in CI, developer shells used for tests, or unattended
  production hosts until the account permissions and competition rules are reviewed.
- A successful API response is not proof that an order filled. Read the returned
  order status and execution quantities, and reconcile ambiguous outcomes.
