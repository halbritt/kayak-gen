author: reviewer-codex-001
date: 2026-06-06
run: run_00abc6ed7fb8b35ed5860d7d4286643a
job: job_run_00abc6ed7fb8b35ed5860d7d4286643a_review

# Review — Workflow 0062 P0 Gate Recovery

## Verdict

accept

## Findings

No findings.

The three P0 slices satisfy the remediation plan and packet checks:

- Scope: branch diff touches the expected implementation/docs/scripts
  paths. `tests/test_services_boundaries.py`,
  `tests/test_import_boundaries.py`, and
  `tests/test_hydrostatics_row_metadata.py` are untouched.
- P0-BOUNDARY-FIX: `kayakgen.services.evaluation` now imports
  `kayakgen.metadata.hydrostatics_rows`, and
  `kayakgen.ui.hydrostatics_metadata` is a compatibility shim.
- P0-INDEX-ISOLATION: conftest has a two-layer `KAYAKGEN_INDEX_DB`
  isolation fixture, with a regression test pinning default `SqliteIndex()`
  resolution inside pytest's tmp tree.
- P0-GATE-ENFORCE: `scripts/fast-gate.sh` runs ruff plus the documented fast
  subset, and `scripts/install-hooks.sh` writes `.git/hooks/pre-push` to
  exec `scripts/fast-gate.sh` (verified by code inspection, `bash -n`, and
  executable file modes without mutating `.git/hooks` in this review-only
  packet).
  `docs/RELEASE_DISCIPLINE.md` now requires the full suite to be green with
  exactly the four documented OpenFOAM opt-in skips.

## Evidence

Targeted check before the long run:

```text
.venv/bin/python -m pytest tests/test_services_boundaries.py \
  tests/test_import_boundaries.py tests/test_hydrostatics_row_metadata.py \
  tests/test_hydro_tab_descriptions.py \
  tests/test_artifact_store.py::test_index_db_isolated_from_user_level_path -q
115 passed in 2.55s
```

Full suite:

```text
.venv/bin/python -m pytest -q
1309 passed, 4 skipped in 517.96s (0:08:37)
```

The four skips were exactly the documented OpenFOAM opt-ins:

```text
tests/test_cfd_run_stages.py:212
tests/test_cfd_run_stages.py:255
tests/test_openfoam_v2512_smoke.py:109
tests/test_openfoam_v2512_smoke.py:213
```

Ruff:

```text
.venv/bin/python -m ruff check kayakgen tests
All checks passed!
```

Fast gate:

```text
time -p scripts/fast-gate.sh
1052 passed, 4 skipped, 2 deselected in 180.41s (0:03:00)
[fast-gate] OK
real 181.63
```

User-level index DB was unchanged before vs. after the full suite and fast
gate:

```text
~/.local/share/kayakgen/index.sqlite
mtime_ns=1780730948840040717
size=90112
runs=0
candidates=0
metrics=0
artifacts=0
events=0
generative_jobs=0
```

Additional checks:

```text
git diff --name-only main...HEAD -- tests/test_services_boundaries.py \
  tests/test_import_boundaries.py tests/test_hydrostatics_row_metadata.py
# no output

git diff --check main...HEAD
# no output

bash -n scripts/fast-gate.sh
bash -n scripts/install-hooks.sh
# both passed

git ls-files --stage scripts/fast-gate.sh scripts/install-hooks.sh
100755 ... scripts/fast-gate.sh
100755 ... scripts/install-hooks.sh
```
