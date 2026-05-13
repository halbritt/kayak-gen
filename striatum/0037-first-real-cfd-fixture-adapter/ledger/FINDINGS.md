# Findings Ledger - workflow 0037 first real CFD fixture adapter

Verdict intent: accept_with_findings

## Scope Boundary

This ledger consolidates the three review artifacts already present for
workflow `0037-first-real-cfd-fixture-adapter`:

- `striatum/0037-first-real-cfd-fixture-adapter/domain_source/REVIEW_DOMAIN_SOURCE.md`
- `striatum/0037-first-real-cfd-fixture-adapter/ops/REVIEW_OPS.md`
- `striatum/0037-first-real-cfd-fixture-adapter/traceability/REVIEW_TRACEABILITY.md`

Safe-now work is limited to the deterministic local fixture adapter described
by RFC 0026. The safe slice may extend the existing RFC 0015 local dispatch
surface with a `fixture-local-command` profile, deterministic case files,
local command execution, schema-validated raw output parsing, persisted run
records, CLI visibility, and CI tests.

The safe slice must not include OpenFOAM, SU2, hosted or remote execution,
Docker/container dispatch, real solver validation, calibration, analytical
resistance promotion, watertight `cfd_ready` bypasses, or final design-fitness
claims.

## Sub-Agent / Parallel Worker Usage

Four read-only explorer sub-agents were used with disjoint extraction scopes:

- One reviewed the domain-source artifact and claim semantics.
- One reviewed the ops artifact and operational/test gaps.
- One reviewed the traceability artifact and RFC acceptance map.
- One reviewed all three artifacts for deduplication, conflicts, missing
  evidence, and proposed ledger structure.

All sub-agents were read-only. They did not edit files, call `striatum`,
publish artifacts, push branches, or update operator reports. The ledger was
then written directly from those summaries plus a direct read of the workflow
sources.

## Consolidated Findings

### L-F1 - Fixture profile and adapter are absent

Severity: high

RFC 0026 names `fixture-local-command` with adapter
`fixture_local_command`, `required_mesh_readiness="cfd_surface_candidate"`,
`required_mesh_profile="open_wetted_surface_resistance_v1"`, and
`result_semantics="raw_unvalidated"`.

Current code only admits `unavailable` and `mock_local_command` as adapter
names, and the built-in profile registry only includes
`unavailable-open-wetted-surface`, `unavailable-watertight-solid`, and
`mock-failing-local-command`.

Required safe-now action: add the fixture adapter name, add and register the
fixture profile, expose it through `solver_profile_names()` / `cfd profiles`,
and route it through the existing adapter factory.

Evidence:

- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:39`
- `kayakgen/eval/cfd/jobs.py:25`
- `kayakgen/eval/cfd/jobs.py:635`
- `kayakgen/eval/cfd/jobs.py:643`

### L-F2 - Prepare does not write deterministic fixture case files

Severity: high

`prepare_local_job()` currently writes `profile.json`, `job.json`, and
`run.json`. The only local-command adapter prepare path creates `logs/`.
RFC 0026 requires deterministic adapter case files for the fixture profile in
addition to the generic job records.

Required safe-now action: render stable fixture case inputs from the job spec
and mesh manifest metadata, then cover them with deterministic-output tests.

Evidence:

- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:79`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:105`
- `kayakgen/eval/cfd/jobs.py:302`
- `kayakgen/eval/cfd/jobs.py:378`

### L-F3 - Successful fixture execution and normalized raw parsing are absent

Severity: high

The existing command-backed profile is intentionally failing. The clean-exit
branch in `MockFailingLocalCommandAdapter` writes a synthetic
`raw-result.json` from return code/stdout/stderr; it does not require a
command-produced raw output file, parse a fixture schema, or normalize fields
such as drag force, residuals, fixture version, command provenance, return
code, claim state, and warnings.

Required safe-now action: add a fixture raw-result model/parser and allow
`succeeded` only when the command exits cleanly and required raw output is
present and schema-valid.

Evidence:

- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:49`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:82`
- `kayakgen/eval/cfd/jobs.py:375`
- `kayakgen/eval/cfd/jobs.py:407`

### L-F4 - Fixture failure modes are not persisted reliably

Severity: high

RFC 0026 requires missing command, nonzero command, missing output, and
malformed output to produce `unavailable` or `failed` records with
`error_kind` and `error_message`. Current mock command code records nonzero
return codes, but missing executable or permission failures can escape
`subprocess.run()`. Because `run_local_job()` writes `running` before adapter
execution, an unhandled execution error can leave a stale running record.
Missing output and malformed output are not checked by an adapter path today.

Required safe-now action: map missing executable/permission errors,
nonzero exits, missing output, and malformed output to stable persisted run
records. The reviewed artifacts recommend at least the existing
`solver_unavailable` and `command_failed` strings plus documented strings for
missing and malformed output.

Evidence:

- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:84`
- `kayakgen/eval/cfd/jobs.py:321`
- `kayakgen/eval/cfd/jobs.py:383`
- `kayakgen/eval/cfd/jobs.py:399`

### L-F5 - CI coverage is still RFC 0015-level

Severity: high

Existing tests cover raw-claim round trips, forbidden claim promotion,
deterministic generic prepare, readiness rejection, unavailable solver state,
and mock command failure. They do not cover the RFC 0026 fixture success path
or its fixture-specific failures.

Required safe-now tests:

- `fixture-local-command` appears in profile listing.
- Fixture prepare writes deterministic case files.
- Fixture run succeeds with schema-valid raw output and `raw_unvalidated`
  claim state.
- Missing command produces a persisted unavailable or failed record.
- Nonzero fixture command produces a persisted failed record.
- Clean command with missing raw output fails.
- Malformed raw output fails at the adapter/run layer.
- Fixture-success run records round-trip from disk.
- CLI run/status output keeps raw/unvalidated warning visibility.

Evidence:

- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:88`
- `tests/test_cfd_jobs.py:39`
- `tests/test_cfd_jobs.py:96`
- `tests/test_cfd_jobs.py:336`

### L-F6 - Raw/unvalidated semantics are sound but need fixture-specific persistence

Severity: medium

The domain-source review found no semantic conflict: the current claim gates
and CFD records already structurally preserve `raw_unvalidated` semantics.
`SolverProfile`, `CfdJobSpec`, `CfdRunRecord`, and `SolverRawResult` inherit
the raw/unvalidated claim fields, and existing tests reject calibrated or final
claim promotion. The CLI also prints the generic CFD raw-results warning on
prepare, status, and run.

RFC 0026 additionally requires successful fixture runs to include a warning
that fixture output is not calibrated, validated, or final design fitness. The
review artifacts recommend persisting that warning in the run/result record,
not only in CLI copy, so web and sweep callers see the same semantics.

Required safe-now action: ensure any new fixture raw-result model and run
record path remain `raw_unvalidated`, and persist or losslessly expose the
fixture-specific warning.

Evidence:

- `docs/rfcs/0025-cfd-calibration-claim-gates.md:69`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:67`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:86`
- `kayakgen/eval/cfd/jobs.py:41`
- `kayakgen/eval/cfd/jobs.py:75`
- `kayakgen/eval/cfd/jobs.py:131`
- `kayakgen/cli/main.py:180`
- `kayakgen/cli/main.py:207`
- `kayakgen/cli/main.py:230`
- `tests/test_cfd_jobs.py:72`

### L-F7 - Two RFC 0026 implementation choices need pinning before coding

Severity: low

The reviews agree that RFC 0026 is compatible with more than one fixture shape,
but implementation tests need stable choices:

- Fixture command shape: checked-in `python -m` module versus generated
  per-job script.
- Normalized output location: reuse `raw-result.json` versus introduce an
  `outputs/` manifest or directory.

Required safe-now action: choose and document these before or during the
implementation slice so tests lock the intended contract.

Evidence:

- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:93`

### L-F8 - RFC 0017 revision note is a documentation follow-up

Severity: low

RFC 0026 says it revises RFC 0017 by selecting a fixture/local-command adapter
slice before OpenFOAM, SU2, hosted execution, or validated solver dependency.
The traceability review notes that RFC 0017 still has no status note pointing
to RFC 0026.

Required safe-now action if documentation is in scope for the implementation
step: add a status note to RFC 0017 and update the RFC index if needed. This
ledger does not edit RFCs.

Evidence:

- `docs/rfcs/0017-first-real-cfd-adapter.md:3`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:5`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:90`

## Deferred / Out Of Scope

The following must remain deferred for this workflow:

- OpenFOAM, SU2, RANS, panel-method CFD, real solver adapter selection, and
  real solver installation requirements.
- Hosted or remote workers, Docker/container execution, queue scheduling,
  accounts, cost controls, cancellation, or multi-user operation.
- Real solver validation against measured kayak data.
- Calibration fixtures, fitted resistance models, removal of uncalibrated
  warnings, or analytical-resistance promotion.
- Final design-fitness scoring or any claim that fixture success establishes a
  design decision.
- Watertight solid dispatch, volume meshing, closed-volume `cfd_ready`
  promotion, or a second watertight fixture profile.
- Treating existing web raw-result routes as acceptance proof for RFC 0026; web
  artifact handling is supporting coverage, while adapter-level prepare/run and
  parser tests must land first.

Evidence:

- `docs/rfcs/0015-cfd-solver-dispatch-and-jobs.md:160`
- `docs/rfcs/0015-cfd-solver-dispatch-and-jobs.md:168`
- `docs/rfcs/0025-cfd-calibration-claim-gates.md:69`
- `docs/rfcs/0025-cfd-calibration-claim-gates.md:85`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:26`
- `docs/rfcs/0026-first-real-cfd-fixture-adapter.md:99`

## Conflict And Missing-Evidence Notes

No contract conflict was found. The apparent difference between review
verdicts is a scope distinction: the domain-source review accepts the semantic
foundation, while ops and traceability record that the RFC 0026 fixture adapter
implementation itself is still absent.

Missing evidence today:

- No implemented `fixture-local-command` profile.
- No `fixture_local_command` adapter route.
- No deterministic fixture case files.
- No successful fixture run.
- No schema-normalized fixture raw result.
- No adapter-level missing-output or malformed-output failure records.
- No RFC 0026 fixture test coverage.

## Landing Checklist

1. Resolve the fixture command and raw-output location choices.
2. Add and register `fixture-local-command` / `fixture_local_command`.
3. Render deterministic fixture case files during prepare.
4. Add a checked-in local fixture command or equivalent local executable.
5. Parse schema-valid normalized raw output into a raw/unvalidated fixture
   result.
6. Persist clear unavailable/failed records for missing command, nonzero exit,
   missing output, and malformed output.
7. Persist or losslessly expose the fixture-specific not-calibrated,
   not-validated, not-design-fitness warning.
8. Add the RFC 0026 test matrix without external solver dependencies.
9. Keep OpenFOAM, SU2, hosted execution, validation, calibration, watertight
   `cfd_ready`, and final design-fitness claims deferred.
