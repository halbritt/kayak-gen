# RFC 0041: Real CFD Adapter Successor

Status: landed real openfoam-v2512-interfoam-local succeeded path (opt-in env-gated); claim_state stays raw_unvalidated
Date: 2026-05-14
Context: successor to RFC 0017 after RFC 0026 landed the deterministic
`fixture-local-command` adapter. Builds on RFC 0015 local CFD job records, RFC
0010 mesh package/readiness profiles, RFC 0023 watertight evidence handoff, and
RFC 0025 claim gates. RFC 0040 is the companion closed-volume solver-readiness
roadmap; this RFC consumes its profile gate when a selected solver needs
watertight input. Companion geometry/readiness work must remain separate from
this adapter RFC unless an accepted workflow explicitly combines them.
Disposition of predecessor: RFC 0041 revises RFC 0017 as the current
external-solver successor. RFC 0026 remains the landed fixture-local-command
adapter slice and is not superseded; this RFC resumes the deferred real
external-solver path after that fixture boundary.

## Problem

RFC 0015 gives the project a local CFD job store and adapter boundary. RFC 0026
proved that boundary with a deterministic fixture command that can succeed in
CI without an external solver. The project still has no accepted path for a
real external CFD solver adapter.

The remaining risk is not just "pick a solver and run it." A real adapter can
cross several evidence boundaries at once:

- dependency detection and platform installation;
- deterministic case-template generation;
- mesh-profile and readiness gates;
- solver logs, residuals, and raw force artifact collection;
- failure-state persistence;
- claim wording that keeps raw solver output separate from calibrated
  resistance and final design fitness.

If those boundaries are not explicit, a successful local command could be
mistaken for calibrated CFD, a generated open-surface package could be treated
as watertight input, or solver-specific files could leak into core hull and
evaluation models.

## Goals

- Define the first external-solver adapter slice after the fixture adapter.
- Require a named solver target, install check, case-template version, mesh
  profile, and raw-output parser before implementation begins.
- Reuse `CfdJobSpec`, `CfdRunRecord`, `SolverProfile`, `SolverAdapter`, local
  job directories, and existing web/CLI status surfaces.
- Keep mesh readiness gates authoritative: insufficient or forged evidence must
  fail at prepare time before solver execution.
- Persist solver version, command provenance, stdout/stderr logs, raw artifact
  refs, residual summaries, and raw force outputs when available.
- Treat every real-solver output as `raw_unvalidated` unless a separate
  calibration/validation RFC later accepts stronger evidence.
- Keep CI coverage possible without requiring an installed external solver.

## Non-Goals

- No claim that OpenFOAM, SU2, or any other solver already runs in this
  project.
- No production volume meshing, boundary-layer meshing, container execution, or
  hosted worker infrastructure.
- No calibrated CFD, calibrated analytical resistance, accepted final
  prediction, final design fitness, or Pareto-default scoring.
- No broad watertight or `cfd_ready` promotion for generated packages. A real
  adapter may consume `watertight_solid_resistance_v1` only when the package
  already carries verified matching evidence under RFC 0023 or its successor.
- No second solver adapter in the first implementation slice.
- No new browser route shape, authentication, cancellation, scheduling, cost
  controls, or multi-user job system.
- No changes to the `Hull` aggregate or parametric geometry model.

## Dependencies

- RFC 0010 for mesh packages, readiness levels, and solver-profile vocabulary.
- RFC 0015 for `CfdJobSpec`, `CfdRunRecord`, local job directories, and adapter
  boundaries.
- RFC 0023 and RFC 0040 for watertight-required profile evidence if the
  selected solver needs closed-body and volume-mesh handoff artifacts.
- RFC 0025 and RFC 0027 for claim gates that keep solver output raw unless a
  separate validation or calibration workflow accepts stronger evidence.
- RFC 0026 for the fixture-local-command lifecycle, raw-result location, and
  CI-friendly adapter proof.
- RFC 0018 only as the existing local web route consumer; hosted workers or new
  route shapes stay outside this RFC.

## Missing Evidence And Gates

This RFC may advance only by making missing evidence visible. It does not treat
any item below as already satisfied.

1. **Solver selection gate.** A short implementation decision must name exactly
   one local external solver target before code lands. Candidate names such as
   OpenFOAM or SU2 remain candidates until that decision records the selected
   executable commands, version command, license/install notes, supported
   platforms, and expected output files.
2. **Mesh-profile gate.** The selected adapter must declare one accepted mesh
   profile. If it requires `watertight_solid_resistance_v1`, prepare must reject
   all packages without verified matching closed-body, self-intersection, and
   volume-mesh evidence satisfying RFC 0040's readiness profile gate, or an
   accepted narrower workflow that explicitly consumes landed RFC 0023 handoff
   evidence as that gate. If it targets an open-surface profile, the decision
   must document why that solver mode is physically and operationally coherent
   and must not imply watertight readiness.
3. **Case-template gate.** Case generation must be deterministic from the job
   spec, mesh package manifest, speed/fluid inputs, and a versioned template.
4. **Execution gate.** Missing binaries, failed version checks, nonzero solver
   exits, timeouts, missing raw outputs, malformed outputs, and parser
   mismatches must persist `unavailable` or `failed` run records with stable
   `error_kind` values and human-readable messages.
5. **Raw-result gate.** A `succeeded` run means the command exited cleanly and
   the required raw artifacts parsed. It does not mean validated drag,
   calibrated resistance, or design fitness.
6. **Optional integration gate.** Installed-solver tests may run only when an
   explicit environment flag and solver binary are present. Required CI must use
   fixture files and fake commands to prove adapter behavior without real solver
   installation.

## Proposal

Add one external-solver adapter under the existing local CFD dispatch boundary.
The adapter is selected by a small pre-implementation decision record rather
than by this RFC text alone. The decision record must fill this profile shape:

```python
ExternalSolverProfile(
    name: str,
    adapter_name: str,
    solver_name: str,
    solver_version_command: list[str],
    required_mesh_readiness: str,
    required_mesh_profile: str,
    case_template_version: str,
    supported_speed_range_mps: tuple[float, float],
    supported_fluid_model: str,
    expected_raw_outputs: tuple[str, ...],
    result_semantics: Literal["raw_unvalidated"],
)
```

The adapter has the same lifecycle as the fixture adapter:

1. `prepare` validates the mesh package and writes deterministic case files.
2. `run` checks dependency availability, invokes the solver command locally,
   captures logs, and writes an updated `run.json`.
3. `collect` parses only the agreed raw artifacts into a normalized raw result.

Normalized output is intentionally small:

```python
CfdExternalRawResult(
    job_id: str,
    solver_name: str,
    solver_version: str,
    case_template_version: str,
    speed_mps: float,
    seawater_density_kg_m3: float,
    kinematic_viscosity_m2_s: float,
    mesh_profile: str,
    mesh_readiness: str,
    drag_force_n: float | None,
    residual_summary: dict[str, float],
    raw_output_refs: list[str],
    warnings: list[str],
    claim_state: Literal["raw_unvalidated"],
)
```

The parser must tolerate the selected solver's native files by translating only
the fields the project has explicitly accepted. It must not infer calibrated
physics from solver names, residual convergence, force monotonicity, or
agreement with analytical resistance. Those checks may become validation
evidence only through a later calibration or validation RFC.

### Mesh Readiness

Adapter prepare uses the solver profile's declared mesh requirement as a hard
gate:

- `open_wetted_surface_resistance_v1` may be accepted only for a solver mode
  whose decision record states the required boundary semantics and limitations.
- `watertight_solid_resistance_v1` may be accepted only when the mesh package
  already satisfies the evidence-bound `cfd_ready` handoff for the same body,
  hull hash, profile, tolerances, diagnostics, artifacts, and checksums.
- Hand-edited readiness strings, synthetic closed-volume diagnostics, stale
  hashes, cross-body evidence, missing volume-mesh diagnostics, or failed
  self-intersection evidence must be rejected before any solver command runs.

### CLI And Web Surface

No new command family or route shape is required. The adapter should appear as
a normal solver profile through:

```text
kayakgen cfd profiles
kayakgen cfd prepare
kayakgen cfd run
kayakgen cfd status
GET/POST /api/cfd/*
```

Existing web routes may surface the new profile and run states through the
current local filesystem job contract. They must continue to label all outputs
as raw and unvalidated. Hosted workers, browser-side meshing, and asynchronous
queue semantics remain future RFC scope.

## Acceptance Criteria

- A pre-implementation decision names exactly one external solver target and
  records installation prerequisites, version command, supported platforms,
  mesh profile, case-template version, expected raw outputs, and known
  limitations.
- The built-in profile list exposes the selected adapter only with
  `result_semantics="raw_unvalidated"`.
- `cfd prepare` writes deterministic case files for the selected profile and
  refuses mesh packages below the profile's readiness requirement.
- If the selected solver profile requires `watertight_solid_resistance_v1`, no
  real solver `succeeded` path may be enabled until the package satisfies RFC
  0040's readiness profile gate, or an accepted narrower workflow explicitly
  consumes landed RFC 0023 handoff evidence as that gate.
- Prepare rejects forged, stale, synthetic, cross-body, cross-profile, missing,
  or malformed watertight evidence before solver execution.
- Missing solver binaries or failed version checks produce `unavailable`
  records, not silent success.
- Nonzero solver exits, timeouts, missing raw output files, malformed raw
  output, and parser/job mismatches produce `failed` records with stable
  `error_kind` and `error_message`.
- Successful runs capture solver version, command argv, stdout/stderr logs,
  raw artifact refs, residual summaries when available, and a normalized raw
  drag field only when the parser can prove the source field.
- `cfd status`, web job payloads, run records, and raw-result payloads continue
  to expose `raw_unvalidated` claim metadata and warnings.
- Required tests do not need an installed external solver. They cover profile
  registration, deterministic prepare, readiness rejection, dependency
  unavailable, command failure, missing/malformed output, parser success from
  fixture files, run-record round trip, and forbidden claim promotion.
- Optional installed-solver smoke tests are skipped unless an explicit
  environment flag and selected solver executable are present.
- Documentation for the adapter states that solver success is not calibrated
  CFD, not a final prediction, and not design fitness.

## Open Questions

- Which solver target has the lowest maintenance cost for contributors while
  still accepting a mesh profile the project can honestly produce?
- Should the first external adapter wait for watertight-solid evidence, or is a
  documented open-surface resistance mode acceptable as an incremental raw
  solver path?
- Which raw outputs are the minimum useful first parser: total drag only,
  residuals plus drag, or a pressure/friction decomposition when the solver
  exposes it?
- What timeout and log-size limits keep local runs bounded without turning this
  into hosted job management?
- Should optional installed-solver smoke tests live under the normal test suite
  with skips, or under a separate integration-test marker?

## Implementation Path

1. Write the solver-selection decision record for one adapter target, including
   install, version, mesh profile, case-template, raw-output, and limitation
   fields.
2. Add profile metadata and dependency detection while preserving existing
   unavailable and fixture profiles.
3. Render deterministic case files from `CfdJobSpec` and `MeshPackageManifest`
   behind the existing `SolverAdapter.prepare` boundary.
4. Add local command execution with bounded logs, timeout handling, version
   capture, and stable failure records.
5. Add the raw-output parser and normalized `CfdExternalRawResult` fixture
   tests before enabling a `succeeded` path.
6. Add optional installed-solver smoke coverage guarded by an explicit
   environment flag.
7. Update CLI/web/docs wording only after the adapter behavior lands, keeping
   all outputs raw/unvalidated and all calibration/final-prediction wording
   behind later RFC gates.

## Domain Modeling

The real CFD adapter is an anti-corruption layer at the external solver
boundary. It translates project job records and mesh packages into a
tool-specific case directory, then translates tool-specific logs and raw force
files back into project read models. It does not change `Hull`, does not decide
mesh readiness, and does not promote resistance claims.
