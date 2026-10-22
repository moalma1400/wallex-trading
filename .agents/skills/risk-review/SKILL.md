---
name: risk-review
description: Review offline Spot research controls without inventing a user risk profile.
compatibility: Uses explicit caller-provided local simulation limits only.
metadata:
  owner: wallex-trading
  scope: risk-controls
---

# Research risk review procedure

1. Determine which inputs are policy choices. Do not select or suggest the user's capital, maximum exposure, loss tolerance, time horizon, market, leverage, or strategy.
2. Require explicit non-default limits for any simulation. Verify negative exposure, values above the supplied limit, invalid/empty configuration, shorting, and leverage fail closed.
3. Prefer rejection to silent clamping, silent defaults, hidden retries, or assumptions inferred from public docs. Preserve a visible audit trail of simulated inputs and events.
4. Test deterministic failure behavior, cash conservation, cost deduction, and drawdown calculation with synthetic data. Note modeled risks omitted by the simplified engine (liquidity, gaps, latency, queue position, precision, venue rejection, and live failures).
5. A local risk limit is not a recommendation, safety guarantee, or permission to use an exchange. Keep margin/leverage execution excluded.
6. Any real exchange use remains blocked until a separate current contract/security/risk review and jurisdiction-specific legal/compliance review; never imply legality is guaranteed.

## Challenge-specific gate

- For Feature 004, load limits from `config/challenge/wallex_hackathon_policy.json`; null or missing limits are an explicit veto, not an invitation to choose defaults. The loader ignores numeric values unless configuration status is `REVIEWED_INTERNAL` with evidence status. These are internal controls, not official Wallex/organizer limits.
- Require independently sourced capital and available-balance evidence, complete official provenance for non-synthetic evidence, independent strategy approval, reconciled local state, fresh trusted metadata, known fees/costs, and a supported settlement quote. Synthetic evidence clears gates only under an explicit offline-fixture flag; an unverified brief baseline is a blocker, not only a warning. Do not treat a TMN buy-balance check as sufficient for a Spot sell; until base-asset balance/fee handling is validated, sell proposals must block.
- Preserve machine-readable blocker reasons and deterministic audit references. Trace all callers before claiming a veto protects an intent: the risk evaluator is not connected to the record-only dispatcher or any order-submission path. Do not add an order-submission action.
