# Offline Paper Trading Broker

`wallex_agent.paper_trading.PaperBroker` is a local, virtual Spot ledger. It does not make HTTP requests, read balances, use API keys, or submit exchange orders. It is separate from both the shadow runner and the live MCP server.

## Example

```python
from wallex_agent.paper_trading import PaperBroker

broker = PaperBroker(
    "var/paper/paper.sqlite3",
    initial_cash="1000000",
    fee_bps="10",                 # illustrative only: 0.10% per side
    slippage_bps="20",            # illustrative only: 0.20% per side
    max_order_notional="100000",
    max_daily_loss_percent="3",
)
fill = broker.execute_market_order(
    event_id="candle-BTC_USDT-2026-10-23T10:00:00Z-buy",
    timestamp="2026-10-23T10:00:00Z",
    symbol="BTC_USDT",
    side="buy",
    quantity="0.001",
    reference_price="100000",
)
print(fill)
print(broker.snapshot())
```

Use a deterministic, unique `event_id` for each intended simulated order. Retrying the same ID returns the original result and does not apply a second fill. SQLite persists virtual cash, positions and fills across process restarts.

## Simulator behavior

- Applies adverse slippage to the reference price and fees to simulated notional.
- Rejects non-positive quantities/prices, orders over the notional cap, buys exceeding virtual cash, and sells exceeding virtual inventory.
- Maintains a per-day marked-equity baseline and rejects orders when the configured daily-loss limit has been reached.
- Reports marked equity and explicit `live_trading_enabled: false` / `order_submission_attempted: false` fields.
- Uses decimal arithmetic for money/quantity calculations.

## Important limitations

This is a deterministic research simulator, not a market-data service or complete trading system. The caller must provide timestamps, symbols, quantities and reference prices. It does not implement candle-based signal generation, automatic mark-to-market for all symbols, partial fills, order-book depth, queue priority, taxes, exchange-specific fee tiers, portfolio allocation, or reconciliation with Wallex. Daily loss checks use the stored position marks and the order's supplied reference price. Do not treat illustrative fee/slippage settings as official Wallex rates. No profitability is implied.
