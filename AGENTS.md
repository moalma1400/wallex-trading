# Repository-local agent instructions

- Follow `.specify/memory/constitution.md` and the current feature's canonical Spec Kit artifacts.
- Follow Spec Kit's sequence: constitution, specify, clarify when material ambiguity remains, plan, tasks, analyze, implement, and converge/verify. Use generated skills in `.agents/skills/` as the procedure; do not claim to have invoked a skill that was not actually invoked. This Arena environment has no verified native Spec Kit integration, so apply the generated skill instructions manually and document this limitation.
- Do not rewrite or replace canonical Spec Kit templates, scripts, manifests, workflows, or skills with a home-grown process. Keep the generic integration command files in `.agents/skills/`; do not add private assistant state there.
- Research only public sources without bypassing access controls. Never call production endpoints for experimentation or use a Wallex key.
- For each material claim, include a direct source URL and source ID. Separate direct official statements from interpretation, assumptions, and unresolved questions. Keep retrieval timestamps in UTC and do not invent publication dates.
- Persian-first user-facing knowledge; preserve exact endpoint paths, HTTP methods, parameter names, headers, and enum values.
- Do not state a capability is current merely because it appears in an old sample. Record official-source discrepancies in `docs/research/discrepancies.md`.
- Never introduce strategy code, order execution, account changes, credential collection, or unnecessary dependencies in the current phase.
- Run `python3 scripts/validate_sources.py`, `git diff --check`, and applicable link/consistency checks before proposing changes. Validator must stay offline.
- Do not commit secrets, private account data, generated caches, or local tool environments.
