# Security and safe trading-project boundaries

## Credential and personal-data handling

- Never commit API keys, tokens, cookies, passwords, recovery codes, wallet information, account identifiers, or other personal/account data.
- Never request or use real Wallex credentials for research. Keep `.env.example` placeholders fictional and empty of valid secrets.
- If a secret is accidentally exposed, stop using it, notify the owner, revoke/rotate it through the official account interface, remove it from current files and history using an owner-approved process, and treat it as compromised. Do not paste it into issues or chat.
- Do not collect private data from Wallex or other users. Prefer generic, synthetic examples.

## Trading actions

This phase permits only local/offline, strategy-neutral research tooling over synthetic or user-supplied files. No production REST request, public-data fetch, live WebSocket connection, account access, API key, order placement/cancellation/amendment, transfer/withdrawal, or account-setting change is authorized. There is no exchange adapter in scope. Public documentation does not itself grant account permission.

Any future proposal for real exchange use requires a separate reviewed specification, explicit scope approval, security and risk review, least-privilege permissions, and an independent, current jurisdiction-specific legal/compliance gate (including sanctions and access restrictions). Passing this gate cannot be claimed by this project or guaranteed. Leveraged/margin execution, transfers, and withdrawals remain excluded. Paper simulation must be deterministic, offline, and clearly separated from any future exchange adapter.

## Reporting

Report suspected repository exposure or credential leaks privately to the repository owner rather than opening a public issue. This repository is private, but private status is not a substitute for credential hygiene.
