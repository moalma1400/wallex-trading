# Tasks — Feature 008

- [ ] T001 Reconcile official order-create and order-detail references with the source register.
- [ ] T002 Add the Feature 008 source/discrepancy records and retain unknown permission/competition facts as unresolved.
- [ ] T003 Define the fail-closed live activation policy schema without invented defaults.
- [ ] T004 Implement a separate fixed-contract Spot execution client.
- [ ] T005 Implement deterministic pre-trade eligibility and risk checks using Decimal arithmetic.
- [ ] T006 Implement order submission without automatic POST retries and safe order-detail reconciliation by client ID.
- [ ] T007 Expose execution tools only behind the activation gate; keep Feature 007 public/read-only behavior unchanged.
- [ ] T008 Add offline fake-transport tests for valid/invalid order intents, disabled pairs, caps, secret redaction, mode isolation, and uncertain POST outcomes.
- [ ] T009 Add audit events and operator documentation.
- [ ] T010 Run source and link validators, full offline test suite, compileall, and git diff check.
- [ ] T011 Open a draft PR against the authenticated-readonly feature branch; do not merge or enable live mode.

**Live activation gate:** remains closed until the exact challenge rules/window, dedicated account permissions, permitted Spot markets, risk caps, fees/precision, compliance eligibility, and explicit activation record are verified. This is a software implementation gate, not per-order human approval after activation.
