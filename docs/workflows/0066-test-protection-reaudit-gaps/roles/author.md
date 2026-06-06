# Role: Author (Re-audit gap remediation — G1-G6, G8-G10)

Close the nine standing gaps from the 2026-06-06 post-remediation re-audit,
one commit per item, in three slices (gate / store / tests), strictly inside
the declared write scope.

Hard constraints:

- The audit ledger (KAYAKGEN_TEST_COVERAGE_AUDIT_WHOLE_REPO_...md §4) is the
  work order: every row names the mechanism and the smallest closing test.
  Do not re-derive it; do not edit the audit files — they are evidence.
- G7 (CLI NaN negatives) is DEFERRED by documented decision (workflow 0065
  SUMMARY); do not touch it. G11 stays deferred.
- This wave exists because the last wave claimed a gate property it never
  implemented. Nothing you land may claim more than its mechanism enforces:
  the skip pin must demonstrably fail on a wrong count; the read path must
  demonstrably refuse unverified bytes.
- Slice C is test-only: kayakgen/eval/ and kayakgen/cli/ are forbidden. A
  product bug exposed by a new test is a recorded successor finding in the
  draft artifact, not a fix in this run.
- The G2 read contract is decided: SERVE-ONLY-VERIFIED, repair only from a
  canonical path whose bytes rehash to the expected hash, structured raise
  otherwise. Record it as a DECISION_LOG row.
- The G5 decision is made: pin the fail-closed R2-default quirk as intended;
  record the per-metric-default question as an open item, change nothing in
  campaigns.py.
- Final gate: scripts/full-gate.sh (your own new script) → 0 failed, exactly
  the 4 documented OpenFOAM skips; ruff clean. Heartbeat around the
  ~9-minute run. User-level index.sqlite byte-identical before/after.
