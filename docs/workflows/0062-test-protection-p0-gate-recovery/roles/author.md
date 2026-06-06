# Role: Author (Test-protection P0 — gate recovery)

Implement the three P0 items from
`KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_CLAUDE_OPUS_4_8_2026-06-06.md`
(P0-BOUNDARY-FIX → P0-INDEX-ISOLATION → P0-GATE-ENFORCE), strictly in that
order, one commit per slice, strictly inside the declared write scope.

Hard constraints:

- `tests/test_services_boundaries.py`, `tests/test_import_boundaries.py`, and
  `tests/test_hydrostatics_row_metadata.py` are forbidden paths. The boundary
  test goes green by fixing the import direction (relocate the registry to the
  new `kayakgen/metadata/` package; keep a `kayakgen.ui.hydrostatics_metadata`
  re-export shim); the row-metadata tests must pass byte-stable through the
  shim, untouched.
- The conftest autouse fixture must make it impossible for any test to write
  the user-level `~/.local/share/kayakgen/index.sqlite` (audit finding R3:
  before remediation, 100% of that DB's rows were pytest tmp-path phantoms).
- The fast gate (`scripts/fast-gate.sh`) is a pre-push convenience, not the
  release gate; the FULL suite is the slice-completion gate. Measure the fast
  subset's runtime and record it plus the deselect list in the script header
  and `docs/RELEASE_DISCIPLINE.md`.
- Final gate: `.venv/bin/python -m pytest -q` → 0 failed, exactly the 4
  documented OpenFOAM opt-in skips; `.venv/bin/python -m ruff check kayakgen
  tests` clean.
- The full suite takes ~9 minutes: heartbeat before and after long commands;
  do not let the lease expire mid-run.
- Commit messages follow repo convention with the co-author line from
  `docs/RELEASE_DISCIPLINE.md`; use the byline supplied in your work packet
  for published artifacts.
