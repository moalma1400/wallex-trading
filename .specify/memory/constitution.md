# Wallex Trading Constitution

## Core Principles

### I. Specification Before Implementation
Specifications and measurable acceptance criteria precede implementation. Scope, assumptions, and exclusions must be explicit; changes to agreed requirements are recorded and reviewed.

### II. Evidence-First Documentation
Every material factual claim about Wallex must link to an identifiable, authoritative source. Distinguish verified observations, statements made by official documentation, inference, assumptions, and unresolved questions. Record conflicts instead of silently reconciling them.

### III. Currency and Provenance
Prefer official documentation currently presented by Wallex. Preserve useful legacy evidence with a clear legacy label. Record exact URLs, retrieval time in UTC, publication/update dates only when supplied, and currentness confidence. Do not infer undocumented behavior.

### IV. Traceability and Reviewability
Changes must trace from specification through plan, tasks, artifacts, and validation evidence. Research inventories and validation should be reviewable, reproducible, and explicit about gaps.

### V. Financial Credential and Personal-Data Protection
Never commit API keys, access tokens, cookies, account identifiers, personal data, or secrets. Do not create or use a real Wallex API key for documentation research. Use placeholders only and minimize any sensitive examples.

### VI. Challenge-Scoped Autonomous Trading Authorization
This repository supports a time-bounded trading competition, not a bug-bounty engagement. Once the owner explicitly activates a verified challenge run, permitted Spot trading decisions and order lifecycle actions may execute autonomously through verified Smart98-mediated tools without per-order human approval; manual trades do not count as algorithmic performance. This authorization is strictly limited to the verified dedicated challenge account, official competition window and rules, permitted Spot markets, and configured deterministic risk limits. It does not authorize withdrawals, transfers, deposits, wallet operations, margin, leverage, borrowing, shorting, derivatives, OTC execution, market manipulation, wash/self-trading, or any unverified action. Public documentation must never be probed by direct production API calls.

### VII. Risk Before Automation
Document risk controls, permissions, failure handling, and a defined test process before implementing automated trading. A documented capability is not proof of runtime availability, authorization, safety, or suitability. Do not claim a strategy is profitable or safe without appropriate evidence.

### VIII. Current Phase Boundary and Integration Mediation
Feature 005 is approved to implement a narrowly scoped Smart98-mediated adapter for verified public, read-only Wallex Spot market data, using only actual documented/observed tool contracts and sanitized fixtures. Feature 007 is approved to implement a standalone, repository-owned Model Context Protocol (MCP) server for verified public, read-only Wallex Spot market data, as an independent alternative to Smart98 mediation. Smart98 remains an optional MCP host/client for this repository; it is not a mandatory dependency of the standalone runtime. All application access intended for Wallex must pass through either (a) a verified Smart98-mediated interface, or (b) the repository-owned standalone MCP server defined by Feature 007. Direct Wallex API calls and direct-access fallbacks are prohibited. Public read-only data retrieval through verified Smart98 tools or the standalone MCP server may be used to validate the adapter when the tool contract and access path are confirmed; never experiment against direct Wallex production endpoints or use private credentials.

Backtesting, shadow testing, dry-run, and unit/CI tests remain offline and must never submit real orders. Actual challenge-account order execution is a separate activation boundary: implementation must fail closed until the official challenge window/rules, dedicated challenge-account permissions, allowed Spot markets, actual Smart98 order-tool contracts, deterministic risk limits, reconciliation, and an explicit owner activation decision are recorded. Once that activation gate is satisfied, permitted Spot orders may run autonomously without per-order approval. This does not authorize prohibited or unverified account actions. Strategy, market, timeframe, fees, capital, and risk values must come from verified challenge rules or explicit owner inputs; never invent defaults.

### IX. Competition Rules, Eligibility, and Compliance
This project must not treat bug-bounty restrictions as the governing product model for the trading hackathon. The owner-provided challenge brief is user-provided evidence until independently confirmed; claims about official permissions, market eligibility, account access, scoring, and settlement must retain that provenance. Before a live challenge run, record the official rules available to the team, competition window, permitted market list, dedicated challenge-account permissions, and any applicable access/compliance constraints; where jurisdiction, sanctions, exchange eligibility, or local law create a material question, obtain current qualified compliance/legal review. Do not claim that this constitution establishes legal eligibility or overrides exchange terms or local law. If eligibility or a required permission is unknown or contradictory, do not activate live execution.

## Development and Research Constraints

- Use official Wallex sources as primary evidence; identify non-official sources distinctly if ever needed.
- Keep user-facing trading knowledge Persian-first while preserving exact English API identifiers, paths, headers, fields, and enum values.
- Do not copy entire source pages. Write concise, structured original summaries.
- Record inaccessible pages, broken navigation, contradictory claims, and open questions honestly.
- Offline software must be deterministic, network-free, and use only caller-supplied local data. Do not embed example market, timeframe, fee, capital, strategy, leverage, or risk settings as defaults.
- Implement Wallex market-data and any later authorized challenge order integration only through Smart98 or the Feature 007 standalone MCP server, using verified contracts; never invent transport, auth, schemas, tool names, permissions, or configuration. Keep public data, challenge-account reads, and state-changing order tools explicitly separated.
- Avoid unnecessary packages, services, databases, bots, credentials, or infrastructure.
- No license is selected yet; do not add one without owner approval.

## Governance

This constitution governs all specifications, plans, tasks, research, implementation, and review in this repository. Any feature that conflicts with it must be revised or explicitly deferred; the constitution itself can be amended only through a reviewed, documented change. Every pull request must check evidence quality, credential hygiene, trading-boundary compliance, and traceability. Acceptance criteria are not considered met without recorded validation evidence. Where user decisions are required, document the question and do not substitute an invented requirement.

**Version**: 1.3.0 | **Ratified**: 2026-10-21 | **Last Amended**: 2026-10-22

### Amendment record

Version 1.1.0 authorized local offline research only. Version 1.2.0 records the owner's explicit competition-scope decision: verified public read-only Spot market data may be integrated through Smart98, and a separately gated, owner-activated challenge run may autonomously execute only verified permitted Spot orders without per-order approval. Direct Wallex calls, prohibited products/actions, unverified tools, and live execution before the activation gate remain prohibited.

Version 1.3.0 records the owner's explicit standalone-MCP decision: Feature 007 authorizes a repository-owned standalone Model Context Protocol server as an independent alternative to Smart98 mediation for verified public, read-only Spot market data. Smart98 is demoted from a mandatory dependency to an optional MCP host/client. The standalone server may access only officially documented Wallex endpoints approved for this feature; the initial capability is public read-only Spot market data. Authenticated reads require a separately verified endpoint, explicit secret handling, and an isolated manual test workflow. No order or other state-changing capability is implemented by this feature. Offline CI, paper replay, and backtesting remain incapable of performing authenticated requests or real trading actions. Unverified endpoints, undocumented permissions, and ambiguous behaviors fail closed. This amendment does not authorize live trading, order placement, cancellation, deposits, transfers, withdrawals, or any other state-changing account operation.