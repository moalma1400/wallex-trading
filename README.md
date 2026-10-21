# Wallex Trading

**Wallex trading project — official documentation, SDD specifications, and trading-system preparation.**

## Purpose and current phase

This private repository maintains a Persian-first, source-backed knowledge base about official Wallex trading/API documentation and an offline, strategy-neutral research kernel. Feature 001 remains an incomplete documentation research effort; Feature 002 adds only local data validation, deterministic replay/backtest calculations, explicit risk gates, and simulated paper-ledger mechanics over synthetic or user-supplied files. Neither feature implements a strategy, fetches data from Wallex/Smart98, connects to an account or live feed, calls production APIs, places/cancels orders, transfers assets, or provides individualized buy/sell recommendations. Feature 004 captures a user-provided Wallex/Starcoach hackathon brief as provenance-tagged knowledge and adds offline fail-closed eligibility/risk/settlement controls; it does not independently verify challenge policy or implement live execution.

Documented capabilities do not prove that a feature is currently available at runtime, suitable or profitable, or permitted for every account or use. Fees, symbols, limits, access, and platform behavior can change; check the dated official sources before relying on any value. Official U.S. Treasury/OFAC materials in the research record also describe sanctions designation and potential non-U.S.-person exposure; this repository is not legal advice, and no use or transaction should proceed without independent, current legal/compliance review.

## Spec-Driven Development

The project uses the official [GitHub Spec Kit](https://github.com/github/spec-kit) workflow. The pinned CLI version and initialization notes are recorded in [`.specify/init-options.json`](.specify/init-options.json) and [Spec Kit setup](specs/001-wallex-official-documentation-inventory/spec-kit-setup.md). Canonical templates, scripts, workflows, and agent-neutral command skills are retained under `.specify/` and `.agents/skills/`. Specifications and acceptance criteria come before implementation; plans, tasks, analyses, and validation evidence should remain linked.

## Start here

- [Feature 001: official documentation inventory](specs/001-wallex-official-documentation-inventory/spec.md) — in progress
- [Feature 002: offline research kernel](specs/002-offline-research-kernel/spec.md) — initial offline slice delivered
- [Feature 003: historical market data and quality](specs/003-historical-market-data/spec.md) — local-only import/audit/export; no network provider
- [Feature 004: hackathon knowledge base and offline policy](specs/004-wallex-hackathon-policy/spec.md) — user-brief provenance, fail-closed controls; no live adapter
- [Wallex/Starcoach challenge knowledge base](docs/knowledge-base/README.md) — rules, restrictions, judge reproduction and demo checklist
- [Repository roadmap](specs/ROADMAP.md)
- [Feature 003 quickstart](specs/003-historical-market-data/quickstart.md)
- [Feature 002 quickstart](specs/002-offline-research-kernel/quickstart.md)
- [Research source register](docs/research/source-register.yaml)
- [Coverage matrix](docs/research/coverage-matrix.md)
- [Persian knowledge base](docs/fa/README.md)
- [Repository-specific reusable skills](.agents/skills/README.md) (Markdown guidance; not verified slash commands)
- [Discrepancy register](docs/research/discrepancies.md)
- [Unresolved questions](docs/research/unresolved-questions.md)
- [Research log](docs/research/research-log.md)

## Contributing and evidence

Read [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md) before making changes. Report missing sources, inaccessible pages, or conflicting official statements by opening an issue or pull request with exact URLs and retrieval details. Update the machine-readable register and coverage matrix whenever the source landscape changes. Cite material claims by stable source ID and direct URL; label official statements, observations, inferences, assumptions, and unknowns distinctly.

Future features must first specify objectives, supported markets, assumptions, required permissions, risk limits, and measurable acceptance criteria. Strategy or execution work requires separate review and explicit approval before any account-changing action.

## License

No license has been selected. All rights remain with their respective owners; do not assume permission to reuse repository content beyond applicable law and GitHub's service terms.
