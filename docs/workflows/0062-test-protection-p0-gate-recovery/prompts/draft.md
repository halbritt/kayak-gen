# Draft Prompt — P0 slice stack

Read the packet objective, your role file, the two context reports
(`KAYAKGEN_TEST_COVERAGE_AUDIT_..._2026-06-06.md` §4 rows R0/R3/R4 and
`KAYAKGEN_TEST_PROTECTION_REMEDIATION_PLAN_..._2026-06-06.md` §3), and
`SOURCES.md`. Then implement, in order, one commit per slice:

1. **P0-BOUNDARY-FIX.** `kayakgen/services/evaluation.py:33` imports
   `kayakgen.ui.hydrostatics_metadata`, failing
   `test_services_does_not_import_ui_or_cli[path2]` (red on `main` since
   2026-05-25). Create `kayakgen/metadata/` (package with `__init__.py`),
   move the registry module there (suggested name:
   `kayakgen/metadata/hydrostatics_rows.py`), reduce
   `kayakgen/ui/hydrostatics_metadata.py` to a re-export shim so every
   existing UI import keeps working, update `services/evaluation.py` to
   import from the new home, and update the `docs/ARCHITECTURE_MAP.md`
   package-layout row. Verify:
   `pytest tests/test_services_boundaries.py tests/test_import_boundaries.py
   tests/test_hydrostatics_row_metadata.py tests/test_hydro_tab_descriptions.py -q`
   all green.

2. **P0-INDEX-ISOLATION.** Add an autouse fixture to `tests/conftest.py`
   that monkeypatches `KAYAKGEN_INDEX_DB` to a per-test tmp path (cite audit
   R3 in the comment: sweep/search runner tests were writing the operator's
   real `~/.local/share/kayakgen/index.sqlite`; at audit time 129/129 rows
   were pytest phantoms). Add a regression test in
   `tests/test_artifact_store.py` pinning the isolation property (e.g. the
   env var is set and resolves inside pytest's tmp tree, so
   `_default_index_path()` never points at the user-level location during a
   test). Verify: run `pytest tests/test_sweep.py -q`, then confirm the
   user-level DB file's mtime did not change.

3. **P0-GATE-ENFORCE.** Add `scripts/fast-gate.sh`: `ruff check kayakgen
   tests` then the fast pytest subset — deselect the browser/visual suite
   (`tests/test_web_browser.py`), the subprocess-lifecycle tests
   (`tests/test_generative_jobs_subprocess.py`), and the CFD
   fixture-command integration tests (measure which files dominate runtime;
   record the final deselect list + measured runtime in the script header;
   budget ≤ ~3 minutes). Add `scripts/install-hooks.sh` that installs it as
   `.git/hooks/pre-push`. Update `docs/RELEASE_DISCIPLINE.md`: gate 1
   wording becomes "green, with only the documented OpenFOAM opt-in skips
   (expected: 4)"; document the hook install command; record that striatum
   workflow review/apply jobs run the FULL suite. Add a `CHANGELOG.md`
   entry for the three slices.

**Slice gate (after slice 3):** `.venv/bin/python -m pytest -q` → 0 failed,
4 skipped (documented OpenFOAM opt-ins only); `.venv/bin/python -m ruff
check kayakgen tests` → clean. Heartbeat before and after the full run.

Publish `striatum/0062-test-protection-p0-gate-recovery/DRAFT.md` with: per-
slice commit shas + diffstat, boundary-test pass evidence, the user-DB
mtime-unchanged evidence, the fast-gate deselect list + measured runtime,
and the full-gate output tail. Use the byline from your work packet.
