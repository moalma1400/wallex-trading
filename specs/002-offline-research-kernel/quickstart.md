# Quickstart — Offline Research Kernel

## Requirements

- Python 3.11 or newer.
- No network, API key, exchange account, third-party dependency, or live feed.

## Validate local data

The command reads a caller-supplied CSV only. Required columns: `symbol,timestamp,open,high,low,close,volume`. Use decimal text and timestamps with an explicit UTC offset (for example, `Z`). The example below is a synthetic fixture and not Wallex data.

```bash
python3 scripts/check_market_data.py tests/fixtures/synthetic_ohlcv.csv
```

To check gaps, explicitly choose an interval for this dataset; the tool does not infer one:

```bash
python3 scripts/check_market_data.py tests/fixtures/synthetic_ohlcv.csv --interval-seconds 60
```

An audit reports issues and does not sort rows, interpolate, repair, or access a remote source.

## Run tests

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/validate_sources.py
python3 scripts/validate_doc_links.py
```

## Backtest interface status

The library accepts explicit `TargetExposure` decisions and an explicit `SimulationConfig`; it does not generate strategy signals. All cost assumptions are generic local model inputs, not current Wallex fees. Check the tests and contract in this feature before using the replay API. A paper result is not a live or exchange-connected paper-trading session.

## Explicitly unsupported

No strategy recommendation, public/live data fetch, Smart98 or Wallex adapter, key management, user/account access, order submission, margin/leverage, transfer/withdrawal, or legality assessment. Obtain current independent, jurisdiction-specific legal/compliance advice before any future real exchange use; no outcome is guaranteed.
