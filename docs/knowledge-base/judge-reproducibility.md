# Judge reproduction guide (offline)

This guide reproduces local policy checks and synthetic examples. It does not connect to Wallex, place orders, prove market availability, or establish profitability. The challenge terms and disabled list are user-provided evidence, not independently verified official rules.

## Requirements and safety

- Python 3.11+; no network access or exchange credentials required.
- Use only synthetic fixtures or a separately licensed, provenance-captured dataset. Never commit private-account data or member PII.
- Do not configure any live adapter. It is not implemented. `live` dispatch is expected to fail closed.
- No current LLM call is made for historical data. The AI event format is a schema contract only; no model integration is included.

## Re-run

From repository root:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/build_challenge_pair_registry.py --check
python3 scripts/validate_sources.py
python3 scripts/validate_doc_links.py
```

Optional focused challenge suite:

```sh
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_challenge.py' -v
```

All input files are local. Test names demonstrate rejection of disabled/unknown/stale/contradictory metadata, non-spot and margin/borrow/short flags, unconfigured age/quote/risk, unverified order constraints and settlement evidence. The fixture `tests/fixtures/challenge_market_metadata.json` is explicitly synthetic; its positive eligibility test requires an explicit test-only flag and emits a warning.

## Reproducible run record

For any future research run, capture a stable run ID and append-only local events containing:

- repository commit SHA, configuration SHA-256, strategy and event schema versions;
- dataset/fixture identifier and SHA-256, source and capture interval/time zone, candle completeness and causal alignment;
- code invocation, deterministic seeds if applicable, dependency/environment versions;
- explicit fees/slippage/cost assumptions (never infer them from unverified brief text);
- every decision including HOLD, source feature references, risk verdict/reasons, order intent and simulated result, fees, balance/P&L snapshots and run summary;
- AI model/provider/version and prompt/template hash plus actual validated output when a real model is introduced; never post-hoc rationale or present-day model backfills for historical decisions.

Events use deterministic IDs and a versioned schema. They reject exchange-origin records in this offline implementation, common secrets/PII fields and floats in decision payloads; use decimal strings for financial quantities. Never log credential material, personal details, raw private account responses, or member identity.

## Interpreting outcomes

A unit-test pass means offline invariants hold for the tested paths. A synthetic eligibility pass does not mean a market is eligible. A backtest/shadow result is not a real fill, audited challenge account balance, or profitability claim. Feature 002’s next-bar-open execution and its explicit costs remain unchanged. Its `ReplayResult.limitations` states that `initial_cash` does not establish ownership or withdrawability and that generic commission/slippage do not represent official costs. Credit fees, forced liquidation, registration balances, spread as a distinct cost, and special challenge settlement are not modeled. Do not report model return as net credit-account profit or as withdrawable cash; do not treat unknown costs/triggers as zero or use the unrelated plan example as a hackathon rate. Disclose dataset provenance, missingness, assumptions and limitations in any report.

## Judge handoff

A real submission should provide (1) exact public commit and run ID, (2) configuration/data hashes, (3) architecture and algorithm/risk explanation, (4) complete decision/trade-event export, (5) exact offline reproduction commands, (6) a separate demonstration recording, and (7) known unresolved organizer confirmations. Do not expose credentials or private account data in the handoff.
