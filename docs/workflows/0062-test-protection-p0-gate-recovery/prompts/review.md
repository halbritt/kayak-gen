# Review Prompt — P0 slice stack

Read the draft artifact, the run branch diff, your role file, and the two
context reports (audit rows R0/R3/R4; plan items P0-*). Review for:

- **Gate integrity first:** confirm via `git diff main...HEAD --stat` that
  `tests/test_services_boundaries.py`, `tests/test_import_boundaries.py`,
  and `tests/test_hydrostatics_row_metadata.py` are untouched. Any edit
  there is `needs_revision`, full stop.
- **Slice 1:** registry relocated to `kayakgen/metadata/`, shim in place,
  `services/evaluation.py` no longer imports `kayakgen.ui`, ARCHITECTURE_MAP
  updated, row-metadata byte-stability tests green unchanged.
- **Slice 2:** conftest fixture is autouse and per-test; the regression test
  pins the property (deleting the fixture would fail it); no test writes the
  user-level index DB (check the draft's mtime evidence; re-verify with a
  targeted run if cheap).
- **Slice 3:** fast-gate.sh runs within its stated budget (run it); the
  pre-push installer works; RELEASE_DISCIPLINE no longer says "green or
  skipped" and pins expected skips = 4; CHANGELOG entry present.
- **Full gate:** run `.venv/bin/python -m pytest -q` and
  `.venv/bin/python -m ruff check kayakgen tests` yourself. Required: 0
  failed, exactly 4 documented OpenFOAM skips, ruff clean. Write your
  findings file BEFORE the ~9-minute run and heartbeat around it.

Publish `striatum/0062-test-protection-p0-gate-recovery/review/REVIEW.md`
with file-path-grounded findings and your verdict. `accept` /
`accept_with_findings` when the apply job can fix it; `needs_revision` for
scope violations or a red gate; never a terminal `reject`.
