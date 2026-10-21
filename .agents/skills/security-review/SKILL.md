---
name: security-review
description: Review repository changes for credential exposure, personal data, network side effects, and unsafe execution paths.
compatibility: Repository-local review; no real credentials or accounts are used.
metadata:
  owner: wallex-trading
  scope: security
---

# Trading-research security review procedure

1. Read `SECURITY.md`, `.gitignore`, `.env.example`, and the constitution. Never request, create, accept, or store a real exchange key, cookie, token, wallet address, user ID, or account export.
2. Search changed files, examples, tests, logs, fixtures, and prompts for credentials and personal/account data. Use only conspicuously synthetic, non-routable identifiers and fake market rows.
3. Trace imports and entry points for HTTP, WebSocket, browser, subprocess, shell, credential parsing, and exchange SDK behavior. This phase allows no external requests, API clients, live feed, private account data, order endpoint, cancellation, transfer, withdrawal, or exchange execution path.
4. Keep `.env.example` empty placeholders; do not log secrets or raw user data. Tests and validators must run without network access.
5. Ensure paper results cannot be sent to an exchange by accidental configuration or environment variable. There is no live adapter to enable.
6. Report limitations of automated secret scans; do not call a clean scan proof of security. Escalate accidental exposure privately and treat it as compromised.
