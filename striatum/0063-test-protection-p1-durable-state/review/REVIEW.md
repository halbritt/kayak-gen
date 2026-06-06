# Review - Workflow 0063 Durable-State Hardening

author: reviewer-codex-001
date: 2026-06-06
run: run_2198d739c43270edeb3ee93f93160b97
session: sess_0026ec1191c6bd2ea14ae105ebccb698
job: job_run_2198d739c43270edeb3ee93f93160b97_review

## Verdict

accept

## Findings

No defects found in the reviewed scope.

## Review Notes

- `FilesystemArtifactStore._put_bytes` now writes new content-addressed bytes
  through a same-directory temp sibling plus `os.replace`
  (`kayakgen/services/artifact_store.py:602`, `:612-617`, `:747-753`).
  The temp file is dot-prefixed, so it does not match the
  `_store/<hash>.*` read glob while a write is in flight.
- The existing-file dedupe branch now verifies size and rehashes on size
  mismatch before repairing corrupt bytes (`artifact_store.py:702-736`).
  The new corruption test stages truncated bytes at the exact hash path and
  confirms the repaired store file and canonical path both contain intact
  bytes (`tests/test_artifact_store.py:212-246`).
- Same-length corruption is not caught by this implementation because the
  cheap size screen returns before rehashing (`artifact_store.py:717-722`).
  That is explicitly documented as out of scope in the draft artifact
  (`striatum/0063-test-protection-p1-durable-state/DRAFT.md:167-169`) and
  matches the remediation plan's length-first acceptance.
- JSON helpers now use explicit utf-8 and atomic temp-plus-replace writes
  while preserving the exact `model_dump_json(indent=2)` payload bytes
  (`kayakgen/io/json.py:12-40`). The added non-ASCII round-trip test asserts
  byte identity with the pydantic dump (`tests/test_hull_roundtrip.py`).
- `SqliteIndex` rebuilds only when `PRAGMA user_version` is lower than
  `SCHEMA_VERSION`; current and future stamps run idempotent `CREATE TABLE IF
  NOT EXISTS` only, without dropping rows (`artifact_store.py:183-218`). The
  stale-version and current-version tests cover both branches
  (`tests/test_artifact_store.py:275-338`).
- The SHA pin is test-only. `git diff main..HEAD --
  kayakgen/eval/stability/registry.py` is empty, and the new test comment
  explains the evaluator-version-event response rather than treating a digest
  change as a routine snapshot update (`tests/test_stability_fit_registry.py:428-448`).

## Evidence Before Full Gate

- Working tree was clean before review artifact creation.
- Branch diff from `main`: `CHANGELOG.md`, `kayakgen/io/json.py`,
  `kayakgen/services/artifact_store.py`, `tests/test_artifact_store.py`,
  `tests/test_hull_roundtrip.py`, `tests/test_stability_fit_registry.py`,
  and `striatum/0063-test-protection-p1-durable-state/DRAFT.md`.
- `kayakgen/eval/stability/registry.py` has no branch diff.
- Targeted check passed:
  `.venv/bin/python -m pytest -q tests/test_artifact_store.py::test_corrupt_store_file_repaired_on_next_put tests/test_artifact_store.py::test_stale_schema_version_db_rebuilt_not_crashed tests/test_artifact_store.py::test_current_schema_version_db_preserved_on_reopen tests/test_hull_roundtrip.py tests/test_stability_fit_registry.py::test_fixture_canonical_sha256_pinned_to_literal_digest`
  -> `15 passed in 0.89s`.

## Full Gate

- `.venv/bin/python -m pytest -q` passed: `1315 passed, 4 skipped,
  1 warning in 515.45s (0:08:35)`.
- The 4 skips are exactly the documented OpenFOAM opt-in skips:
  two in `tests/test_cfd_run_stages.py` and two in
  `tests/test_openfoam_v2512_smoke.py`.
- The single warning is the expected repair-path warning in
  `tests/test_cfd_jobs.py::test_openfoam_rerun_ignores_stale_force_dat_and_raw_result`.
- `.venv/bin/python -m ruff check kayakgen tests` passed:
  `All checks passed!`.
