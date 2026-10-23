# Candle Dataset Audit

`wallex-data-audit` inspects local OHLCV JSONL produced by the public candle recorder or another source using the supported candle schema. It never connects to Wallex, reads account data, or sends orders.

## Run

```sh
python -m pip install -e ".[test]"
wallex-data-audit --input data/BTCUSDT-60s.jsonl \
  --symbol BTCUSDT --interval-seconds 60 \
  --output reports/BTCUSDT-data-audit.json
```

The tool automatically looks for the recorder's sibling manifest at `INPUT.manifest.json`. Pass `--manifest PATH` to use a different manifest. The exit code is 0 for `OK`, 1 for data that is invalid or requires review, and 2 for CLI/file errors.

## What is checked

- Invalid JSON, rows that are not objects, and malformed/non-positive OHLC values.
- Duplicate timestamps and timestamps arriving out of order.
- Missing, mixed, mismatched, or invalid symbol/interval metadata.
- Candle start alignment relative to the inferred or specified interval.
- Gaps between candle timestamps, with elapsed seconds and potential missing-bucket counts.
- Manifest markers for reconnects, connection errors and possible dropped partial candles.

## How to interpret status

- `OK`: no structural error, warning, or observed time gap was found in the supplied records. This does not prove that the source feed was complete.
- `REVIEW`: missing metadata, a time gap or a recorder manifest warning needs human interpretation.
- `INVALID`: a structural data error was detected, such as malformed OHLCV, duplicate or out-of-order timestamps, inconsistent interval or symbol.

**A timestamp gap is not automatically a data-loss event.** A public trade stream may have no trades during some intervals, so no candle is emitted for those intervals. The report labels gaps as `potential_gap_or_no_trades` rather than inserting synthetic candles or declaring the dataset corrupt. Confirm the capture window, recorder manifest and market activity before using the file for backtesting.

The report includes first/last timestamps, elapsed seconds, valid and invalid rows, gap details, the relevant subset of manifest fields, and issue codes. It deliberately omits secrets and account data. The audit does not repair, sort, fill, deduplicate or modify the input dataset; use the report to decide whether to correct or exclude records before backtesting.
