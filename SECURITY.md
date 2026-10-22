# Security and safe trading-project boundaries

## Credential and personal-data handling

- Never commit API keys, tokens, cookies, passwords, recovery codes, wallet information, account identifiers, or other personal/account data.
- Never request or use real Wallex credentials for research. Keep `.env.example` placeholders fictional and empty of valid secrets.
- If a secret is accidentally exposed, stop using it, notify the owner, revoke/rotate it through the official account interface, remove it from current files and history using an owner-approved process, and treat it as compromised. Do not paste it into issues or chat.
- Do not collect private data from Wallex or other users. Prefer generic, synthetic examples.

## Trading actions and current phase

Features 001–004 remain documentation or local/offline research and challenge-control work. Feature 005 is approved only for a narrowly scoped public, read-only **Spot market-data** adapter through a verified Smart98-mediated contract, plus offline tests and documentation, after its evidence/security/architecture gates pass. T003 remains open/blocked: a user-supplied report text records tool-specific observations, but authoritative Smart98/version/permission contracts and rate-limit, timeout, pagination, and order-lifecycle evidence remain unresolved. The existing `src/mcp_adapter/` parser/provider seam is not a live Smart98 connection and is not production-enabled. Public documentation or an operator-reported tool invocation does not itself grant account permission.

No direct Wallex requests or direct-access fallback are permitted. Do not install/configure MCP servers or request/create credentials. Private-account reads, live orders/cancellations/amendments, transfers, deposits, withdrawals, wallet actions, Margin, leverage, borrowing, shorting, derivatives, OTC execution, and other state-changing actions remain out of scope. Tests, CI, replay, backtests, shadow, and dry-run must remain offline with respect to Wallex and Smart98.

Any future real exchange use requires verified challenge rules and dedicated-account permissions, exact tool contracts, explicit owner activation, a deterministic risk/reconciliation review, least-privilege controls, and an independent, current jurisdiction-specific legal/compliance gate (including sanctions and access restrictions). Passing this gate cannot be claimed by this project or guaranteed. Paper simulation remains deterministic, offline, and separated from any future external adapter.

## Reporting

Report suspected repository exposure or credential leaks privately to the repository owner rather than opening a public issue. This repository is private, but private status is not a substitute for credential hygiene.
