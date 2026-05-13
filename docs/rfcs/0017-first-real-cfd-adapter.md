# RFC 0017: First Real CFD Adapter

Status: proposed
Date: 2026-05-13
Context: builds on RFC 0010 mesh packages, RFC 0015 local CFD job dispatch,
and RFC 0012 resistance provenance boundaries.

## Problem

RFC 0015 defines deterministic local CFD job records and adapter boundaries,
but it intentionally stops before running a real solver. The next step needs a
single real adapter with narrow scope, clear installation requirements,
repeatable case generation, and raw-output labeling.

Without a focused first adapter, solver-specific setup can leak into the domain
model or produce results that users mistake for calibrated resistance.

## Goals

- Select one first real solver adapter and define its minimum supported case.
- Reuse `CfdJobSpec`, `CfdRunRecord`, solver profiles, and mesh readiness gates.
- Capture raw force, residual, runtime, and solver-version provenance.
- Fail visibly when the solver is unavailable, misconfigured, or given an
  insufficient mesh package.
- Keep all outputs marked raw and unvalidated.

## Non-Goals

- Validating CFD predictions against measured kayak data.
- Providing hosted execution, queue scheduling, accounts, or cost controls.
- Supporting multiple solvers in the first implementation.
- Calibrating analytical resistance from CFD results.
- Bypassing mesh readiness or closed-volume requirements.

## Dependencies

- RFC 0015 local job dispatch and run-record persistence.
- RFC 0010 mesh-package manifests and named readiness profiles.
- RFC 0016 if the selected adapter requires a watertight closed volume.
- RFC 0012 for result provenance and unvalidated-output warnings.

## Proposal

Add one concrete adapter under the existing `SolverAdapter` boundary. The RFC
does not choose the solver in advance; acceptance requires a follow-up decision
record naming the adapter target before implementation starts.

Candidate targets:

- an OpenFOAM steady resistance case using a watertight solid profile;
- an SU2 external-flow case if mesh preparation is simpler;
- a local command adapter that runs a checked-in deterministic solver fixture
  only if a full solver is too large for the first slice.

The selected adapter profile must declare:

```python
RealSolverProfile(
    name: str,
    solver_name: str,
    solver_version_command: list[str],
    required_mesh_profile: str,
    case_template_version: str,
    supported_speed_range_mps: tuple[float, float],
    outputs: list[str],
    validation_status: Literal["unvalidated"],
)
```

Case generation writes a complete solver directory from the job spec and mesh
package. Collection parses only a small normalized result:

```python
CfdRawResistanceResult(
    job_id: str,
    speed_mps: float,
    drag_force_n: float | None,
    residual_summary: dict[str, float],
    solver_version: str,
    warnings: list[str],
)
```

The adapter may return `succeeded` only when the solver command exits cleanly
and required raw files are present. It must still mark the result unvalidated.

## Acceptance Criteria

- One real adapter profile is named and documented with installation
  prerequisites.
- `cfd prepare` writes deterministic solver input files for that profile.
- `cfd run` captures solver version, stdout/stderr logs, exit status, and raw
  output paths.
- `cfd status` and run records continue to label results raw and unvalidated.
- Missing solver binaries produce `unavailable`.
- Bad commands or missing output files produce `failed` with `error_kind`.
- Tests cover case generation, unavailable solver, failed collection, and a
  tiny deterministic success fixture that does not require validated physics.

## Open Questions

- Should the first adapter wait for `watertight_solid_resistance_v1`, or target
  an open-surface candidate profile first?
- Which solver has the lowest maintenance cost for contributors on Linux,
  macOS, and CI?
- What raw output is the minimum useful comparison record: total drag only,
  drag plus residuals, or pressure/friction decomposition?
- Should adapter tests run only against fixtures, or should an optional
  integration test run when the solver is installed?

## Implementation Path

- Step 1 - Choose the first solver target and document required mesh profile.
- Step 2 - Add adapter profile metadata and dependency checks.
- Step 3 - Add deterministic case-template rendering.
- Step 4 - Add command execution and raw-output collection behind existing job
  records.
- Step 5 - Add fixture tests and optional installed-solver integration tests.

## Domain Modeling

The real solver adapter is an anti-corruption layer at the CFD infrastructure
boundary. It produces read models and run events, but it does not alter the
`Hull` aggregate or create calibrated resistance claims.
