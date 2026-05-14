---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-007
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_25abcf51f7544cb8ac8313b98c35e6ed
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_solver_path_claude
lease: lease_efe719fa6b224666b3fbf37c6a081f86

# Panel Vote — CFD Solver Path

## Vote

**Option A — OpenFOAM.com v2512 `interFoam`, gated behind
`watertight_solid_resistance_v1` / `cfd_ready` evidence.** Selection
plus adapter-skeleton scope only; no real `succeeded` path is
authorized by this decision.

## Decision Sentence For `docs/DECISION_LOG.md`

Adopt OpenFOAM.com OpenFOAM-v2512 `interFoam` as the first real
external CFD solver target for kayak-gen, under the local-command
adapter boundary defined by RFC 0015 / RFC 0026. The selected solver
profile is `openfoam-v2512-interfoam-local`, the required mesh
profile is `watertight_solid_resistance_v1`, the required readiness
is `cfd_ready` (as already gated by RFC 0023 handoff evidence and
its RFC 0040 successor), and the case-template version is
`openfoam-v2512-interfoam-dtchull-v1` — a project-owned deterministic
template informed by, but not vendored verbatim from, the official
OpenFOAM-v2512 `multiphase/interFoam/RAS/DTCHull` tutorial. Initial
parser scope is limited to solver version/provenance, run logs, and
raw `postProcessing/forces/<time>/force.dat` files; the normalized
`drag_force_n` is the accepted total-force vector projected onto the
job velocity axis under kayak-gen's stern-positive X convention.
Linux is the primary supported platform; macOS and Windows are
documented as optional Docker/WSL/source environments and are not
required for CI. Required CI uses fake commands and fixture files
only; installed-solver smoke runs require an explicit environment
flag. This decision authorizes profile metadata, dependency
detection, deterministic case rendering, unavailable/failed-state
behavior, and parser fixture coverage; it does **not** enable a
real OpenFOAM `succeeded` path. No real `succeeded` path may be
enabled until the package satisfies RFC 0040's readiness profile
gate, or an accepted narrower workflow explicitly consumes landed
RFC 0023 handoff evidence as that gate, for an OpenFOAM-readable
volume-mesh handoff.

## Evidence

### Research-Packet Evidence

- `striatum/0050-decision-panel-research/research/solver_path/RESEARCH.md`
  recommends Option A and supports it with seven external citations
  (OpenFOAM current-release page, v2512 release notes, the v2512
  DTCHull `Allrun` and `controlDict`, `snappyHexMesh` geometry guide,
  `forceCoeffs` post-processing docs) accessed 2026-05-14. The two
  load-bearing facts for this vote are: (a) OpenFOAM-v2512 ships a
  maintained `multiphase/interFoam/RAS/DTCHull` tutorial that uses
  `interFoam` with a `forces` function object on the hull patch under
  water density — a documented free-surface ship-hull resistance
  workflow; and (b) the OpenFOAM repository moved to GitLab, so a
  pinned release line (v2512) rather than a floating repo path is
  required.
- The same packet's SU2 citations (GitHub releases, theory docs,
  custom-output docs, mesh-file docs) confirm SU2 has working
  incompressible RANS solvers, a clean `history.csv` output, and a
  documented install/build path, but the maintained sources surfaced
  here do not include a comparable first-party free-surface
  ship-resistance tutorial. That asymmetry is the difference between
  "ready to wire a parser" and "ready to wire a kayak-relevant
  case."
- The packet anchors the option set to project boundaries already in
  the repo: RFC 0041 requires a named solver target, install/version
  notes, mesh profile, deterministic case template, raw-output
  parser scope, and CI strategy *before* code lands. RFC 0040 stages
  the production volume-mesh evidence path the eventual `succeeded`
  path must consume. RFC 0025 keeps all real-solver output
  `raw_unvalidated`. Those constraints are not relaxed by this vote.

### Independent Check On Current Code (verified this session)

The research packet's claims about the current adapter surface are
real, not aspirational:

- `kayakgen/eval/cfd/jobs.py:30` defines
  `CfdAdapterName = Literal["unavailable", "mock_local_command",
  "fixture_local_command"]` — there is no `openfoam` or `su2`
  adapter today.
- `kayakgen/eval/cfd/jobs.py:35` pins
  `FIXTURE_CASE_TEMPLATE_VERSION = "fixture-local-command-v1"` and
  `FIXTURE_RAW_OUTPUT = "raw-result.json"`, consistent with RFC 0026
  and the user guide.
- `SolverProfile` (`jobs.py:60-72`) already carries
  `required_mesh_readiness`, `required_mesh_profile`,
  `adapter_name`, `command_template`, and
  `result_semantics="raw_unvalidated"`. That is the exact field set
  RFC 0041 requires for an external solver profile, so the
  decision's profile shape is structurally feasible without changing
  upstream models. The named adapter literal will need to grow one
  member when the implementation slice lands.
- `CfdJobSpec` (`jobs.py:74-92`) and `CfdRunRecord` (`jobs.py:95-113`)
  already record `mesh_evidence_hashes`, `mesh_readiness`,
  `mesh_warnings`, `error_kind`, `error_message`, and
  `result_semantics="raw_unvalidated"`. The plumbing for prepare-time
  evidence rejection, stable error kinds, and raw/unvalidated wording
  is in place.
- `kayakgen/eval/cfd/` lists only `__init__.py`, `fixture_command.py`,
  and `jobs.py`. There is no `openfoam`, `su2`, or external-adapter
  module that this vote conflicts with.

The cross-check is also consistent with the sibling decision: this
panel run's `panels/solver_readiness/claude/VOTE.md` (D055-style
posture) explicitly stated that the solver-readiness vote "does not
select a production mesher or solver" and listed RFC 0041 as the
proper home for that selection. This solver_path vote is the sibling
that names the solver under the gates that vote left intact.

### Independent Domain Check

- `docs/PRD.md:42` records the current CFD state as "job/run/profile
  plumbing with readiness gates, local artifact directories,
  unavailable solver state, mock failed-command state, CLI commands,
  and local web job routes. It does not run OpenFOAM, SU2, hosted
  workers, Dockerized solvers, or any real CFD adapter." Choosing
  OpenFOAM v2512 here does not change that statement; the no-claim
  remains true until `succeeded` runs land.
- `docs/ROADMAP.md:69` ("CFD dispatch and real adapter" track) says
  the next work is to "Make a solver-selection decision, choose a
  mesh profile, define case-template and raw-output parser gates,
  then implement one external adapter with required CI not depending
  on installed solver binaries. Outputs remain `raw_unvalidated`."
  This vote is literally the first sentence of that paragraph.
- `docs/ROADMAP.md:Batch E` (`:145-164`) lists "one solver target
  selected by decision record; explicit installation/version/platform
  notes; chosen mesh profile and readiness gate; deterministic
  case-template version; expected raw outputs and parser scope;
  required tests that do not require the solver binary" as the
  prerequisites the implementation workflow must satisfy before
  starting. Option A names all six.
- `docs/design/kayak_hull_design_constraints.md` (§10 pipeline
  strategy) puts CFD as the final stage after cheaper geometric and
  hydrostatic filters. Choosing a solver-selection decision now,
  while leaving the `succeeded` path gated on volume-mesh evidence,
  is consistent with that ordering; choosing a path that would
  require enabling a `succeeded` run on open-surface packages
  (Option B) would invert it.
- `docs/USER_GUIDE.md`, `docs/DECISION_LOG.md`, `AGENTS.md`, and
  `docs/workflows/0018-deferred-backlog/QUEUE.md` reviewed for
  conflicts; none found. The deferred queue's item "0025 CFD solver
  dispatch and jobs" maps to "RFC 0041 and later validation/
  calibration work" — exactly the path this vote takes.

### External-Source Check

I did not re-fetch the seven external URLs cited by the research
packet from this session (`WebFetch` is not loaded in the current
tool surface, and the citations are dated 2026-05-14 to match this
run). The claim-to-source mapping is sound on its face: the OpenFOAM
DTCHull tutorial path is a long-standing maintained free-surface
hull case under `interFoam` with a `forces` post-processing object,
and the v2512 release line and GPL/GitLab posture are stable public
facts. The single load-bearing inference — that a first-party
maintained ship-resistance template family carries more domain
weight for "first real kayak-relevant adapter" than a clean parser
for a generic incompressible external-flow solver — does not turn
on a contested URL; it turns on the *existence* of a maintained
template family, which the cited tutorial demonstrates. Nothing in
the local repo or roadmap contradicts the cited facts.

## Why Rejected Alternatives Lose

### Option B — OpenFOAM open-surface adapter under `open_wetted_surface_resistance_v1`

Loses because it conflates two decisions: "which solver target?" and
"is open-surface real-solver dispatch physically and operationally
coherent for kayak hulls?" RFC 0041 explicitly allows
`open_wetted_surface_resistance_v1` "only for a solver mode whose
decision record states the required boundary semantics and
limitations" and "must not imply watertight readiness"
(`docs/rfcs/0041-real-cfd-adapter-successor.md:96-102`). The current
generated open hull/deck STLs are inspection surfaces, not a
boundary-condition contract for free-surface or submerged
ship-resistance physics. Choosing Option B now would either:

- pre-commit to an open-surface physics envelope this project has
  not characterized and the research packet did not characterize,
  risking implied claims that exceed the no-claims rule at
  `docs/ROADMAP.md:44-47`; or
- ship an "OpenFOAM solver smoke" capability under a name that users
  reasonably read as kayak resistance, which the panel
  `solver_readiness` decision and this vote both refused for
  surface-only solver profiles.

Nothing in the maintained OpenFOAM sources cited supports an
open-surface RANS resistance workflow as the *first* template family
for a kayak; the DTCHull tutorial is a free-surface watertight-hull
case. Option B trades the strongest domain evidence the research
packet found for an earlier runnable binary, which is the wrong
trade against the no-claims posture.

### Option C — SU2 incompressible external-flow adapter

Loses on domain fit relative to the present evidence. SU2 has a
documented `INC_NAVIER_STOKES`/`INC_RANS` capability, clean
`history.csv` output with `DRAG`/`FORCE_X` fields, native `.su2`
mesh format with marker-driven boundary conditions, and packaged
binaries for Linux/macOS/Windows (research packet, SU2 citations).
Those are real maintainability advantages.

But:

- The maintained SU2 sources surfaced for this pass do not include
  a first-party ship/free-surface resistance tutorial comparable to
  OpenFOAM's DTCHull. Selecting SU2 first optimizes adapter
  maintainability over domain fidelity, and the project's stated
  audience (`docs/PRD.md:16`) is paddlers and independent builders
  who need "an honest hydrodynamic read on a hull" — domain fidelity
  is the higher-order good.
- SU2's `.su2`/CGNS mesh format and marker contract would push the
  first volume-mesh handoff toward a converter pass and a new
  marker-naming contract on top of RFC 0040's still-being-defined
  volume-mesh diagnostic. The OpenFOAM case structure consumes
  `constant/triSurface/*.stl` via `snappyHexMesh` directly (research
  packet, `snappyHexMesh` geometry guide citation), so the eventual
  mesh-handoff contract sits closer to the artifacts kayak-gen
  already produces.
- SU2 remains a legitimate later option. Choosing OpenFOAM first
  does not foreclose adding an SU2 profile in a separate later
  workflow, but only one solver adapter belongs in the first
  implementation slice per RFC 0041 non-goals
  (`docs/rfcs/0041-real-cfd-adapter-successor.md:65-66`).

### Option D — Defer real external solver, harden RFC 0040 first

Loses because it answers a question that is not on the panel's
table. RFC 0040 sequencing is already authoritative as a separate
roadmap track (`docs/ROADMAP.md:68`, Batch D), the
`panels/solver_readiness/claude/VOTE.md` sibling already adopted
that sequencing (readiness report → schema hardening → generated-body
hardening), and RFC 0041 explicitly says it "may advance only by
making missing evidence visible" — the solver-selection decision is
the missing evidence Option D refuses to produce. Voting Option D
here would leave RFC 0041 blocked indefinitely without changing the
RFC 0040 trajectory.

A narrower defense of Option D — "do not name a solver until
volume-mesh evidence lands" — is also already honored by Option A's
gate language: this vote names OpenFOAM v2512 *and* refuses to
enable a `succeeded` path until RFC 0040 readiness evidence exists.
Option A is therefore Option D plus the named-solver record RFC
0041 needs; Option D pure is strictly less informative for no extra
safety.

### Sub-variant rejected: vendor a different OpenFOAM line (Foundation v13)

Not selected because OpenFOAM.com v2512 (OpenCFD/ESI line) and
OpenFOAM Foundation v13 are distinct release lines with different
packaging, tutorial trees, and case drift surface (research packet,
v2512 release-notes citation). A generic "OpenFOAM" profile would
either pick one line implicitly or fail version-pinning. The vote
pins the OpenFOAM.com release line and the OpenFOAM-v2512 tag
explicitly.

## Implementation Gates That Must Remain In Force

These gates must not be relaxed by any workflow consuming this
decision:

1. **Solver-profile shape.** The new profile registration must fill
   the `ExternalSolverProfile` shape RFC 0041 names
   (`docs/rfcs/0041-real-cfd-adapter-successor.md:118-137`):
   `name="openfoam-v2512-interfoam-local"`,
   `adapter_name` (new local-command literal),
   `solver_name="openfoam"`,
   `solver_version_command=["openfoam", "--version"]` or the
   equivalent v2512 version probe documented at landing time,
   `required_mesh_readiness="cfd_ready"`,
   `required_mesh_profile="watertight_solid_resistance_v1"`,
   `case_template_version="openfoam-v2512-interfoam-dtchull-v1"`,
   `expected_raw_outputs=("log.interFoam",
   "postProcessing/forces/<time>/force.dat")`,
   `result_semantics="raw_unvalidated"`. Anything narrower or
   different requires a follow-up decision record, not a code edit.
2. **Watertight gate is mandatory.** `cfd prepare` must reject any
   package below `cfd_ready` for this profile *before* any solver
   command runs. Hand-edited readiness strings, synthetic
   closed-volume diagnostics, stale hashes, cross-body evidence,
   missing volume-mesh diagnostics, or failed self-intersection
   evidence must be rejected with the existing dispatch error codes
   (`evidence_profile_mismatch`, `cross_body`, `cross_hull`,
   `cross_tolerance`, `body_surface_mismatch`,
   `artifact_checksum_mismatch`) already present in
   `kayakgen/eval/cfd/jobs.py`. Adapter prepare may not invoke
   `snappyHexMesh` as the readiness authority by side effect; mesh
   readiness is decided upstream by RFC 0023/RFC 0040 evidence.
3. **Case template is project-owned.** The
   `openfoam-v2512-interfoam-dtchull-v1` template is informed by but
   not byte-vendored from the upstream tutorial. Files derived from
   the official tutorial must carry a comment recording the source
   URL, OpenFOAM-v2512 tag, and date. The legal review of OpenFOAM's
   GPL distribution conditions for any vendored fragment must occur
   before such fragments land.
4. **Parser scope is narrow.** First-pass parser parses only:
   solver version output (probe command), `log.interFoam` for a
   stable "finished" signal and run duration, and
   `postProcessing/forces/<time>/force.dat` for the raw total-force
   vector. The normalized `drag_force_n` is the dot product of the
   accepted total force with the negative job-velocity unit vector
   (so positive drag opposes motion under kayak-gen's stern-positive
   X convention). The parser must not derive `force_coeffs`,
   pressure/viscous splits, wave-resistance components, convergence
   verdicts, or calibrated drag from any of these files. Later
   `forceCoeffs` extension is permitted only after a fixture proves
   the file format and an explicit reference-area/direction metadata
   contract lands.
5. **Failure semantics.** Stable `error_kind` values must include
   at minimum: `solver_unavailable`, `version_check_failed`,
   `command_failed`, `timeout`, `missing_output`, `malformed_output`,
   `parser_mismatch`, `readiness_below_requirement`, plus the
   evidence-rejection codes already used by dispatch. Missing
   binaries and failed version checks produce `unavailable`, not
   `succeeded`.
6. **Bounded runtime.** Local runs must enforce a wall-clock
   timeout and a log-size cap. Defaults must be small enough that a
   timed-out misconfiguration cannot wedge a developer machine.
7. **Adapter stays at the boundary.** The adapter translates
   `CfdJobSpec` plus `MeshPackageManifest` into a case directory and
   raw outputs back into `CfdRunRecord`/raw-result records. It does
   not modify `Hull`, geometry models, mesh-package authoring,
   resistance, stability, or web/CLI route shapes beyond surfacing
   the new profile through the existing endpoints.
8. **CI strategy.** Required CI uses fake commands and checked-in
   fixture `force.dat`/`log.interFoam` files. Required tests cover:
   profile registration, deterministic prepare, readiness rejection
   for each rejection code, unavailable dependency,
   `command_failed`, `timeout`, `missing_output`, `malformed_output`,
   `parser_mismatch`, parser success from fixture files, run-record
   round trip, and forbidden claim promotion (no `raw_unvalidated →
   calibrated` upgrade). Optional installed-OpenFOAM smoke tests are
   skipped unless an explicit environment flag (e.g.,
   `KAYAKGEN_INSTALLED_SOLVER_SMOKE=1`) and a discovered OpenFOAM
   environment are both present.
9. **Platform note.** Linux (Ubuntu 24.04/22.04, openSUSE, RHEL
   variants per the v2512 packages page) is the primary supported
   platform. macOS and Windows are documented as optional Docker/WSL/
   source routes. Required CI is Linux-only; multi-platform CI is
   not in scope for this slice.
10. **No second adapter in this slice.** The first implementation
    workflow may not bundle an SU2 profile, hosted-worker runner,
    Docker execution, or asynchronous queue. Those are separate
    later decisions.

## No-Claims Language That Must Remain In Force

This decision does not relax any of the following, and consuming
workflows must preserve them where they already appear in
`docs/PRD.md`, `docs/USER_GUIDE.md`, `docs/ROADMAP.md`, the RFC
index, and `docs/DECISION_LOG.md`:

- "Real-solver output remains `raw_unvalidated`. It is not
  calibrated resistance, validated drag, final prediction, design
  fitness, Pareto-default scoring, or proof of seaworthiness"
  (`docs/ROADMAP.md:40-43`).
- "Open hull/deck STLs and ordinary generated mesh packages are
  inspection or open-surface candidate artifacts. Only the narrow
  fixture-backed handoff path can report `cfd_ready`; production
  volume meshing and ordinary watertight solver readiness remain
  roadmap work" (`docs/ROADMAP.md:44-47`).
- "Current CFD support is job/run/profile plumbing... It does not
  run OpenFOAM, SU2, hosted workers, Dockerized solvers, or any
  real CFD adapter" (`docs/PRD.md:42`) — must remain accurate until
  a real `succeeded` path lands behind RFC 0040 evidence.
- `cfd_ready` remains a *solver-input* readiness label only.
  Selecting OpenFOAM does not redefine `cfd_ready`, does not promote
  any open package to `cfd_ready`, and does not turn the
  fixture-backed `cfd_ready` path into production volume meshing.
- The OpenFOAM selection does not create a hosted CFD capability,
  Docker execution capability, browser-side meshing capability,
  multi-user job system, cancellation guarantees, or auth surface.
- This decision does not change resistance calibration, high-angle
  `GZ`, design-fitness scoring, Pareto-default scoring, browser
  parity, hosted-demo capability, or any wording about them.
- The selected solver is named; **no real `succeeded` run is
  authorized by this decision.** Implementation may land profile
  metadata, dependency detection, deterministic case rendering,
  parser fixtures, and `unavailable`/`failed` behavior, but the
  `succeeded` path must wait for RFC 0040 readiness evidence (or an
  accepted narrower workflow consuming landed RFC 0023 handoff
  evidence) for an OpenFOAM-readable volume-mesh handoff.

## Confidence

**High.**

Rationale: the recommended solver target is the one the research
packet's external evidence most strongly supports for kayak-relevant
free-surface hull resistance work, the gating posture is the
literal reading of RFC 0041's mesh-profile, case-template, parser,
CI, and `result_semantics` requirements, and every load-bearing
field in `SolverProfile`, `CfdJobSpec`, and `CfdRunRecord` is
already present in `kayakgen/eval/cfd/jobs.py` — so the decision is
structurally feasible without upstream model changes. The sibling
`panels/solver_readiness/claude/VOTE.md` posture (no production
mesher or solver chosen there; RFC 0041 is the proper home for
solver selection) is consistent with this vote. The main residual
uncertainty is whether the eventual production volume-mesh evidence
contract (RFC 0040) will name `watertight_solid_resistance_v1` or a
narrower successor profile; if RFC 0040 lands a narrower profile
name, the `required_mesh_profile` field on the OpenFOAM profile is
the only field this decision likely needs to revise, and that
revision is a single string change behind the same gate.

## Sources Reviewed

Local:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/USER_GUIDE.md` (CFD sections, surface asymmetry)
- `docs/ROADMAP.md` (No-Claims Rules, Dependency Tracks, Batch D, Batch E)
- `docs/DECISION_LOG.md`
- `docs/rfcs/README.md` (entries 0010, 0015, 0016, 0017, 0018, 0021,
  0022, 0023, 0026, 0028, 0040, 0041)
- `docs/rfcs/0041-real-cfd-adapter-successor.md` (full)
- `docs/design/kayak_hull_design_constraints.md` (§10 pipeline strategy)
- `docs/workflows/0018-deferred-backlog/QUEUE.md` (item "0025 CFD
  solver dispatch and jobs", item "0028 real CFD solver adapter")
- `docs/workflows/0050-decision-panel-research/SOURCES.md`
- `docs/workflows/0050-decision-panel-research/prompts/panel_vote.md`
- `striatum/0049-roadmap-reconciliation/final/FINAL_REVIEW.md` (read
  via patch summary)
- `striatum/0049-roadmap-reconciliation/integration/PATCH_SUMMARY.md`
- `striatum/0050-decision-panel-research/research/solver_path/RESEARCH.md`
- `striatum/0050-decision-panel-research/panels/solver_readiness/claude/VOTE.md`
  (sibling posture)
- `kayakgen/eval/cfd/jobs.py` (CfdAdapterName literal, SolverProfile,
  CfdJobSpec, CfdRunRecord, FIXTURE_CASE_TEMPLATE_VERSION,
  FIXTURE_RAW_OUTPUT — verified)
- `kayakgen/eval/cfd/` directory listing (verified: only
  `__init__.py`, `fixture_command.py`, `jobs.py`)

External claims (as cited in the research packet, accessed
2026-05-14; not re-fetched in this session):

- OpenFOAM.com current release page — OpenFOAM-v2512 released
  2025-12-22; install routes include Linux packages, Docker, WSL,
  source.
- OpenFOAM-v2512 release notes — GPL distribution; Ubuntu
  24.04/22.04, openSUSE, RHEL variants, Windows options, macOS
  source/Docker packages; repository moved to GitLab (release-line
  pinning required).
- OpenFOAM-v2512 DTCHull `Allrun` and `controlDict` — official
  free-surface hull tutorial uses `interFoam` with a `forces`
  function object on the hull patch under water density. Supports
  raw `force.dat` as first parser scope.
- OpenFOAM `snappyHexMesh` geometry guide — consumes triangulated
  surfaces from `constant/triSurface` (STL/STLB/OBJ/VTK), with
  surface regions becoming patches. Supports case rendering from
  mesh-package artifacts but not by itself readiness promotion.
- OpenFOAM `forceCoeffs` post-processing — total/pressure/viscous
  decomposition documented; supports a later parser extension after
  reference-area/direction metadata contract lands.
- SU2 GitHub releases — SU2 8.5.0 "Harrier" 2026-04-27; precompiled
  binaries for Linux/macOS/Windows; source build needs C/C++, Python
  3, Meson, Ninja.
- SU2 theory/output/mesh docs — `INC_NAVIER_STOKES`/`INC_RANS`
  available; `history.csv`/`history.dat` carries `DRAG`,
  `FORCE_X/Y/Z`, residuals; native `.su2`/CGNS mesh format with
  marker-driven boundaries.

## Sub-Agent Help

No sub-agents were spawned. Verification of code references and the
sibling panel posture was performed inline via direct read-only
inspection.
