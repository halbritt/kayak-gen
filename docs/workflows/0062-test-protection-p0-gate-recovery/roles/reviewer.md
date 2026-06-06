# Role: Reviewer (Test-protection P0 — gate recovery)

Review the P0 slice stack against the remediation plan items
P0-BOUNDARY-FIX, P0-INDEX-ISOLATION, and P0-GATE-ENFORCE, and against the
audit findings R0/R3/R4 they close.

Non-negotiable checks:

- `git diff` for the run branch touches NO forbidden path: the boundary tests
  and `tests/test_hydrostatics_row_metadata.py` must be untouched. A green
  boundary test achieved by editing the test is an automatic `needs_revision`.
- The registry relocation preserves the hydro-rows wire payload byte-for-byte
  (the untouched row-metadata tests passing is the evidence).
- The conftest isolation fixture is autouse and pins the property for every
  test, not just the artifact-store file; the regression test would fail if
  the fixture were deleted.
- `scripts/fast-gate.sh` actually runs inside its stated budget; the
  RELEASE_DISCIPLINE edit removes the "green or skipped" loophole and pins
  expected skips = 4 (OpenFOAM opt-in).
- Run the FULL gate yourself: `.venv/bin/python -m pytest -q` (0 failed, 4
  documented skips) and ruff clean. Heartbeat before/after the ~9-minute run;
  write your findings file BEFORE starting the long run and update it after,
  so the verdict can publish even if the lease gets tight.

Verdict semantics: `accept` / `accept_with_findings` for anything the apply
job can fix; `needs_revision` for scope violations or a red gate. Do NOT use
a terminal `reject` (operator hazard: it wedges the run). Findings cite file
paths and, where relevant, plan item ids.
