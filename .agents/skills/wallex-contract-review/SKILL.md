---
name: wallex-contract-review
description: Compare documented Wallex API contracts while preserving modern, generated, and legacy differences.
compatibility: Requires registered official source IDs and URLs; documentation analysis only.
metadata:
  owner: wallex-trading
  scope: contract-review
---

# Wallex contract review procedure

1. Read the relevant source-register entries and fetch the exact official page/spec linked there; identify whether it is product prose, generated OpenAPI, current-looking guide, or legacy reference.
2. Transcribe HTTP method, host, path, version prefix, auth scheme/header, parameters, JSON field names/types, enums, status codes, pagination, errors, and stated limits verbatim. Cite every material claim by source ID and exact URL.
3. Keep OpenAPI `host`, endpoint examples, and developer-overview base URL separate. Flag leading `//`, `.com` versus `.ir`, route or payload disagreements, and missing fields; do not normalize or silently choose one.
4. Distinguish documented contract from runtime availability. No live requests or credentials are allowed. Samples and schemas are not proof of permissions, current fees, valid symbols, or account eligibility.
5. Add a discrepancy entry with each side's exact evidence, conservative interpretation, confidence, and unresolved question. Update `docs/api/` and Persian-first `docs/fa/` summaries.
6. Account-changing, margin, wallet, withdrawal, and private-data endpoints are still only documentation evidence and must never be executed. Do not prepare executable request payloads for a user's account.
7. Mark a page `reviewed` only after enough content was inspected to support its summary; use `in_progress` when returned content is truncated. Contract review never grants integration approval.
