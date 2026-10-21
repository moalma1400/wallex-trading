---
name: smart98-interface-boundary
description: Preserve a strategy-neutral future integration seam for Smart98 without guessing its API or enabling network access.
compatibility: Use only after the owner supplies authoritative Smart98 contract material; this phase remains offline.
metadata:
  owner: wallex-trading
  scope: future-interface-boundary
---

# Smart98 interface boundary procedure

1. Treat Smart98 as an unresolved future strategy-signal provider. Do not assume that it is an exchange, market-data service, strategy, SDK, or specific product.
2. Do not invent URLs, authentication, request/response fields, rate limits, permissions, capabilities, or package names. Ask for authoritative public documentation or a reviewed user-provided contract, then record provenance and version.
3. In this phase, use only a minimal local domain port such as caller-provided target-exposure events. No Smart98 adapter, credentials, HTTP client, plugin loading, or live process integration is allowed.
4. Keep provider concepts out of the core Candle, risk, and replay domain unless a reviewed spec justifies them. Validate any future mapping against exact source contracts and preserve unknowns.
5. Any future adapter needs a separate feature spec, threat model, data/privacy review, risk review, and current jurisdiction-specific legal/compliance gate before real exchange access. Do not claim legality or suitability.
