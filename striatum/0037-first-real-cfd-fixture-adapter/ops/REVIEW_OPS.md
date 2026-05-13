# REVIEW_OPS — workflow 0037 first real CFD fixture adapter

Verdict intent: accept_with_findings

## Scope

Independent Striatum review for workflow `0037-first-real-cfd-fixture-adapter`, role `reviewer_ops`.

Reviewed deterministic case generation, command execution, raw-output parsing, unavailable/failed/succeeded states, malformed and missing output behavior, external solver dependency, and CI/test coverage.

This review did not call `striatum`, did not publish artifacts, did not mutate project code, and did not update `OPERATOR_REPORT.md`.

## Sub-agent help used

Four read-only explorer sub-agents were used with disjoint scopes:

- Source obligations: RFC/workflow acceptance requirements and ops ambiguities.
- Job adapter mechanics: `kayakgen/eval/cfd/jobs.py` profiles, command execution, states, and output parsing.
- Test coverage: `tests/test_cfd_jobs.py` and CFD CLI tests.
- CLI/API surface: user-facing `cfd` commands and web raw-result handling.

All sub-agents were read-only and preserved the assigned reviewer_ops role. The main review also inspected the same sources directly and ran the targeted existing CFD tests.

## Verification

Targeted existing tests passed:

`.venv/bin/python -m pytest -q tests/test_cfd_jobs.py tests/test_cli.py::test_cfd_prepare_status_and_unavailable_run tests/test_cli.py::test_cfd_prepare_rejects_watertight_solver_for_current_package`

Result: `15 passed in 2.83s`.

This verifies the already-landed RFC 0015 dispatch behavior, not the RFC 0026 fixture-local-command success path.

## Findings

### OPS-001 — RFC 0026 fixture profile and adapter are not implemented yet

Severity: high

`CfdAdapterName` only permits `unavailable` and `mock_local_command` in [jobs.py](/home/halbritt/git/kayak-gen/kayakgen/eval/cfd/jobs.py:25). The built-in profile registry contains only `unavailable-open-wetted-surface`, `unavailable-watertight-solid`, and `mock-failing-local-command` in [jobs.py](/home/halbritt/git/kayak-gen/kayakgen/eval/cfd/jobs.py:643). There is no `fixture-local-command` profile or `fixture_local_command` adapter.

Required action: add the RFC 0026 built-in fixture profile, register it in `solver_profile_names()`, and route it through `_adapter_for()`.

### OPS-002 — Prepare writes job records but no deterministic fixture case files

Severity: high

`prepare_local_job()` currently writes `profile.json`, `job.json`, and `run.json` in [jobs.py](/home/halbritt/git/kayak-gen/kayakgen/eval/cfd/jobs.py:302). The only local-command adapter prepare path creates `logs/` only in [jobs.py](/home/halbritt/git/kayak-gen/kayakgen/eval/cfd/jobs.py:378).

RFC 0026 requires deterministic adapter case files in addition to the existing profile/job/run records.

Required action: fixture prepare should render stable case inputs from job spec and mesh manifest metadata, with tests comparing deterministic outputs.

### OPS-003 — Successful fixture execution and normalized raw parsing are absent

Severity: high

The only command-backed built-in profile is intentionally failing. The clean-exit branch in `MockFailingLocalCommandAdapter` synthesizes `raw-result.json` from return code/stdout/stderr in [jobs.py](/home/halbritt/git/kayak-gen/kayakgen/eval/cfd/jobs.py:407); it does not require command-produced raw output, parse fixture schema, or normalize fields such as drag force and residuals.

Required action: add a fixture raw-result model/parser and allow `succeeded` only after clean command exit plus present, schema-valid raw output.

### OPS-004 — Missing command, missing output, and malformed output are not adapter-level failure states

Severity: high

`subprocess.run()` is not wrapped for missing executable or permission errors in [jobs.py](/home/halbritt/git/kayak-gen/kayakgen/eval/cfd/jobs.py:383). `run_local_job()` writes `running` before adapter execution in [jobs.py](/home/halbritt/git/kayak-gen/kayakgen/eval/cfd/jobs.py:321), so an unhandled execution error could leave a stale running record.

Missing output and malformed output are not checked by the adapter at all.

Required action: map missing command to `unavailable` or `failed` with stable `error_kind`; map nonzero command, missing output, and malformed output to `failed` with persisted `error_kind` and `error_message`.

### OPS-005 — CI coverage is RFC 0015-level, not RFC 0026-level

Severity: high

Existing tests cover round-trip raw claims, deterministic generic prepare, readiness rejection, unavailable solver, mock command failure, and CLI unavailable wording in [tests/test_cfd_jobs.py](/home/halbritt/git/kayak-gen/tests/test_cfd_jobs.py:39) and [tests/test_cli.py](/home/halbritt/git/kayak-gen/tests/test_cli.py:176).

Missing tests:

- `fixture-local-command` appears in profile listing.
- Fixture prepare writes deterministic case files.
- Fixture run succeeds with schema-valid raw output.
- Missing command produces a persisted unavailable/failed record.
- Clean command with missing raw output fails.
- Malformed raw output fails at adapter/run layer.
- CLI status/run wording covers fixture success and raw-unvalidated warning.

### OPS-006 — Web raw-result handling is useful but not a fixture adapter acceptance substitute

Severity: medium

The web layer has generic raw-result artifact handling and malformed JSON tests, but those tests manually mutate artifacts rather than exercising a real fixture adapter through prepare/run. This is helpful supporting coverage, not proof that RFC 0026 behavior exists end to end.

Required action: keep web raw-result tests, but add adapter-level tests first.

## Ops ambiguities to resolve before implementation

RFC 0026 leaves two choices open that affect tests:

- Whether the fixture command is a checked-in `python -m` module or a generated per-job script.
- Whether normalized output is `raw-result.json` or an `outputs/` manifest.

Either choice is workable, but tests need a stable contract. Missing-command classification and warning-string stability should also be pinned or tested by semantic substrings rather than brittle full text.

## Positive observations

The existing RFC 0015 base is suitable for the fixture slice. Mesh readiness/profile gating is already centralized, job IDs are deterministic from stable inputs, run records persist raw claim state, and the existing tests confirm raw CFD cannot be promoted to calibrated or validated claims.

No OpenFOAM, SU2, hosted solver, Docker, or external CFD dependency is present in the scoped implementation or tests.

## Required actions for the next workflow step

1. Add and document `fixture-local-command`.
2. Implement deterministic fixture case generation.
3. Implement command execution with captured stdout/stderr and persisted logs.
4. Implement schema-validated raw-result parsing.
5. Persist clear failure records for missing command, nonzero command, missing output, and malformed output.
6. Add CI tests for prepare, success, unavailable/missing command, command failure, missing output, malformed output, and run-record round trip.
7. Keep every result `raw_unvalidated` with warning copy that fixture output is not calibrated, validated, or final design fitness.

## Verdict rationale

The workflow can proceed with recorded findings. The current code correctly represents the earlier local-dispatch slice, but the RFC 0026 fixture adapter remains implementation work. These are substantial ops/test requirements, yet they are bounded and do not require rejecting or re-scoping the workflow.