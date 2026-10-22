# Research and Source Decisions

**Feature**: [001-wallex-official-documentation-inventory](spec.md)
**Snapshot**: 2026-10-21 UTC
**Research log**: [docs/research/research-log.md](../../docs/research/research-log.md)

## Sources examined

- Official Wallex website: `https://wallex.ir/` and fee page `https://wallex.ir/commission`.
- Current-looking official developer docs: `https://developers.wallex.ir/docs`, 115 `/docs` destinations from `https://developers.wallex.ir/sitemap.xml`.
- Official legacy API reference: `https://api-docs.wallex.ir/`, a single page with sections for prerequisites, markets, account, orders/trades, OTC, WebSocket, and Wallgate.
- Official U.S. Treasury press release and OFAC FAQ as external, clearly separated legal/compliance context.

Directly reviewed modern topic pages: overview, API key, markets, fee, depth, candles, Spot intro/markets/orders/create/cancel/detail/types, OTC intro/markets/price/create, Margin intro/open, trading-credit intro/types, WebSocket intro/connection/migration/private token, latest public trades. The exact reviewed source IDs and URLs are in the source register. Remaining sitemap pages are not represented as reviewed.

## Findings relevant to design

- Modern docs and legacy reference differ in route and parameter style. Keep source-specific descriptions and capture differences in the discrepancy register.
- Current fee display is incomplete: the official commission page's maker/taker table was blank in the retrieved rendering; the API endpoint documents fields but not fixed current values. Record no invented rate.
- The official Wallex help-center fee URL returned a localized 404 page. The homepage-linked API documentation route failed in the reader without an HTTP status; neither is marked reviewed.
- Several API pages describe account-changing functions (orders, margin positions, transfers/withdrawals); the research work only reads the docs, never calls those endpoints.
- The new WebSocket documentation says most channels do not supply a snapshot/history and messages during disconnect are lost. Channel-specific review remains incomplete.
- Official U.S. Treasury and OFAC pages raise material sanctions/compliance risk; legal jurisdiction and user-specific applicability remain unresolved.

## Clarification decision

No user clarification was needed to specify this feature: the scope is explicitly documentation-only, and no strategy, asset list, timeframe, risk tolerance, or execution architecture is to be invented. User-specific future decisions remain in `docs/research/unresolved-questions.md`. A formal Spec Kit `/speckit-clarify` command was not invoked; no native Arena integration is verified, and the generated Generic integration documents its command files as instructions for a compatible agent. The relevant procedures were applied through this environment's ordinary file and shell operations.

## Process deviation note

A limited direct source discovery/inspection pass was performed immediately after the spec commit to ground scope and identify the 115-page sitemap inventory; the full knowledge-base artifacts were begun before the plan/task documents were finalized. This departs from the ideal Specify → Plan → Tasks → Analyze → Implement sequence. This plan and task list now retrospectively trace and bound that initial research, but it is not represented as a successful invocation of Spec Kit slash commands. Future feature work must follow the documented sequence before implementation.
