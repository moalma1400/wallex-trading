---
name: smart98-interface-boundary
description: Preserve the mandatory Smart98 mediation boundary without guessing Smart98, Wallex API, or Wallex MCP contracts.
compatibility: Use only for repository research/documentation unless a separate approved feature supplies authoritative Smart98 and upstream contract material.
metadata:
  owner: wallex-trading
  scope: future-interface-boundary
---

# Smart98 interface boundary procedure

1. Treat the user's project-context statement that Smart98 is the organizational AI Agent platform and intended mediation layer as a requirement only. Do not infer Smart98 product features, runtime availability, supported MCP transports, registration, tool discovery, auth, credentials, schemas, timeouts, logs, or Wallex compatibility.
2. Any future Wallex API or Wallex MCP access for the trading agent MUST pass through an explicitly approved Smart98-mediated integration. Never design a direct Wallex connection from the trading application as a fallback.
3. Keep four layers distinct in documentation: Wallex API capabilities, an authoritative Wallex MCP implementation (if verified), Smart98's platform/interface, and this repository's agent strategy/validation/replay. Record evidence and status per layer.
4. Do not invent URLs, authentication, request/response fields, tool/MCP names, rate limits, permissions, capabilities, or package names. Ask for authoritative public docs or an owner-reviewed contract; record source, version/date, completeness, and unresolved details.
5. Propose only a provider-neutral internal `MarketDataPort` for normalized, provenance-bearing read-only observations. This is an internal design label, not an external tool name or schema. Keep provider selection configurable at the domain boundary, but unknown/unconfigured providers fail closed. Strategy code must not import a Smart98 SDK or Wallex MCP implementation.
6. Separate public read-only market data from account-sensitive reads and order-changing tools. Account-sensitive reads and all order placement/amendment/cancellation remain disabled. A tool's presence is not authorization. Shadow may only observe approved read-only data and record proposed decisions; it must never submit, amend, or cancel orders.
7. Deterministic data validation, Spot eligibility, and risk vetoes remain outside the language model. Unknown, stale, contradictory, inactive, or prohibited markets remain blocked. Exchange credentials/private keys must never enter model context, repository files, fixtures, or logs.
8. In the current phase, do not install MCP servers, modify Smart98 configuration, create credentials, call Smart98/Wallex, add an adapter, or make production requests. If docs/runtime access is unavailable, document the exact missing evidence and leave compatibility `UNKNOWN`.
9. Any later adapter requires a separate feature specification, source/contract review, threat model, privacy/security/risk review, explicit permission approval, and current jurisdiction-specific legal/compliance gate before exchange access. Do not claim legality or suitability.
