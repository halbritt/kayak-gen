# Patch Summary - workflow 0037 first real CFD fixture adapter

## Status

Implemented the ledger-approved RFC 0026 fixture-local-command slice. The new
adapter remains local, deterministic, and raw/unvalidated. It does not add
OpenFOAM, SU2, hosted execution, Docker/container dispatch, validation,
calibration, watertight `cfd_ready` bypasses, or final design-fitness claims.

## Findings Addressed

- L-F1: Added and registered the built-in `fixture-local-command` profile with
  adapter name `fixture_local_command`, `cfd_surface_candidate` readiness, and
  `open_wetted_surface_resistance_v1` mesh profile gating.
- L-F2: Fixture prepare now writes deterministic adapter case files under
  `case/`, including fixture input, mesh summary, and command metadata.
- L-F3: Added a checked-in `python -m kayakgen.eval.cfd.fixture_command`
  command and a schema-validated fixture raw-output parser that normalizes
  successful output into `raw-result.json`.
- L-F4: Persisted stable unavailable/failed records for missing command,
  nonzero command, missing output, malformed output, and job-id mismatch.
- L-F5: Added RFC 0026 job and CLI coverage for profile listing, deterministic
  prepare, success, failure modes, run-record round trip, and warning visibility.
- L-F6: Fixture success and failure records remain `raw_unvalidated` and carry
  the fixture warning that output is not calibrated, validated, or final design
  fitness.
- L-F7: Pinned the fixture command shape to a checked-in `python -m` module and
  the normalized output location to job-root `raw-result.json`.
- L-F8: Added an RFC 0017 revision note and updated the RFC index/status text.

## Changed Files

- `CHANGELOG.md`
- `docs/rfcs/0017-first-real-cfd-adapter.md`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md`
- `docs/rfcs/README.md`
- `kayakgen/cli/main.py`
- `kayakgen/eval/cfd/__init__.py`
- `kayakgen/eval/cfd/fixture_command.py`
- `kayakgen/eval/cfd/jobs.py`
- `tests/test_cfd_jobs.py`
- `tests/test_cli.py`
- `striatum/0037-first-real-cfd-fixture-adapter/implementation/PATCH_SUMMARY.md`

## Verification

- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q tests/test_cfd_jobs.py`
  - Result: `20 passed in 3.06s`
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q tests/test_cli.py::test_cfd_profiles_lists_fixture_local_command tests/test_cli.py::test_cfd_fixture_run_and_status_keep_raw_warning_visible tests/test_cli.py::test_cfd_prepare_status_and_unavailable_run tests/test_cli.py::test_cfd_prepare_rejects_watertight_solver_for_current_package`
  - Result: `4 passed in 1.88s`
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q tests/test_cfd_jobs.py tests/test_cli.py`
  - Result: `36 passed in 8.63s`
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q`
  - Result: `201 passed in 28.49s`
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m compileall -q kayakgen/eval/cfd kayakgen/cli/main.py`
  - Result: passed
- `git diff --check`
  - Result: passed
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m ruff check kayakgen/eval/cfd kayakgen/cli/main.py tests/test_cfd_jobs.py tests/test_cli.py`
  - Result: not run successfully because the referenced venv does not have
    `ruff` installed (`No module named ruff`).

## Deferred Findings

No ledger-approved safe-now finding was intentionally deferred. The broader
out-of-scope items remain deferred: OpenFOAM/SU2 or other real solver
selection, solver installation requirements, hosted/container execution,
validation against measured kayak data, calibration, analytical resistance
promotion, watertight solid dispatch, volume meshing, closed-volume `cfd_ready`
promotion, and final design-fitness scoring.

## Sub-Agent Usage

- Read-only workflow explorer: summarized the workflow sources, reviews,
  findings ledger, acceptance criteria, prohibited work, and artifact
  requirements.
- Read-only code explorer: mapped `kayakgen/eval/cfd/`, CLI, and test change
  points and called out adapter/run-record risks.
- Test worker: edited only `tests/test_cfd_jobs.py` and `tests/test_cli.py` to
  express the RFC 0026 fixture profile, prepare, success, failure, round-trip,
  and CLI warning expectations.
- Documentation worker: edited only RFC/changelog files to pin the fixture
  command/output/profile choices and keep RFC 0017 real-solver selection
  deferred.
