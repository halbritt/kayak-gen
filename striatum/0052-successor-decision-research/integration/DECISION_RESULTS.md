---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: decision-integrator-codex-gpt-5.5-001
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: decision_results
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_540a4f0e7c78480ea19bc9fcd25e5789
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_integrate_decisions
lease: lease_c05eb640383f46ce8f052d3c8de18792
date: 2026-05-14

# Decision Results - Workflow 0052

## Integration Rule

Strict two-of-three majority was applied across the Claude, Codex, and Gemini
panel votes for each workflow 0052 decision. A decision is accepted only when
at least two lanes selected materially the same option.

This integration records design and sequencing decisions only. It does not
implement runtime behavior, tests, solver execution, public hosting,
calibration, watertight-readiness promotion, high-angle product output,
desktop rewrite, optimizer/search behavior, or product-capability changes.

## Vote Counts

| Decision | Claude | Codex | Gemini | Majority |
| --- | --- | --- | --- | --- |
| High-angle product surface | Option A, staged explicit surfacing | Option A, staged explicit surfacing | Option A, staged explicit surfacing | Option A, 3-0 |
| OpenFOAM success gate | Option A, full evidence gate before success | Option A, full evidence gate before success | Option A, full evidence gate before success | Option A, 3-0 |
| Public demo operations | Option A, defer public operation until operator gates | Option A, defer public operation until operator gates | Option A, defer public operation until operator gates | Option A, 3-0 |
| Resistance source candidate | Option A, Edinburgh validation-only full packet | Option A, Edinburgh validation-only full packet | Option A, Edinburgh validation-only full packet | Option A, 3-0 |
| Sweep next delta | Option A, `pending` candidate state next | Option A, `pending` candidate state next | Option A, `pending` candidate state next | Option A, 3-0 |
| Volume-mesher path | Option A, OpenFOAM-v2512 `snappyHexMesh` evidence harness | Option A, OpenFOAM-v2512 `snappyHexMesh` evidence harness | Option A, OpenFOAM-v2512 `snappyHexMesh` evidence harness | Option A, 3-0 |

## Majority Decisions

### 1. High-Angle Product Surface

Accepted: Option A, staged explicit surfacing.

Fixed-trim generated-body v1 high-angle `GZ` may be surfaced only as an
explicit, provenance-rich hydrostatic comparison artifact. The accepted order
is CLI JSON first, then opt-in sweep artifacts, then display-only comparison
and web read models, with desktop kept minimal/supporting.

Default `kayakgen stability`, default sweep summaries, default comparison
frontiers, and default Pareto objectives remain unchanged. Any surfaced values
must carry generated-body and per-heel gate evidence, body/load/trim
provenance, `result_semantics="unvalidated_hydrostatic_comparison"`,
`summary_semantics="grid_bounded"`, fixed-trim and sealed-body warnings, and
no safety, seaworthiness, capsize, ISO, validation, solver-readiness, final
prediction, or design-fitness wording.

### 2. OpenFOAM Success Gate

Accepted: Option A, full evidence gate before success.

`openfoam-v2512-interfoam-local` remains unable to return `succeeded` until one
run record binds all of the following: accepted OpenFOAM-readable
`watertight_solid_resistance_v1` / `cfd_ready` volume-mesh evidence,
OpenFOAM.com v2512 `interFoam` provenance beyond `$WM_PROJECT_VERSION`, a real
deterministic v2512 case smoke, a v2512-correct `force.dat` parser, and
raw-unvalidated no-claims payloads.

Until then, parser-readable fake output continues to produce
`solver_success_blocked`. After the gate opens, `succeeded` means only that
the selected local solver executed and the adapter parsed raw artifacts. It is
not validation, calibration, final prediction, design fitness, or solver
readiness for other hulls.

### 3. Public Demo Operations

Accepted: Option A, defer public operation until operator gates are recorded.

Workflow 0052 does not accept a public hosted browser demo because the current
repo records no operator owner, budget/cap, deployed revision, hosted smoke,
bounded persistence policy, cleanup receipt, or public no-claims wording.

Once those gates exist, the authorized hosted shape is one fixed-size managed
container running the existing `kayakgen serve --host 0.0.0.0 --port 8080` or
repo Docker path, with autoscaling, databases, queues, hosted workers, and
persistent volumes off unless explicitly budgeted and cleaned up. Static or
Pyodide hosting, production hosting, accounts, quotas, collaboration features,
and hosted CFD require separate decisions.

### 4. Resistance Source Candidate

Accepted: Option A, Edinburgh full source-review packet capped at
validation-only.

The University of Edinburgh DataShare dataset "Hydrodynamics of Three Slender
Models Resembling Pacific Canoe Hulls" (DOI `10.7488/ds/3785`) is the first
measured resistance source selected for a full RFC 0042 source-review packet.
The maximum positive outcome is `validation_fixture`; `calibration_fixture`
promotion is forbidden for this source because the hull class and test purpose
remain outside the sea-kayak/surfski calibration envelope.

The follow-up packet must complete deterministic extraction, unit normalization,
Froude basis, uncertainty notes, attribution, source-file checksums, fixture
metadata, and accepted-use warnings. Tzabiras, Gomes, Sea Kayaker,
Lazauskas/Winters/Tuck, and MDPI sources remain permission, recovery,
citation-only, or later validation candidates. Current resistance output stays
`uncalibrated_comparative`.

### 5. Sweep Next Delta

Accepted: Option A, `pending` candidate state next.

The next RFC 0009 delta is candidate lifecycle: add `pending` to
`CandidateStatus`, add additive `pending_count` to `SweepRunRecord`, write
planned candidate records before evaluation begins, define transition and
resume policy explicitly, and keep pending candidates visible but
frontier-ineligible in `summary.csv`, `run.json`, and comparison reports.

Sweep-side STL artifacts, active optimizer/search loops, broad metadata
redesign, parallel worker queues, calibrated resistance, real OpenFOAM
`succeeded`, high-angle product surfacing, public browser hosting, and new
design-fitness semantics remain out of scope for the pending workflow.

### 6. Volume-Mesher Path

Accepted: Option A, OpenFOAM-v2512 `snappyHexMesh` evidence harness.

OpenFOAM.com OpenFOAM-v2512 `snappyHexMesh` is selected as the first production
volume-mesher candidate for RFC 0040 follow-up work, under a profile such as
`openfoam-v2512-snappyhexmesh-watertight-v1`. The first slice is an evidence
harness over `generated_hull_plus_deck_closed_body_v1`, not readiness
promotion.

The harness should render deterministic OpenFOAM meshing cases, optionally run
installed `surfaceFeatureExtract`, `blockMesh`, `snappyHexMesh -overwrite`, and
`checkMesh -allTopology -allGeometry -meshQuality` behind an explicit
environment flag, and bind `VolumeMeshDiagnostic` evidence for body refs,
diagnostic hashes, OpenFOAM.com v2512 provenance, patch metadata, quality
summaries, logs, command metadata, output artifacts, and SHA-256 checksums.
Required CI remains solver-free through fake commands and fixtures.

Ordinary generated packages remain below watertight solver-profile acceptance.
A passing `snappyHexMesh` package is OpenFOAM-readable volume-mesh evidence for
one profile, not validated CFD, calibrated resistance, final prediction, design
fitness, hosted worker readiness, or real solver success.

## Dissent And Risks

No workflow 0052 panel had a minority vote. Each decision reached a 3-0
majority.

Shared risks preserved by the panel artifacts:

- High-angle `GZ` values can be misread as safety, seaworthiness, capsize, or
  validation results unless opt-in defaults and copy tests stay strict.
- The OpenFOAM `force.dat` parser must be corrected to the v2512 schema before
  any success state opens.
- A passing `snappyHexMesh` or `checkMesh` run can be over-read as validated
  CFD unless the evidence-harness wording stays separate from solver success.
- Edinburgh DataShare is useful validation infrastructure, but its hulls are
  outside the kayak/surfski calibration envelope.
- Public demo operation creates cost, uptime, abuse, persistence, dependency,
  and cleanup obligations that the current repo does not yet own.
- `pending` records must not carry fitness, artifact, or partial-success
  implications before evaluation actually runs.

## Unresolved Items

No decision panel lacked a two-of-three majority. There are no unresolved
workflow 0052 decisions.

Implementation dependencies that remain blocked or evidence-gated:

- Real OpenFOAM `succeeded` runs wait for OpenFOAM-readable volume-mesh
  evidence, v2512 provenance, deterministic smoke, parser correction, and
  raw-unvalidated payload gates.
- Calibrated resistance waits for an in-envelope measured kayak/surfski source
  and a later accepted-fit workflow.
- High-angle product output waits for an explicit staged surfacing workflow and
  must remain opt-in and no-claims bounded.
- Public browser hosting waits for owner, budget/cap, deployment, hosted
  smoke, persistence, cleanup, and public wording evidence.
- Active optimizer/search waits for pending lifecycle plus a later search-spec
  workflow.

## Implementation Burn-Down Queue

1. **Sweep pending lifecycle.** Add `pending` records and counts, explicit
   transition/resume policy, backward compatibility for older run records, and
   comparison visibility with frontier ineligibility. Do not bundle STLs or
   optimizer/search.
2. **Edinburgh validation-only packet.** Complete the RFC 0042 packet for
   Edinburgh with source checksums, extraction, units, Froude basis,
   uncertainty, fixture metadata, accepted-use warnings, and calibration
   blockers.
3. **High-angle CLI artifact surface.** Add the first explicit CLI JSON surface
   for generated-body v1 only after computed gate evidence exists; defaults and
   objective/frontier behavior stay unchanged.
4. **OpenFOAM-v2512 `snappyHexMesh` harness.** Implement the RFC 0040 evidence
   harness and fixture/fake-command tests for deterministic case rendering,
   `checkMesh`, patch metadata, quality summaries, artifact hashes, and
   dispatch rejection.
5. **OpenFOAM success-gate hardening.** Correct the v2512 `force.dat` parser
   and add provenance/case-smoke gates, while keeping `solver_success_blocked`
   until matching OpenFOAM-readable volume-mesh evidence exists.
6. **Public demo operations.** Proceed only after an operator supplies owner,
   budget/cap, provider, deployment, hosted smoke, persistence, cleanup, and
   public no-claims evidence.
7. **Sweep-side STL artifacts.** Schedule after `pending` lands, with explicit
   `evaluators.stl: true`, artifact sidecars, checksums, disk-budget warnings,
   and open-inspection-surface wording.
8. **Search/optimizer design.** Keep blocked until lifecycle, objective
   metadata snapshots, algorithm/version/seed/budget/bounds/constraints, and
   forbidden-objective handling are accepted.

Carryover from workflow 0051 remains visible: the stale web CFD status-copy
cleanup is a small UI successor item, and the RFC 0009 reconciliation record is
now reinforced by D016's `pending` decision plus the existing D010
admissibility row.
