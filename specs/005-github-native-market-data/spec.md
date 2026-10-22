# Feature 005: GitHub-native read-only market-data connectors

**Status:** Implementation proposal on `feat/github-native-market-data`; owner review required before merge.

## User stories
- Researcher can fetch CoinGecko public price snapshots without Smart98, Olive, or MCP.
- Researcher can configure a reviewed Wallex public market-data endpoint and fetch read-only market metadata.
- Maintainer can test parsing/error handling offline and schedule collection in GitHub Actions.
- Owner can disable network access by default and ensure no trading/account mutation path exists.

## Requirements
- FR-001: Python standard library only; no MCP/Smart98 dependency.
- FR-002: No network unless `--network` is explicitly supplied.
- FR-003: Wallex base URL and route are explicit configuration; no host/path is silently chosen because official docs record conflicts.
- FR-004: HTTPS only; reject URL credentials, unsafe routes, insecure final URLs, non-2xx, invalid JSON, and oversized responses.
- FR-005: Read-only GET for configured Wallex market-data route and CoinGecko simple-price endpoint. Other Wallex routes must be specified and reviewed separately.
- FR-006: Optional CoinGecko Demo key comes from environment and never appears in URL or output.
- FR-007: Snapshots include source URL, UTC retrieval time, HTTP status, and SHA-256 of raw response bytes.
- FR-008: Unit tests use synthetic payloads and injected transport; CI tests never use network.
- FR-009: No balances, private account data, orders, transfers, withdrawals, or trading actions.
- FR-010: GitHub Actions has manual and two-hour scheduled triggers, but collection remains disabled unless `ENABLE_PUBLIC_MARKET_DATA=true` is configured.
- FR-011: Missing Wallex base URL/route skips Wallex instead of guessing.

## Evidence gaps
The official Wallex source register/discrepancy log records host, market-list path, candle parameters, and authentication-annotation differences. Therefore live Wallex connectivity is not considered verified until the owner confirms the exact route and manually reviews a live run. CoinGecko quotas/requirements depend on plan; rate limits and terms must be respected.

## Acceptance criteria
- Offline tests cover success, bad URL, non-2xx, invalid JSON, non-object JSON, insecure final URL, unsafe route, key not in URL, and timeout bounds.
- Existing offline validators and test suite pass.
- Workflow artifacts are inspectable and are not committed as market data.
- No profitability or runtime-success claims are made before live verification.
