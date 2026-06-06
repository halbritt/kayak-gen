# Draft Prompt — D048 + D049

Read the packet objective, your role file, DECISION_LOG rows D048/D049,
audit rows R2/R1, SOURCES.md, and the current tests/test_compare.py +
tests/test_cfd_in_loop_evaluator_status.py. Implement, one commit per
decision:

1. **D048** — wire ensure_objectives_claim_admissible_for_search into
   build_comparison_report with an explicit_exploratory parameter; expose
   --explicit-exploratory on the compare CLI; add the refusal-token test;
   migrate the downgrade-pinning tests to the opt-in path with all
   assertions intact; USER_GUIDE + LEDGER (BUG-026) updates.
2. **D049** — add kind to StabilityFitRecord (default "analytical");
   rewrite the graduation tests around real records from the conftest
   factory (add a kind passthrough kwarg to the fit factory if needed);
   LEDGER (BUG-001) + schema-checklist doc updates; CHANGELOG for both.

**Slice gate:** .venv/bin/python -m pytest -q → 0 failed, 4 documented
skips; ruff clean. Heartbeat before/after.

Publish striatum/0064-test-protection-p1-contract-decisions/DRAFT.md with
slice shas + diffstat, refusal-token evidence, real-record graduation
evidence, and the full-gate tail. Use the packet's byline.
