# Standalone Wallex MCP operator guide

Feature 007 exposes one repository-owned MCP tool, `wallex_get_markets`, over
the Model Context Protocol stdio transport. It is independent of Smart98 at
runtime. It currently supports only the verified public Spot market metadata
endpoint:

- Method: `GET`
- Host: `api.wallex.ir`
- Path: `/hector/web/v1/markets`
- Official documentation: [MARKETS](https://developers.wallex.ir/docs/basic-services-markets)

No API key is required or sent for this endpoint. The default allowlist contains
only this GET route. Depth, candles, ticker, trades, authenticated endpoints,
orders, cancellations, deposits, withdrawals and transfers are not exposed.

## Install

Use Python 3.12 for the repository CI configuration (the package metadata
supports Python 3.10+).

```sh
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[test]"
```

## Run the server

```sh
wallex-mcp-server
# or
python -m wallex_mcp.server
```

The server speaks MCP over stdio. Configure the MCP host to launch the
`wallex-mcp-server` executable (or `python -m wallex_mcp.server`) with the
repository's virtual environment. Do not pipe unrelated output to stdout;
protocol messages use stdout and diagnostics use stderr.

## Offline validation

```sh
python scripts/validate_sources.py
python scripts/validate_doc_links.py
python -m compileall -q src tests scripts
python -m pytest -v
git diff --check
```

Tests inject a fake HTTP transport. The stdio protocol smoke test initializes
an MCP client and lists tools without invoking the Wallex-backed tool. These
tests must not make network requests to Wallex and must not require credentials.

The dedicated `.github/workflows/wallex-mcp.yml` workflow is manually
dispatchable and runs its validation job only when dispatched against
`main`. The regular offline CI workflow also validates pull requests to main.

## Security and operational boundaries

- Never paste API secrets into chat, source files, fixtures, logs, or commits.
- Do not set credentials for offline CI or ordinary tests.
- Never treat the presence of an MCP tool as proof that the exchange permits a
  use case, that an account is eligible, or that a market is tradable.
- Any future endpoint must have an official source record, reviewed response
  schema, explicit allowlist entry, and separate tests before it is enabled.
- Account-changing or trading actions are out of scope for Feature 007 and
  must not be added under this feature.
- Review `security-data-flow.md` before integrating the server into an agent.
