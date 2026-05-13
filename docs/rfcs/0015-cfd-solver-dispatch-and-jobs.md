# RFC 0015: CFD Solver Dispatch and Jobs

Status: proposed
Date: 2026-05-13
Context: RFC 0008 reserves heavy CFD jobs behind web stubs, RFC 0010 defines
mesh package/readiness metadata, and RFC 0012 keeps resistance calibration
claims separate from unvalidated solver output.

## Problem

The project can write mesh packages and analytical resistance reports, but it
has no contract for starting external solver work, recording run provenance, or
returning solver results to CLI/web/sweep callers.

Without a dispatch contract, future OpenFOAM, SU2, or hosted CFD work will
either leak tool-specific behavior into the domain model or create artifacts
that cannot be compared, reproduced, or failed safely.

## Goals

- Define a solver-agnostic CFD job specification.
- Store reproducible job/run artifacts on disk before adding remote execution.
- Keep solver adapters isolated behind a narrow boundary.
- Require mesh packages and readiness profiles before dispatch.
- Represent pending/running/succeeded/failed states consistently for CLI, web,
  and future hosted workers.
- Preserve the distinction between raw solver output and calibrated/validated
  resistance claims.

## Non-Goals

- Choosing a permanent hosted compute provider.
- Claiming OpenFOAM, SU2, or any external solver is validated for kayak design.
- Implementing cost controls, account management, multi-user scheduling, or
  cancellation guarantees.
- Making the current open wetted-surface package a watertight volume mesh.

## Proposal

Add `kayakgen.eval.cfd.jobs` with four small contracts:

```python
CfdJobSpec(
    job_id: str,
    hull_ref: str,
    mesh_package_ref: str,
    solver_profile: str,
    speed_mps: float,
    seawater_density_kg_m3: float,
    kinematic_viscosity_m2_s: float,
    created_at: str,
)

CfdRunRecord(
    job_id: str,
    status: Literal["queued", "running", "succeeded", "failed", "unavailable"],
    solver_profile: str,
    input_manifest: str,
    output_manifest: str | None,
    started_at: str | None,
    finished_at: str | None,
    error_kind: str | None,
    error_message: str | None,
)

SolverProfile(
    name: str,
    required_mesh_readiness: str,
    adapter_name: str,
    container_image: str | None,
    command_template: list[str],
)

SolverAdapter(
    prepare(job_spec, mesh_package) -> PreparedSolverCase,
    run(prepared_case) -> SolverRawResult,
    collect(prepared_case) -> CfdRunRecord,
)
```

The first dispatch backend is a local filesystem queue. It writes one directory
per job with:

- `job.json`;
- copied or referenced mesh package manifest;
- solver input files;
- `run.json`;
- solver logs;
- raw force/residual outputs when available.

CLI starts with:

```text
kayakgen cfd prepare hull.json --mesh-package mesh-package/ --solver-profile NAME --out jobs/
kayakgen cfd run jobs/JOB_ID/
kayakgen cfd status jobs/JOB_ID/
```

The web frontend may expose the same states, but any unavailable solver must
remain visibly unavailable rather than pretending to run. Remote or hosted
dispatch can later implement the same `CfdJobSpec` and `CfdRunRecord` contract.

## Acceptance Criteria

- CFD job specs and run records serialize and round-trip.
- `cfd prepare` refuses missing mesh packages and mesh readiness below the
  selected solver profile requirement.
- Local jobs are deterministic enough to compare manifests in tests.
- Failed solver commands produce `failed` run records with `error_kind` and
  `error_message`.
- Uninstalled solver profiles produce `unavailable`, not silent success.
- CLI and web status wording make clear when results are raw/unvalidated.
- Tests cover prepare success, readiness rejection, unavailable solver, failed
  command, and run-record parsing.

## Open Questions

- Which external solver adapter should be first: OpenFOAM, SU2, or a local
  mock adapter that only validates the dispatch contract?
- Should the first real profile target open wetted-surface resistance or wait
  for watertight solid/volume readiness?
- What minimum residual/force outputs must be normalized into comparison
  records?
- Should solver jobs live under sweep run records, or remain separate artifacts
  linked by reference?

## Implementation Path

- Step 1 - Add job spec, run record, solver profile, and local filesystem
  queue models.
- Step 2 - Add `kayakgen cfd prepare/status` using existing mesh packages.
- Step 3 - Add an unavailable/mock adapter so web and CLI can exercise states
  without external solver installation.
- Step 4 - Add `kayakgen cfd run` for local command adapters with failure
  capture.
- Step 5 - Implement the first real solver adapter only after the target mesh
  readiness profile is accepted.

## Domain Modeling

`CfdJobSpec` and `CfdRunRecord` are domain events/read models at the boundary
between kayak generation and external solver infrastructure. `SolverAdapter` is
an anti-corruption layer for tool-specific CFD behavior.
