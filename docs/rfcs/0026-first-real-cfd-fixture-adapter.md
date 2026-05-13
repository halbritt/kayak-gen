# RFC 0026: First Real CFD Fixture Adapter

Status: landed fixture-local-command
Date: 2026-05-13
Context: revises RFC 0017 by selecting a deterministic fixture/local-command
adapter slice before any OpenFOAM, SU2, hosted, or validated solver dependency.

## Problem

RFC 0017 asks for the first real CFD adapter, but it leaves the target open.
OpenFOAM or SU2 would force solver installation, mesh-readiness, case-template,
and physics questions into the first slice. The current job boundary in RFC
0015 is ready for adapter work, but the project still needs a deterministic
success path that exercises prepare/run/collect semantics without claiming real
CFD validation.

## Goals

- Choose the first adapter slice: a deterministic local-command fixture adapter.
- Exercise the existing `CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, mesh
  readiness, logs, and raw-output collection boundaries.
- Require no external solver binary in CI.
- Preserve `raw_unvalidated` semantics for all outputs.
- Create the adapter shape that a later OpenFOAM or SU2 adapter can reuse.

## Non-Goals

- Running OpenFOAM, SU2, RANS, or panel-method CFD.
- Validating CFD predictions against measured kayak data.
- Calibrating analytical resistance from fixture output.
- Promoting fixture adapter success to final design fitness.
- Bypassing mesh readiness requirements for future watertight solvers.

## Proposal

Supersede RFC 0017's undecided first-adapter target with a local fixture
adapter profile:

```python
SolverProfile(
    name="fixture-local-command",
    required_mesh_readiness="cfd_surface_candidate",
    adapter_name="fixture_local_command",
    required_mesh_profile="open_wetted_surface_resistance_v1",
    result_semantics="raw_unvalidated",
)
```

The adapter writes a deterministic case directory, invokes a checked-in Python
module with `python -m kayakgen.eval.cfd.fixture_command`, and collects a
normalized raw record from `raw-result.json` at the prepared job directory root:

```python
CfdFixtureRawResult(
    job_id: str
    speed_mps: float
    drag_force_n: float
    residual_summary: dict[str, float]
    fixture_version: str
    command: list[str]
    returncode: int
    claim_state: Literal["raw_unvalidated"]
    warnings: list[str]
)
```

The fixture output may be numerically plausible, but it is not a solver
validation source and is not calibration data. It exists to prove adapter
plumbing: deterministic inputs, command execution, stdout/stderr capture,
missing-output failure, malformed-output failure, and normalized raw result
collection.

The existing unavailable and failing-command profiles remain. The new fixture
profile adds a deterministic success profile that CI can run without an
external CFD installation. Workflow 0037 pins this fixture slice to
`open_wetted_surface_resistance_v1`; no watertight fixture profile is part of
this RFC.

## Acceptance Criteria

- A built-in fixture/local-command profile is documented and listed by the CLI.
- `cfd prepare` writes deterministic profile, job, run, and adapter case files
  for the fixture profile.
- `cfd run` succeeds only when the fixture command exits cleanly and required
  raw output is present and schema-valid.
- Missing command, nonzero command, missing output, and malformed output produce
  `unavailable` or `failed` with `error_kind` and `error_message`.
- Successful fixture runs still say `raw_unvalidated` and include a warning
  that fixture output is not calibrated, validated, or final design fitness.
- Tests require no external solver and cover prepare, success, unavailable,
  command failure, missing output, malformed output, and run-record round trip.
- RFC 0017 is treated as revised: OpenFOAM/SU2 selection remains deferred until
  this adapter boundary is accepted and a mesh profile can support it.

## Workflow 0037 Pinned Choices

- The fixture command is a checked-in Python module invoked with
  `python -m kayakgen.eval.cfd.fixture_command`, not a generated per-job script.
- Normalized fixture output lives at `raw-result.json` in the prepared job
  directory.
- The fixture profile accepts only `open_wetted_surface_resistance_v1` and
  remains `raw_unvalidated`.
- OpenFOAM/SU2 selection from RFC 0017 remains deferred until a later RFC slice
  has the mesh profile and maintenance plan to support it.

## Implementation Path

1. Add `fixture_local_command` as a new adapter name and profile.
2. Render deterministic case inputs from job spec and mesh package metadata.
3. Add the fixture command and normalized raw-output parser.
4. Extend CLI profile/run/status tests for deterministic success and failure
   modes.
5. Keep all output metadata wired to RFC 0025 claim gates.
