# Offline Replay Contract

## Local data input

CSV must include exactly these logical fields (additional columns are rejected for this initial implementation): `symbol,timestamp,open,high,low,close,volume`. Numeric fields are decimal strings. Timestamps require an explicit offset and normalize to UTC. Input rows must be strictly chronological and single-symbol for one replay. The loader does not make network requests or repair data.

## Caller decisions and configuration

A `TargetExposure` is a strategy-neutral decision observed at an existing candle timestamp. Its `fraction` must be nonnegative and no greater than the explicitly configured exposure limit. The engine does not produce target exposures.

`SimulationConfig` requires `initial_cash`, `quote_currency`, `commission_rate`, `slippage_rate`, and `maximum_spot_exposure`. No default values are defined. All rates are generic simulation assumptions, not Wallex terms.

## Deterministic execution semantics

- Signal at candle close `t` can first execute at next available candle open `t+1`; same-bar or earlier fills are forbidden.
- Buys use `open * (1 + slippage_rate)`; sells use `open * (1 - slippage_rate)`.
- Commission is proportional to simulated notional at the explicitly supplied rate.
- Buy size may be limited to cash available after simulated cost; each requested target records requested, filled, and unfilled quantity/status. Short positions are not allowed.
- No tick/lot rounding, queue position, depth, latency, market impact beyond the simple configured slippage factor, order types, exchange minimums, or real fill lifecycle is modeled.
- Positions are marked at candle close. Return/drawdown fields are arithmetic model outputs only.
- Invalid configuration, invalid input chronology, over-limit exposure, and unexecutable final-bar signals fail closed.

## Side effects and security

The entire contract is local and deterministic. It MUST NOT construct network connections, read secrets, persist account information, or call Wallex, Smart98, an API, or a WebSocket. Any future external adapter is outside this contract and needs separate specification, contract review, security/risk review, and jurisdiction-specific legal/compliance clearance.
