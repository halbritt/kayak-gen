# Sources — workflow 0064 (test-protection P1 contract decisions)

1. `docs/DECISION_LOG.md` rows **D048** and **D049** (operator decisions,
   2026-06-06) — the binding spec for this workflow:
   - D048: compare takes the REFUSAL branch. `build_comparison_report` must
     call `ensure_objectives_claim_admissible_for_search`; the auto-downgrade
     to `exploratory_frontier` without opt-in is a contract violation of the
     RELEASE_DISCIPLINE no-claim invariant. The labeled-exploratory behavior
     survives BEHIND `--explicit-exploratory`.
   - D049: `StabilityFitRecord` gains `kind` (`"analytical"` default) so
     CFD-in-loop graduation is reachable with real records.
2. `KAYAKGEN_TEST_COVERAGE_AUDIT_..._2026-06-06.md` rows **R2** (compare
   entry point counter-tested against the invariant) and **R1** (BUG-001
   mock-erasure: all graduation tests use SimpleNamespace fakes; the
   first_class branch is unreachable with production records).
3. `docs/bug-hunt/LEDGER.md` **BUG-026** (high) and **BUG-001** (critical) —
   close both with citations when the slices land.
4. RFC 0044 §Objective-claim gating; `kayakgen/search/pareto.py`
   `ensure_objectives_claim_admissible_for_search` (the gate itself is a
   FORBIDDEN path — call it, don't change it).
5. The 0063 fixture-digest pin (`tests/test_stability_fit_registry.py`) hashes
   the FIXTURE manifest, not the fit record — D049's field addition must not
   touch that file (forbidden path; if the pin breaks, the slice is wrong).

Out of scope: registry gate changes, new claim literals beyond `kind`,
P2 items (workflow D), any RFC 0058 successor taxonomy.
