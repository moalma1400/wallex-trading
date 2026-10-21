# Repository-local agent instructions

- Follow `.specify/memory/constitution.md` and the current feature's canonical Spec Kit artifacts.
- Follow Spec Kit's sequence: constitution, specify, clarify when material ambiguity remains, plan, tasks, analyze, implement, and converge/verify. Use generated skills in `.agents/skills/` as the procedure; do not claim to have invoked a skill that was not actually invoked. This Arena environment has no verified native Spec Kit integration, so apply the generated skill instructions manually and document this limitation.
- Do not rewrite or replace canonical Spec Kit templates, scripts, manifests, workflows, or skills with a home-grown process. Keep the generic integration command files in `.agents/skills/`; do not add private assistant state there.
- Research only public sources without bypassing access controls. Never call production endpoints for experimentation or use a Wallex key.
- For each material claim, include a direct source URL and source ID. Separate direct official statements from interpretation, assumptions, and unresolved questions. Keep retrieval timestamps in UTC and do not invent publication dates.
- Persian-first user-facing knowledge; preserve exact endpoint paths, HTTP methods, parameter names, headers, and enum values.
- Do not state a capability is current merely because it appears in an old sample. Record official-source discrepancies in `docs/research/discrepancies.md`.
- The current implementation phase permits only local/offline, strategy-neutral research tools using synthetic or user-supplied files. Never add Wallex/Smart98 network adapters, live or paper integrations to live feeds, credentials, account data/actions, or leveraged execution. Keep any paper ledger entirely simulated and fail-closed. For any separately approved future integration, all Wallex API/MCP access intended for the trading agent must be mediated through Smart98; never connect the trading application directly to Wallex. Smart98's technical interface is unverified, so do not invent its transport, auth, tools, schemas, or config.
- Never select a strategy, market, timeframe, fee, leverage, capital amount, or risk tolerance for the user. Require explicit inputs for simulation assumptions; do not treat examples as exchange evidence.
- Run `python3 scripts/validate_sources.py`, `python3 scripts/validate_doc_links.py`, the applicable offline test suite, and `git diff --check` before proposing changes. Validators and tests must not use the network.
- Do not commit secrets, private account data, generated caches, or local tool environments.

## Feature 004 — challenge-specific constraints

- Treat `docs/knowledge-base/` and `specs/004-wallex-hackathon-policy/` as the challenge knowledge base. The uploaded brief is user-provided evidence, not independently official-verified; use the five evidence tags defined there. Keep proposed scoring explicitly proposed.
- Preserve the raw disabled-market list verbatim and derive a single canonical list; absence from exclusions is never authorization. Challenge eligibility, risk and settlement must fail closed on missing, stale, contradictory or untrusted evidence.
- Spot-only. Never add margin, leverage, borrowing, shorting, derivatives, deposits, transfers, withdrawals, account access or live order submission. Backtest/shadow/dry-run remain offline and Feature 002's next-bar-open/cost contracts stay unchanged.
- Do not store member PII, credentials, or private account/order data. A cleaned transcript supplied inline is not the original audio; no audio was available for listening or verification, so do not claim audio review/transcription.
