# Market restrictions and eligibility contract

**Evidence status:** Challenge-specific source is the user-provided brief (`USER-WALLEX-HACKATHON-BRIEF`); no market/eligibility fact is independently official-verified. Internal controls below are `INFERRED` safety requirements, not claimed Wallex API fields or exchange semantics.

## Only one canonical pair registry

- Verbatim source: [`config/challenge/wallex_disabled_spot_pairs_raw.txt`](../../config/challenge/wallex_disabled_spot_pairs_raw.txt). Do not hand-edit the derived list as a second source of truth.
- Derived runtime registry: [`config/challenge/wallex_disabled_spot_pairs.json`](../../config/challenge/wallex_disabled_spot_pairs.json). It records the source hash and canonical uppercase `BASE/QUOTE` list.
- The supplied source has 345 lines, all valid and unique; canonical count 345; 0 duplicate and 0 malformed entries. The parser reports both duplicate pairs and duplicate-excess counts. If a future attachment has malformed/duplicate input, preserve it raw, report each issue, and refuse to use an invalid registry until reconciled. Never silently deduplicate the evidence.
- List SHA-256: `48a9d12c5660929bf2044c30535864eb4f008d0580aa3e0cf75f5b528242eba0`.
- Quote assets found: `TMN`, `USDT`; list membership is not authorization. Internal quote allowlist is `TMN` only until settlement conversion is verified.
- The user-provided list may be outdated. It is not a real-time feed and does not establish that a non-listed pair exists, is spot, is active, orderable, challenge-eligible or permitted today.

## Fail-closed decision

`src/wallex_research/challenge.py` implements a pure local decision and returns machine-readable decision/reason codes. Every condition must pass. Unknown, missing, stale, future-dated, contradictory, malformed, untrusted or unconfigured facts produce denial; no network call or exchange adapter is used.

1. Challenge policy is explicitly enabled for the requested offline evaluation context. The repository’s defaults keep live trading off; live execution is not implemented.
2. Pair parses as strict ASCII alphanumeric `BASE/QUOTE` and is normalized uppercase. Whitespace/underscore/extra separators are rejected rather than guessed.
3. Pair is absent from an intact raw-hash-verified disabled registry. Registry errors block.
4. Evidence identifies an explicitly trusted, provenance-backed, fresh metadata source with an official-source URL and content hash. Synthetic fixtures are allowed only in explicitly test-only mode and remain warned as synthetic.
5. Metadata has explicit, non-contradictory Spot/active/enabled/orderable states. `not disabled` is never sufficient. Leveraged tokens, margin, borrow, short, futures, options and derivatives are denied.
6. Quote is explicitly enabled and has a documented permitted settlement path. No inferred conversion or stale quote valuation is accepted. Current internal policy allows only TMN.
7. Quantity/price precision, tick/step and minimum-order-value semantics are explicitly verified, finite and positive, and requested order conforms. No Wallex field names or exchange behavior are inferred by this contract.
8. Strategy approval, algorithmic decision origin (manual intent is denied), and independent risk approval are all explicit. Missing or null risk caps veto.

The policy has no configured maximum metadata age. Until a reviewed internal freshness threshold and timestamp contract exist, real-market eligibility is denied. A synthetic test-only path exercises the algorithm but cannot be used to authorize a challenge order.

## Conduct and operating mode

Spot-only; no margin, leverage, borrowing, shorting, derivatives, withdrawals, transfers, deposits or manual performance trades. Prohibit self/coordinated/wash trading, artificial volume, manipulation and excluded markets. Backtest, shadow and dry-run are isolated from submission. A `live` request returns `LIVE_EXECUTION_NOT_IMPLEMENTED`; it does not make a request. No mode toggle can override this.

For a future, separately approved run, require two-person policy review, immutable run configuration, pinned code/data/model identifiers, reconciled balances/open orders, current market metadata, fresh data/signal, complete risk limits, known cost estimates, and a tested emergency stop. These are internal guardrails, not organizer-confirmed exchange requirements.

## Configuration and maintenance procedure

1. Obtain a dated, traceable organizer source and preserve its exact bytes separately; do not overwrite the old source.
2. Compare old and new pair lists; emit added/removed/duplicate/malformed deltas. Have a second reviewer confirm spelling, quote, source hash and effective time.
3. Rebuild canonical JSON from raw source and update the source-register record/hash and evidence status. Do not claim currentness without an official update.
4. Regenerate with `python3 scripts/build_challenge_pair_registry.py --write`, verify with `python3 scripts/build_challenge_pair_registry.py --check`, then re-run `PYTHONPATH=src python3 -m unittest discover -s tests -p 'test_challenge.py' -v` and source validation.
5. Until confirmation and successful validation, keep the old list as historical user-provided input and block live use.
