# Implementation Plan: Offline Strategy-Neutral Research Kernel

**Branch**: `arena/81f9fa39-wallex-trading` (fixed session branch) | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

**Input**: [Feature specification](spec.md)

## Summary

Implement a dependency-free Python library and CLI for offline OHLCV CSV validation and deterministic, Spot-only target-exposure replay. Caller-supplied cost, capital, currency, and exposure assumptions are mandatory. The engine consumes strategy output but contains no strategy and no exchange adapter. The Wallex source register and Feature 001 knowledge base remain the only source of Wallex claims; contract conflicts are documented, not translated into code.

## Technical Context

**Language/Version**: Python 3.11+ (workspace Python 3.11.2)<br>
**Primary Dependencies**: Python standard library only<br>
**Storage**: Caller-supplied local CSV; in-memory simulation results<br>
**Testing**: `PYTHONPATH=src python3 -m unittest discover -s tests -v`<br>
**Target Platform**: Offline local development/runtime<br>
**Project Type**: Single Python library plus data-audit CLI<br>
**Performance Goals**: Correctness and deterministic repeatability for user-sized local CSVs; no unsubstantiated throughput target<br>
**Constraints**: No network access, API clients, credentials, account data, remote feeds, or live/paper exchange adapters; all configuration explicit; no data repair<br>
**Scale/Scope**: Single symbol and quote-currency ledger per replay; exact Decimal accounting; user-selected inputs only

## Constitution Check

- **Pass**: Specification and acceptance criteria precede implementation; implementation is tied to Feature 002.
- **Pass**: Local-only source files and fixtures; no live APIs, WebSockets, keys, account actions, transfers, or withdrawals.
- **Pass**: No built-in strategy, asset, timeframe, fees, capital, leverage, or personalized risk settings.
- **Pass**: Spot-only, no shorting/leverage; invalid exposure is rejected rather than clamped.
- **Pass**: Official API host/schema discrepancies are documented in Feature 001 and do not drive a runtime connector.
- **Pass**: Current, independent jurisdiction-specific compliance review is a future gate for any exchange use; no legal conclusion is made.

## Research Decisions

See [research.md](research.md). This plan uses only the locally confirmed runtime: Python 3.11.2, no dependency manifest or test framework, and the existing standard-library offline validators. Spec Kit CLI v1.2.2 was checked against GitHub's release list on 2026-10-21 and remains marked Latest; its generated tasks/commands are manually followed because native slash-command invocation is unavailable in this environment. Feature directories are created without running the branch-creating command, to preserve Arena's fixed branch.

## Project Structure

```text
src/wallex_research/
├── __init__.py
├── models.py             # Decimal Candle, TargetExposure, config and result types
├── data_quality.py       # Deterministic checks; no repair
├── csv_io.py             # Strict, local-only CSV parser
├── risk.py               # Explicit Spot exposure validation
└── replay.py             # Next-bar-open paper ledger and backtest accounting
scripts/check_market_data.py
tests/test_data_quality.py
tests/test_replay.py
tests/fixtures/            # synthetic only
specs/002-offline-research-kernel/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── tasks.md
└── contracts/offline-replay.md
```

**Structure Decision**: One Python package under `src/`, one small local-data CLI, and `unittest` tests; no service, database, dependency manager, web framework, or exchange adapter.

## Complexity Tracking

No constitution violations or extra services are introduced. The local signal port is a small domain boundary for future strategies/Smart98 research outputs, not an integration contract.
