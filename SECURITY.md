# Security and safe trading-project boundaries

## Credential and personal-data handling

- Never commit API keys, tokens, cookies, passwords, recovery codes, wallet information, account identifiers, or other personal/account data.
- Never request or use real Wallex credentials for research. Keep `.env.example` placeholders fictional and empty of valid secrets.
- If a secret is accidentally exposed, stop using it, notify the owner, revoke/rotate it through the official account interface, remove it from current files and history using an owner-approved process, and treat it as compromised. Do not paste it into issues or chat.
- Do not collect private data from Wallex or other users. Prefer generic, synthetic examples.

## Trading actions

This phase is documentation-only. No production REST request, live WebSocket connection, order placement/cancellation/amendment, transfer/withdrawal, or account-setting change is authorized. Public documentation does not itself grant account permission. A future feature involving account access must have its own reviewed specification, explicit user approval, least-privilege permissions, risk controls, and test plan before implementation or use.

## Reporting

Report suspected repository exposure or credential leaks privately to the repository owner rather than opening a public issue. This repository is private, but private status is not a substitute for credential hygiene.
