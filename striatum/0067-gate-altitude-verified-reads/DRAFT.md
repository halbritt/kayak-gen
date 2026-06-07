# Draft - Workflow 0067: gate altitude + verified production reads

author: operator-self-declared-codex-local-0067-final
date: 2026-06-07
run: run_f9288a96b9ab737eb01cae5067a6f723
base: 6d405933cd8be29fdea80345c4eaed29088b07d2
branch: striatum/0067-gate-altitude-verified-reads

Implemented the two successor findings from workflow 0066: the skip-count
pin now has an in-suite enforcement point, and reachable production
artifact readers use stored/indexed hashes where provenance exists.

Branch commits:

- `ad4e8b2` - implementation + DRAFT (cherry-picked from detached
  worktree commit `818f777`)
- `7c8fbed` - workflow 0067 scaffold

Evidence below is from the implementation diff against `base`.

## Diffstat

```
 CHANGELOG.md                        |  14 ++++
 docs/DECISION_LOG.md                |   1 +
 docs/RELEASE_DISCIPLINE.md          |  15 ++--
 kayakgen/cli/runs_cli.py            |  31 ++++++++-
 kayakgen/eval/cfd/job_store.py      |  45 +++++++++---
 kayakgen/search/compare.py          |  72 +++++++++++++++++--
 kayakgen/services/artifact_store.py | 135 ++++++++++++++++++++++++++++++++----
 scripts/fast-gate.sh                |  45 ++++++++----
 scripts/full-gate.sh                |  43 ++++++++----
 tests/conftest.py                   |  74 ++++++++++++++++++++
 tests/test_artifact_store.py        | 107 ++++++++++++++++++++++++++--
 tests/test_cfd_jobs.py              |  27 ++++++++
 tests/test_cli.py                   |   6 +-
 tests/test_compare.py               |  50 ++++++++++++-
 tests/test_fast_gate_manifest.py    |  45 ++++++++++++
 15 files changed, 639 insertions(+), 71 deletions(-)
```

`striatum scope-check` over the workflow allowed/forbidden path set:
`clean: true`.

## Slice A - Skip Pin

- `tests/conftest.py` adds `pytest_sessionfinish` enforcement behind
  `KAYAKGEN_ENFORCE_SKIP_PIN=1`.
- Partial and collection-only pytest invocations are not punished. The
  hook returns early unless the explicit env knob is set, and also returns
  for `--collect-only`.
- Expected skips derive from env:
  default `4`; `0` only when both `KAYAKGEN_OPENFOAM_SMOKE=1` and
  `KAYAKGEN_OPENFOAM_LOCAL_RUN=1`; `KAYAKGEN_EXPECTED_SKIPS` remains an
  explicit non-negative override for scripts.
- `scripts/fast-gate.sh` and `scripts/full-gate.sh` export the env knob,
  guard `git rev-parse --show-toplevel`, parse only pytest's final summary
  line, and fail on non-numeric parse output.
- `docs/RELEASE_DISCIPLINE.md`, `docs/DECISION_LOG.md` row D051, and
  `CHANGELOG.md` record the explicit-env altitude decision.

## Slice B - Verified Reads

- `FilesystemArtifactStore` now exposes
  `ref_for_relative_path()` and `get_json_by_relative_path()` backed by a
  `SqliteIndex.artifact_ref_for_relative_path()` join from
  `artifacts.relative_path` to `runs.out_dir`.
- `kayakgen/search/compare.py` routes `run.json`, evaluation JSON, mesh
  diagnostics, and path-only high-angle artifacts through verified indexed
  reads when `_store` provenance exists. Hash-bearing high-angle GZ
  records construct an `ArtifactRef` directly and propagate
  `ArtifactIntegrityError`.
- `kayakgen/cli/runs_cli.py` uses verified indexed reads for `run.json`
  and candidate records during `kayakgen runs reindex` when provenance is
  present.
- `kayakgen/eval/cfd/job_store.py` verifies `run.json` through the store
  when the canonical record is current. Because local CFD `run.json` is
  mutable operational state, a valid out-of-band canonical edit that
  diverges from the indexed hard link is re-anchored with `put_json()` and
  then served from the newly stored hash. This preserves existing web/API
  local-job behavior while avoiding raw untracked serving.

Remaining direct-read surfaces, intentionally recorded:

- Indexless/legacy sweep directories still read canonical JSON directly
  because no expected hash exists.
- CFD `profile.json`, `job.json`, and mesh package manifests remain direct
  reads. They are local mutable setup records and were not promoted to
  immutable hash-ref records in this slice.
- Comparison high-angle display falls back to direct read only when the run
  has no store/index ref and no record-carried hash.

## Store Hardening

- Equal-length `_store/<hash>` occupants are rehashed before write-side
  dedupe; same-length bit rot is repaired.
- Read-side glob resolution sorts same-hash siblings, skips transient
  `read_bytes()` `OSError`, tries intact siblings before raising, and only
  raises after all same-hash siblings fail verification/repair.
- `relative_path` joins reject absolute paths and paths resolving outside
  `run_dir`.
- `ArtifactIntegrityError` is exported in `__all__`.

## Tests And Gates

Focused repairs:

```
.venv/bin/python -m pytest \
  tests/test_cli.py::test_compare_gated_objective_without_opt_in_refuses_at_cli \
  tests/test_cli.py::test_compare_gated_objective_with_opt_in_writes_exploratory_report \
  tests/test_fast_gate_manifest.py::test_every_deselect_nodeid_still_collects \
  tests/test_web.py::test_cfd_routes_prepare_status_run_and_raw_absence \
  tests/test_web.py::test_cfd_routes_failed_command_logs_and_artifact_bounds -q
5 passed in 6.41s

.venv/bin/python -m pytest \
  tests/test_web.py::test_cfd_routes_prepare_status_run_and_raw_absence \
  tests/test_web.py::test_cfd_routes_failed_command_logs_and_artifact_bounds \
  tests/test_cfd_jobs.py::test_load_run_record_reanchors_valid_out_of_band_record -q
3 passed in 3.69s

.venv/bin/python -m ruff check kayakgen tests
All checks passed!
```

Final gate:

```
KAYAKGEN_PY=/home/halbritt/git/kayak-gen/.venv/bin/python scripts/full-gate.sh

[kayakgen skip-pin] OK (4 skipped == expected 4)
1359 passed, 4 skipped, 7 warnings in 684.15s (0:11:24)
[full-gate] OK (4 skipped == expected 4)
```

The seven warnings are the expected store-repair / re-derive warnings from
tests that exercise those paths.

User-level index DB check after the final gate:

```
runs: 0
artifacts: 0
candidates: 0
metrics: 0
events: 0
```

## Operational Note

The Striatum supervised process lane could not attach on this host:
`striatum supervise start` exited before attach. Work was executed in the
claimed Striatum worktree with manual CLI status/claim/publish flow.
