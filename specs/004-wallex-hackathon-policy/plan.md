# Implementation Plan: Wallex Hackathon Knowledge Base and Offline Policy

**Branch**: `arena/81f9fa39-wallex-trading` (fixed Arena branch) | **Date**: 2026-10-21 | **Spec**: [spec.md](spec.md)

## Summary

Extract only the explicitly supplied market list, preserve raw bytes, derive hash-bound canonical JSON, register the attachment as user-provided evidence, and build local Python policy/evidence contracts. Link challenge KB, restrictions, operator/judge, and demo docs; update reusable research skills and preserve Features 001–003. Every policy is offline and fail-closed; no live adapter or real request is in scope.

## Technical context

- Python 3.11+ standard library and `unittest`; no new runtime dependency.
- Local JSON config and text appendix with source SHA-256; unknown numeric thresholds and cutoff stay null.
- Pair syntax is ASCII alphanumeric `BASE/QUOTE`, canonical uppercase. Raw source is retained independently; canonical list is derived.
- Pure policy evaluation and local JSONL decision events; no I/O to Wallex. Synthetic fixture is explicitly test-only.
- Financial values use decimal-safe inputs; event schema contains version, UTC time, sequence, code/config/strategy/source identifiers and deterministic event ID.
- Reuse Feature 002 offline replay, next-bar-open execution and cost interfaces without modification.

## Design decisions

1. The uploaded Markdown is treated as user-provided evidence; provenance record has null URL/retrieval time. It is not labeled official.
2. Keep one raw list and one derived machine registry. Narrative docs link to these files rather than replicate their entries.
3. Unknown metadata freshness/cutoff/fee/risk limits block. No safe numeric defaults are asserted as Wallex/organizer requirements.
4. Internal allowed quote is TMN only until conversion semantics are evidenced; USDT conversion is not guessed.
5. Challenge pair absence from the disabled registry never implies active, orderable or permitted.
6. `backtest`, `shadow` and `dry_run` only record simulated intent/results. `live` has no execution path.
7. Settlement only becomes ready at exact verified cutoff with reconciled balances, known costs, realized result and zero non-TMN inventory. Estimates remain distinct from official valuation.
8. AI schema validation/fallback and event provenance are contracts only. No provider/model or fabricated output explanation is introduced.
9. Feature 002 remains the causal baseline: a completed observation leads to next-bar-open simulation with explicit costs.

## Project structure

```text
config/challenge/                 # raw/derived pair list and fail-closed policy
scripts/build_challenge_pair_registry.py # deterministic derived-list check/write
src/wallex_research/challenge*.py # eligibility, risk, isolated mode, settlement
src/wallex_research/decision_log.py # versioned offline event contract
 tests/test_challenge.py           # offline safety and provenance tests
 docs/knowledge-base/              # rules, restrictions, operator/judge guides
 specs/004-wallex-hackathon-policy/ # canonical Spec Kit feature artifacts
.agents/skills/                    # reusable challenge-specific procedures
```

## Risks and limitations

A user attachment can be incomplete or outdated. The raw disabled list is not a live registry. No exact official challenge URL, audio, current orderability, settlement route, risk limits, or cutoff is presently evidenced. Strict fail-closed behavior therefore prevents real eligibility/settlement conclusions. This feature is not execution readiness, a profitability claim, or legal/compliance approval.
