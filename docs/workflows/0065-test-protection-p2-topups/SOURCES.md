# Sources — workflow 0065 (test-protection P2 top-ups)

1. `KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_..._2026-06-06.md` §5 — items
   P2-HYDRO-ANCHOR, P2-CANCEL-DETERMINISTIC, P2-REGISTRY-MICROGAPS,
   P2-REASON-ENUM, P2-MYPY-DECIDE. P2-CLI-NEGATIVES is explicitly NOT in
   this workflow (deferred until the bug-hunt NaN-validator family is
   green-lit; see plan §5 and §6).
2. `KAYAKGEN_TEST_COVERAGE_AUDIT_..._2026-06-06.md` rows R7 (self-referential
   hydrostatics goldens; no external anchor), R8 (racy cancel smoke can stay
   green without exercising cancel), R10 (registry micro-gaps: ANY-pass,
   hysteresis branch, touching range), §5 note (hand-enumerated reason set),
   §3 note (vestigial mypy).
3. Predecessor workflows 0062/0063/0064 (all landed 2026-06-06) — this run
   closes out the plan; the apply job's OPERATOR_REPORT carries the full
   plan-disposition table.

Hard boundary: TEST-ONLY (+ pyproject/CHANGELOG). kayakgen/ and scripts/ are
forbidden paths. A product bug exposed by a new test is a recorded successor
finding, not a fix in this run. The 0063 fixture-digest pin test must remain
byte-identical.
