# Smart98 Wallex MCP — Capability Matrix

**Date**: 2026-10-21 (historical repository snapshot; operator report notice received 2026-10-22)

> **Current evidence notice:** The status icons and response details in this 2026-10-21 matrix are historical repository claims; its checked-in responses are synthetic fixtures. A separate complete report text supplied by the user now names individual tools and reproduces report-attributed schemas/classifications, but Arena did not independently invoke or verify them. The report's `VERIFIED` labels are not independent Arena verification and do not establish current availability, permission, contract version, or schema compatibility. Treat tool-level capabilities as **USER-REPORTED / NOT INDEPENDENTLY VERIFIED**; authoritative source/version, permissions, and operational limits remain open. See the [dated Feature 005 review](research/feature-005-smart98-evidence-review-2026-10-22.md), [report text](research/user-sources/smart98_mcp_tool_evidence_report_2026-10-22.md), and [initial notice](research/user-sources/smart98_mcp_report_notice_2026-10-22.md).

## Legend

| Icon | Meaning |
|------|---------|
| ✅ | Tested — tool was safely invoked and returned valid data |
| ⚪ | Untested (verified read-only) — tool exists, not yet called |
| 🔒 | Private — returns authenticated-account data; not accessed |
| ⛔ | State-changing — blocked per safety constraints |

## Public Market Data

| Capability | MCP Tool | Status | Details |
|:---|---:|:---|:---|
| List all markets | `wallex_basic_get_markets` | ✅ | 85+ markets with full metadata |
| List spot markets | `wallex_spot_get_markets` | ✅ | Matches basic endpoint |
| List OTC markets | `wallex_otc_get_otcmarkets` | ✅ | stepSize, tickSize, minQty, minNotional, buy/sell/exchange status |
| List margin markets | `wallex_margin_get_markets` | ✅ | Risk coefficients, leverage levels |
| OHLCV candles | `wallex_basic_candle_history` | ✅ | Resolutions: 1,5,15,30,60,240,720,D,W,M |
| Order book depth | `wallex_basic_get_market_depth` | ✅ | 50 levels ask/bid per symbol |
| Full spot depth | `wallex_spot_get_depth` | ✅ | Depth across all spot markets |
| Recent public trades | `wallex_basic_get_latest_trades` | ✅ | ~50 most recent trades |
| OTC price quote | `wallex_otc_get_otc_price` | ⚪ | BUY/SELL side, symbol param |
| Margin public ratio | `wallex_margin_public_ratio` | ⚪ | Long/short ratio per market |

## Private Account Data (not accessed)

`wallex_basic_get_account_balances`, `wallex_basic_get_account_fees`, `wallex_basic_get_account_wallet_by_symbol`, `wallex_spot_get_open_order`, `wallex_spot_get_orders`, `wallex_spot_get_orders_client`, `wallex_margin_get_positions`, `wallex_margin_get_pnl`, `wallex_credit_active_sub_accounts_list`

## State-Changing Operations (all blocked)

All order creation, cancellation, OTC execution, margin operations, IBAN registration, prop-trading activation, transfers, and wallet operations are blocked.

## Integration Architecture

```
Caller-provided research/data → MarketDataProvider interface → Smart98MCPProvider parser/provider → injected MCP invoker seam
```

The repository does not contain the live MCP invoker/connector wiring or a strategy-to-risk-to-audit orchestrator. This diagram describes code boundaries only, not an operational end-to-end integration.

## Not Available via MCP

- WebSocket streaming data
- Full historical trade list
- Historical order book snapshots
- Account transaction history
