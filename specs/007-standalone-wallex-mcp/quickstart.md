# Feature 007 Quickstart: Standalone Wallex MCP Server

## Prerequisites

- Python 3.12 (or any 3.10+).
- The `mcp` SDK is declared in `pyproject.toml` and installed with `pip install -e .` or `pip install -r <(pip freeze)` after the project is installed.

## Run the server locally over stdio

```bash
python -m wallex_mcp.server
```

The server speaks MCP over stdio: protocol messages on stdout, diagnostics on stderr. Do not redirect stdout to a file; an MCP host reads it as the protocol stream.

## Connect an MCP client

The repository ships a protocol smoke test that launches the server as a subprocess and invokes the tool through the official SDK:

```bash
python -m pytest tests/test_server_protocol.py -v
```

For an ad-hoc client:

```python
import asyncio
from mcp import Client
from mcp.client.stdio import stdio_client, StdioServerParameters

async def main() -> None:
    params = StdioServerParameters(command="python", args=["-m", "wallex_mcp.server"])
    async with stdio_client(params) as (read, write):
        async with Client(read, write) as client:
            await client.initialize()
            tools = await client.list_tools()
            result = await client.call_tool("wallex_get_markets", {})
            print(result.structured_content)

asyncio.run(main())
```

## Run offline tests

```bash
python -m pytest -v
```

No test makes a network request to Wallex. Integration tests use sanitized fixtures or a mocked HTTP transport.

## Trigger public integration tests

```bash
gh workflow run wallex-mcp.yml --ref feat/standalone-wallex-mcp
```

or from the GitHub UI: **Actions → wallex-mcp → Run workflow**. Public network smoke is an explicit opt-in step and is never a pull-request check.

## Configure authenticated read-only testing

1. Create a protected GitHub Environment named `wallex-readonly` with the `WALLEX_API_KEY` secret.
2. Ensure the workflow runs only from the trusted default branch.
3. Enable the gated authenticated step only after a safe read-only endpoint is verified and the owner approves.
4. Never run authenticated code from forks, pull requests, or untrusted commits.

## Feature status

| Capability | Status |
|---|---|
| `wallex_get_markets` | Implemented, verified, tested |
| Market depth | NOT IMPLEMENTED — official contract not verified |
| Candle history | NOT IMPLEMENTED — official contract not verified |
| Recent trades | NOT IMPLEMENTED — official contract not verified |
| Ticker | NOT IMPLEMENTED — official contract not verified |
| Authenticated read-only | Prepared, disabled pending verified endpoint and owner approval |