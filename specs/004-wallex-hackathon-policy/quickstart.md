# Quickstart — offline challenge-policy checks

This feature is strictly local. It does not request market data, access an account, or place orders. Use synthetic fixtures only for tests. No challenge credentials, private account data, or PII are needed.

From repository root:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_challenge.py' -v
PYTHONPATH=src python3 -m unittest discover -s tests -v
python3 scripts/build_challenge_pair_registry.py --check
python3 scripts/validate_sources.py
python3 scripts/validate_doc_links.py
```

Inspect the user-provided challenge policy and provenance without treating null configuration as permission:

```bash
python3 -m json.tool config/challenge/wallex_hackathon_policy.json
python3 -m json.tool config/challenge/wallex_disabled_spot_pairs.json
sha256sum config/challenge/wallex_disabled_spot_pairs_raw.txt
```

Risk-limit values and official start/cutoff/freshness are unresolved. Missing values deliberately block proposals/settlement. `tests/fixtures/challenge_market_metadata.json` is synthetic and cannot authorize real trading. `live` mode returns blocked; there is no order adapter. For run/audit schema and judge handoff, see [reproduction guide](../../docs/knowledge-base/judge-reproducibility.md).
