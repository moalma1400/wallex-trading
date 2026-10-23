# Tasks — Feature 008

- [x] T001 Inspect existing Wallex docs and repository governance before changing runtime behavior.
- [ ] T002 Reconcile official order-create and order-detail references with the source register and discrepancy register.
- [x] T003 Define the fail-closed live activation policy schema without invented defaults.
- [x] T004 Implement a mediated execution interface; it has no direct HTTP path and does not handle API keys.
- [x] T005 Implement deterministic pre-trade eligibility and risk checks using Decimal arithmetic.
- [x] T006 Define order delegation without automatic retries; timeout/invalid acknowledgement is an unknown outcome requiring reconciliation.
- [ ] T007 Connect execution tools only after the actual Smart98/MCP contract and permission model are verified.
- [x] T008 Add offline fake-invoker tests for activation gates, disabled pairs, caps, mode-independent policy checks and uncertain order outcomes.
- [x] T009 Add execution-boundary documentation.
- [ ] T010 Run source and link validators, full offline test suite, compileall, and git diff check.
- [ ] T011 Open a draft PR against the authenticated-readonly feature branch; do not merge or enable live mode.

**Live activation gate:** remains closed until the exact challenge rules/window, dedicated account permissions, permitted Spot markets, risk caps, fees/precision, compliance eligibility, verified MCP tool contract, and explicit activation record are verified. This is a software implementation gate, not per-order human approval after activation.
