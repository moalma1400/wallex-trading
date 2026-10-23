# Cost-aware shadow opportunity ranking

The independent `wallex-agent` runner already screens public Spot market metadata and, when explicit fee and slippage assumptions are supplied, calculates an observed short-window net-edge estimate. This module ranks only assessments that are explicitly eligible and whose cost model status is `WATCH_EDGE`.

Ranking order:
1. Highest positive `net_estimated_edge_bps`.
2. Lowest observed quoted spread when net edge ties.
3. Alphabetical normalized symbol for deterministic tie-breaking.

Run `wallex-agent` as described in [the shadow runner guide](README.md). Each output cycle now includes `ranked_opportunities` alongside the full assessments. A ranked item is labelled `SHADOW_CANDIDATE`, not BUY. If cost assumptions are omitted, the cost model is disabled and the ranked list stays empty.

## Safety and interpretation

- The score is a comparison of an already observed price move to an explicit cost reserve, not a forecast or proven trading edge.
- No strategy, asset universe, fee rate, slippage rate, risk budget, or contest rule is inferred.
- Missing, malformed, non-positive, or ineligible rows are excluded.
- Ranking does not imply sufficient liquidity, an executable price, a future return, or permission to trade.
- This code does not read account data or submit, modify, or cancel orders. It is independent of Smart98.
