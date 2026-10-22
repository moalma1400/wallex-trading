# Requirements Checklist: Historical Market Data

- [x] Feature 003 is separate and preserves Features 001/002 and the fixed session branch.
- [x] No network, credentials, private account data, live orders, transfer, withdrawal or live trading is authorized.
- [x] Wallex docs are evidence only; host/auth/availability/precision/time semantics remain unresolved where conflicting.
- [x] Raw/normalized separation, versioned schemas, provenance, hash and idempotency requirements are explicit.
- [x] Replay readiness requires caller-supplied completeness/freshness/symbol/precision policies.
- [x] Local CSV/JSON import, immutable raw storage and deterministic normalized output implemented.
- [x] Audit produces JSON/CSV/Markdown and blocks ineligible replay export.
- [x] Feature 002 replay compatibility and offline repository validators pass; exact commands/results are recorded in the Feature 003 research log. Exact-byte OpenAPI archival remains explicitly incomplete.
