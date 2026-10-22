# Data Model — Offline Research Kernel

All values are caller data or derived local simulation values. The models do not assert Wallex field semantics or runtime compatibility.

## Input domain

### `Candle`

- `symbol: str` — caller-provided non-empty instrument identifier; not checked against exchange metadata.
- `timestamp: datetime` — must be timezone-aware; normalized to UTC.
- `open/high/low/close/volume: Decimal` — parsed from CSV text, not binary float.
- Invariants: prices strictly positive; volume nonnegative; `low <= open <= high`, `low <= close <= high`, and `low <= high`.

### `TargetExposure`

- `timestamp: datetime` — time the caller's decision is observed; must match one candle close.
- `fraction: Decimal` — requested Spot exposure as a fraction of equity, constrained to `[0, maximum_spot_exposure]`.
- There is no embedded strategy or signal-generation method. Smart98 is the user-specified future mediation platform, not a strategy provider. A provider-neutral internal read-only `MarketDataPort` is a proposed seam only; Smart98/Wallex-specific adapters and all external contracts are deferred pending authoritative docs and separate review.

### `SimulationConfig`

- `initial_cash: Decimal > 0` — generic caller-supplied arithmetic balance, not a claim of owned/withdrawable assets and not a representation of credit principal or registration balance.
- `quote_currency: str` — explicit caller label, not validated against exchange metadata.
- `commission_rate: Decimal` — explicit generic proportional simulation assumption in `[0,1)`; not an official exchange rate.
- `slippage_rate: Decimal` — explicit adverse proportional simulation assumption in `[0,1)`; there is no separate spread model.
- `maximum_spot_exposure: Decimal` — explicit cap in `[0,1]`.
- No default instance or built-in parameter values.

Credit-plan fees, credit liability, forced-liquidation thresholds/mechanics, account permissions, and challenge-specific settlement are not modeled. Unknown values remain unknown; no general-plan fee example is reused as a challenge input.

## Data-quality report

`QualityIssue` contains `code`, `severity`, source row (when available), and a concise message. `QualityReport` contains rows examined, an immutable issue tuple, whether cadence was checked, and `is_valid`. The audit reports duplicate/non-monotonic timestamps, mixed symbols, empty datasets, and interval gaps/mismatches when the caller explicitly supplies an expected interval. Unknown interval yields no cadence assertion. CSV parse failures and invalid individual OHLCV values (including malformed decimals, invalid timestamps, OHLC relationships, and negative volume) raise `CSVDataError` at ingestion rather than becoming report issues. Findings never trigger automatic edits.

## Simulation output

- `SimulatedFill`: observation time, next-bar execution time, side, quantity, reference open, adverse simulated price, notional, modeled commission, and slippage cost.
- `LedgerPoint`: candle time, cash, base quantity, mark price, equity, running peak, and drawdown.
- `ReplayResult`: symbol, config/assumptions, immutable order outcomes, fills and ledger, final cash/quantity/equity, arithmetic total return versus initial cash, total modeled commission/slippage, maximum observed drawdown, and explicit `limitations` describing omitted financing/liquidation/settlement assumptions.

## State and transition

The replay starts with explicit cash and zero base quantity. A target fraction observed at candle `t` becomes eligible only at the next candle `t+1` open. Buy quantities are restricted by cash after explicit modeled costs; sells cannot reduce position below zero. The position is marked at each candle close. Any out-of-policy target, invalid chronology, nonzero position request unsupported by input data, or missing next bar fails closed. These outputs are simulated bookkeeping, not exchange orders or fills.
