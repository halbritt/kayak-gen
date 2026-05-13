# RFC 0015: CFD Solver Dispatch and Jobs

Status: partial local-dispatch
Date: 2026-05-13
Context: RFC 0008 reserves heavy CFD jobs behind web stubs, RFC 0010 defines
mesh package/readiness metadata, and RFC 0012 keeps resistance calibration
claims separate from unvalidated solver output.

Status note (workflow 0024, 2026-05-13): mesh packages now expose a named
watertight-required profile, `watertight_solid_resistance_v1`, that dispatch can
use as a readiness gate. The current generated package is still rejected below
`cfd_ready` by that profile.

Status note (workflow 0025, 2026-05-13): RFC 0015 has landed only as a
deterministic local-dispatch slice. The landed boundary covers serializable job
and run records, solver profiles, local job directories, mesh package readiness
gating, CLI prepare/status/run/profiles surfaces, unavailable solver state, and
a mock failed-command state. It does not run OpenFOAM, SU2, hosted workers,
Docker, or any validated solver. All CFD job/status wording remains raw and
unvalidated.

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

Add `kayakgen.eval.cfd.jobs` with four small contracts. Workflow 0025 landed the
local filesystem version of these contracts; the adapter interface remains the
boundary for future real solver integrations rather than evidence that one is
available today.

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
- copied or referenced mesh package manifest, kept reproducible without copying
  large STL artifacts by default;
- solver input files;
- `run.json`;
- solver logs;
- raw force/residual outputs when available.

CLI starts with:

```text
kayakgen cfd prepare hull.json --mesh-package mesh-package/ --solver-profile NAME --out jobs/
kayakgen cfd run jobs/JOB_ID/
kayakgen cfd status jobs/JOB_ID/
kayakgen cfd profiles
```

The landed local profiles are intentionally narrow: an unavailable profile can
exercise the state model without a solver binary, and a mock local-command
profile can exercise failed-command capture. Profiles enforce their required
mesh readiness level during `prepare`; current open wetted-surface packages may
exercise `cfd_surface_candidate` dispatch states, while
`watertight_solid_resistance_v1` still requires `cfd_ready` and rejects current
packages.

The web frontend may later expose the same states, but workflow 0025 does not
add web job routes. Any unavailable solver must remain visibly unavailable
rather than pretending to run. Remote or hosted dispatch can later implement the
same `CfdJobSpec` and `CfdRunRecord` contract.

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

Workflow 0025 accepts only the local-dispatch subset of these criteria. CLI
status must continue to say that CFD outputs are raw and unvalidated; run
records must not imply calibrated resistance, validated drag, Pareto scoring, or
final design fitness. Web status wording remains an RFC requirement, not a
workflow 0025 implementation claim.

## Landed Local Slice

- Serializable `CfdJobSpec`, `CfdRunRecord`, and `SolverProfile` records.
- Deterministic local job directories with small JSON artifacts and logs.
- Mesh package manifest loading and solver-profile readiness rejection.
- Positive speed, seawater density, and kinematic viscosity validation.
- CLI `cfd prepare`, `cfd status`, `cfd run`, and `cfd profiles` surfaces.
- Unavailable profile behavior that records `status: unavailable`.
- Mock failed-command behavior that records `status: failed`, `error_kind:
  command_failed`, error text, and logs.

## Deferred

- Real OpenFOAM, SU2, RANS, Docker/container, hosted, or remote execution.
- Cancellation, scheduling, cost controls, accounts, and multi-user operation.
- Watertight solid geometry, volume meshing, end caps, or current `cfd_ready`
  success.
- Normalized force/residual comparison records from real solver output.
- Calibrated, validated, or final resistance claims from CFD output.
- Web job routes, hosted progress UI, and browser acceptance for job dispatch.

## Open Questions

- Which external solver adapter should be first: OpenFOAM, SU2, or a local
  command adapter beyond the current mock failure profile?
- Should the first real solver adapter target the existing open wetted-surface
  profile, or wait for a future geometry workflow that satisfies
  `watertight_solid_resistance_v1`?
- What minimum residual/force outputs must be normalized into comparison
  records?
- Should solver jobs live under sweep run records, or remain separate artifacts
  linked by reference?

## Implementation Path

- Step 1 - Land job spec, run record, solver profile, and local filesystem
  queue models. Done in the local-dispatch slice.
- Step 2 - Add `kayakgen cfd prepare/status` using existing mesh packages. Done
  in the local-dispatch slice.
- Step 3 - Add unavailable and mock failed-command behavior so CLI can exercise
  states without external solver installation. Done in the local-dispatch
  slice.
- Step 4 - Add local command failure capture for `kayakgen cfd run`. Done only
  for mock failed-command semantics.
- Step 5 - Implement the first real solver adapter only after the target mesh
  readiness profile is accepted. Deferred.

## Domain Modeling

`CfdJobSpec` and `CfdRunRecord` are domain events/read models at the boundary
between kayak generation and external solver infrastructure. `SolverAdapter` is
an anti-corruption layer for tool-specific CFD behavior.
