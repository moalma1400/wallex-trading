# Wallex Trading

**Wallex trading project — official documentation, SDD specifications, and trading-system preparation.**

## Purpose and current phase

This private repository establishes a Persian-first, source-backed knowledge base about publicly available official Wallex trading and API documentation. The current phase is documentation research and specification. It does **not** implement a trading strategy, connect to a Wallex account, call production APIs, place or cancel orders, transfer assets, or provide individualized buy/sell recommendations.

Documented capabilities do not prove that a feature is currently available at runtime, suitable or profitable, or permitted for every account or use. Fees, symbols, limits, access, and platform behavior can change; check the dated official sources before relying on any value.

## Spec-Driven Development

The project uses the official [GitHub Spec Kit](https://github.com/github/spec-kit) workflow. The pinned CLI version and initialization notes are recorded in [`.specify/init-options.json`](.specify/init-options.json) and [Spec Kit setup](specs/001-wallex-official-documentation-inventory/spec-kit-setup.md). Canonical templates, scripts, workflows, and agent-neutral command skills are retained under `.specify/` and `.agents/skills/`. Specifications and acceptance criteria come before implementation; plans, tasks, analyses, and validation evidence should remain linked.

## Start here

- [Feature specification](specs/001-wallex-official-documentation-inventory/spec.md)
- [Research source register](docs/research/source-register.yaml)
- [Coverage matrix](docs/research/coverage-matrix.md)
- [Persian knowledge base](docs/fa/README.md)
- [Discrepancy register](docs/research/discrepancies.md)
- [Unresolved questions](docs/research/unresolved-questions.md)
- [Research log](docs/research/research-log.md)

## Contributing and evidence

Read [AGENTS.md](AGENTS.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [SECURITY.md](SECURITY.md) before making changes. Report missing sources, inaccessible pages, or conflicting official statements by opening an issue or pull request with exact URLs and retrieval details. Update the machine-readable register and coverage matrix whenever the source landscape changes. Cite material claims by stable source ID and direct URL; label official statements, observations, inferences, assumptions, and unknowns distinctly.

Future features must first specify objectives, supported markets, assumptions, required permissions, risk limits, and measurable acceptance criteria. Strategy or execution work requires separate review and explicit approval before any account-changing action.

## License

No license has been selected. All rights remain with their respective owners; do not assume permission to reuse repository content beyond applicable law and GitHub's service terms.
