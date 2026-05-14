---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: decision-integrator-codex-gpt-5.5-003
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: decision_results
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_73eb6101fe054addab37f8f03c0b2bb5
job: job_run_dc0a506896094745b380fd3ad2535d59_integrate_decisions
lease: lease_0fc7ae5399e34b98b5b058d62afbb2f6
date: 2026-05-14

# Decision Results - Workflow 0050

## Integration Rule

Strict two-of-three majority was applied across the Claude, Codex, and Gemini
panel votes for each decision. A decision is accepted only when at least two
lanes selected materially the same option. No unresolved panel lacked a
majority.

This integration records design and sequencing decisions only. It does not
implement runtime behavior, tests, solver execution, public hosting,
calibration, watertight-readiness promotion, real high-angle stability output,
desktop rewrite, optimization, or product-capability changes.

## Vote Counts

| Decision | Claude | Codex | Gemini | Majority |
| --- | --- | --- | --- | --- |
| Solver-readiness evidence | Option A, with Option B as immediate follow-up | Option A | Option A | Option A, 3-0 |
| CFD solver path | Option A: OpenFOAM.com v2512 `interFoam`, watertight-gated | Option A | Option A | Option A, 3-0 |
| Resistance source acceptance | Option A, with Edinburgh validation as later gated follow-up | Option A | Option A | Option A, 3-0 |
| Calibrated resistance promotion | Option A, with Option B as future gate shape | Option A | Option A | Option A, 3-0 |
| High-angle stability model | Option B: fixed-trim generated-body v1 | Option B | Option B | Option B, 3-0 |
| Browser hosting posture | Option A: keep public hosting deferred, with Option B as future accepted shape | Option B: narrow server-backed demo | Option B | Option B, 2-1 |
| Desktop parity strategy | Option A: web workspace primary, desktop supporting | Option A | Option A | Option A, 3-0 |
| Sweep/search admissibility | Option A, with Option B registry prerequisite and C/D standing rules | Option A, with registry gate | Option A | Option A, 3-0 |

## Majority Decisions

### 1. Solver-Readiness Evidence

Accepted: Option A, readiness report first, with schema hardening as the
immediate follow-up.

The project will add an RFC 0040 readiness report explaining body, package,
profile, blocker, warning, evidence-ref, and hash status before changing
package readiness. Follow-up hardening should formalize volume-mesh diagnostic
schema, structured blocker/warning records, SHA-256 hash policy, boundary
patch/marker metadata, direct rejection-code tests, and generated-body matrix
coverage.

No production mesher, universal quality threshold table, or surface-only
solver profile is selected by this decision. Ordinary generated packages remain
below watertight solver-profile acceptance unless matching evidence exists.

### 2. CFD Solver Path

Accepted: Option A, OpenFOAM.com OpenFOAM-v2512 `interFoam`, watertight-gated.

The first external solver target is profile `openfoam-v2512-interfoam-local`,
required mesh profile `watertight_solid_resistance_v1`, readiness `cfd_ready`,
case-template version `openfoam-v2512-interfoam-dtchull-v1`, and a raw parser
limited initially to solver/version provenance, logs, and
`postProcessing/forces/**/force.dat`. Linux is the primary required platform;
macOS and Windows remain optional Docker/WSL/source routes. Required CI must
use fake commands and fixture files, not an installed solver binary.

This authorizes profile metadata, dependency detection, deterministic case
rendering, unavailable/failed states, and parser fixture coverage only. A real
OpenFOAM `succeeded` path remains blocked until matching RFC 0040/RFC 0023
OpenFOAM-readable volume-mesh evidence exists. All outputs remain
`raw_unvalidated`.

### 3. Resistance Source Acceptance

Accepted: Option A, source-review packet first with no current fixture
promotion.

Before any measured source can be promoted, the project needs a source-review
packet covering durable citation/locator, rights for source material and
derived rows, source type, measured quantity, units, hull envelope,
speed/Froude range, extraction metadata, uncertainty treatment, review verdict,
source-use mapping, and explicit non-promotion reasons. Runtime `SourceUse`
stays limited to the existing five values; `rejected` remains review-only.

No current source is promoted to `validation_fixture` or
`calibration_fixture`. Edinburgh remains a permitted later validation-only
candidate after extraction/attribution metadata, not a fixture selected by
this decision.

### 4. Calibrated Resistance Promotion

Accepted: Option A, preserve the current no-promotion gate.

Resistance output remains `uncalibrated_comparative`. No calibrated wording,
numeric fit threshold, calibrated comparative-ranking claim, default
optimization use, or design-fitness claim is authorized. A future accepted-fit
workflow may permit calibrated prediction only after a kayak-envelope
calibration fixture is accepted, an immutable concrete model version reaches
`accepted_fit`, metrics/residuals and validity envelope are persisted, the
evaluated hull/speed is inside the envelope, and
`claim_allows_calibrated_prediction` plus an envelope check passes.

The PRD's 25% over Fn 0.25-0.50 criterion remains an upper-bound roadmap
target, not the final acceptance threshold.

### 5. High-Angle Stability Model

Accepted: Option B, fixed-trim generated-body v1.

The first real generated-kayak high-angle `GZ` model should be a
fixed-upright-trim hydrostatic comparator over
`generated_hull_plus_deck_closed_body_v1`, only after RFC 0024 generated-body
diagnostics pass. The model design includes a default 0-90 degree grid by 5
degrees, caller-supplied strictly increasing grids echoed exactly, hull-fixed
passive CG, per-heel sinkage/displacement solving, closed waterline
clipping/capping diagnostics, per-point status/residual/iteration metadata,
grid-bounded summaries, and sealed-body/flooding warnings.

Real generated-kayak `gz_m`, righting moment, and summary metrics remain
unavailable until the model and tests land behind those gates. The v1 result,
when implemented, is an unvalidated hydrostatic comparison curve, not a
safety, seaworthiness, capsize, final design-fitness, or solver-readiness
claim.

### 6. Browser Hosting Posture

Accepted: Option B by 2-1 majority, narrow server-backed exploratory demo.

The project may pursue a public browser demo only by deploying the existing
Trame app through `kayakgen serve --host 0.0.0.0 --port 8080` or the repo
Docker path. A successor workflow must record operator owner, budget/cap,
deployment revision, environment variables, mounted volumes, persistence
caveats, hosted smoke evidence, cleanup policy, and no-production/no-SLA
wording before any public URL is treated as accepted.

Static/Pyodide and custom JavaScript demos are separate runtime/frontend
decisions. Production hosting, accounts, quotas, hosted worker queues, hosted
CFD, real solver execution, validated CFD, calibrated resistance, and final
design-fitness claims are not authorized.

### 7. Desktop Parity Strategy

Accepted: Option A, web workspace primary and desktop supporting.

The Trame web workspace is the primary UI composition and browser-acceptance
target for new user-facing work. The PyQt desktop GUI remains supported for
local launch, implemented sliders, 3D preview, STL export, compatibility, and
no-claim/status maintenance.

Parity means shared core data/read models, claim boundaries, and implemented
controls where surfaced. Pixel parity, widget parity, a full native desktop
rewrite, and desktop deprecation are not current goals. A thin desktop shell
may be considered later only with a separate recorded need and packaging gate.

### 8. Sweep/Search Admissibility

Accepted: Option A, conservative default whitelist, with objective registry
before optimizer work.

RFC 0009 should be reconciled as a landed/partial sweep-run-record slice rather
than treated as wholly proposed. Current default Pareto objectives remain
`GM0_m:max`, `displacement_error_kg:min`, and `mesh_problem_count:min` when
present. Raw analytical resistance is admissible only when explicitly requested
as exploratory comparison with accepted-use warnings. Raw CFD, advisory warning
counts, unavailable high-angle stability, and scalar `design_fitness` remain
inadmissible.

Search/optimizer work remains blocked until RFC 0009 status is reconciled and
objective metadata records metric label, unit, direction, source evaluator,
availability rule, claim-state requirement, accepted-use requirement, and role.

## Dissent And Risks

### Browser Hosting Dissent

Claude dissented from the browser-hosting majority and voted to keep public
hosting deferred until an owner, cost/capacity boundary, shutdown/redeploy
procedure, and hosted smoke are already in hand. The majority accepted the
narrow server-backed posture, but the dissenting risk is adopted as an
implementation gate: no public URL can be treated as landed without those
operational records.

### Shared Risks Preserved

- `cfd_ready` can be misread as solver success or validated output unless
  adjacent copy keeps it solver-input-only.
- OpenFOAM template work must not vendor upstream files verbatim without
  license review and must not use `snappyHexMesh` as hidden readiness
  authority.
- Resistance fixture promotion can overclaim if validation fixtures are treated
  as calibration fixtures or if source rights for article prose and dataset
  rows are conflated.
- Calibrated resistance wording will be over-read unless model version,
  envelope, metrics, and fallback warnings are visible wherever calibrated
  output eventually appears.
- Fixed-trim high-angle `GZ` is a comparator, not a full free-trim equilibrium
  model, and the sealed full-deck body can mislead if cockpit/downflooding
  limits matter.
- Browser hosting introduces cost, capacity, abuse, cleanup, and dependency
  update obligations that the current repo does not model.
- Web-primary UI strategy must not let the documented desktop GUI silently rot
  while it remains in the PRD and user guide.
- Optimizers will exploit any numeric metric, so objective metadata and claim
  gates must be machine-enforced before active search loops begin.

## Unresolved Items

No decision panel lacked a two-of-three majority. There are no unresolved
workflow 0050 decisions.

Several implementation dependencies remain blocked or evidence-gated:

- Real OpenFOAM `succeeded` runs wait for accepted OpenFOAM-readable
  volume-mesh evidence.
- Calibrated resistance waits for accepted source review, calibration fixture
  promotion, and an accepted-fit workflow.
- High-angle stability values wait for fixed-trim generated-body v1
  implementation and tests.
- Public browser hosting waits for operator, budget/cap, deployment, hosted
  smoke, and cleanup records.
- Optimizer/search work waits for RFC 0009 reconciliation and objective
  metadata.

## Implementation Burn-Down Queue

1. **Roadmap/status follow-through.** Keep `docs/DECISION_LOG.md`,
   `docs/ROADMAP.md`, `CHANGELOG.md`, and workflow reports synchronized with
   the accepted decisions. Reconcile `docs/rfcs/README.md` later where current
   write scope did not permit edits.
2. **RFC 0040 readiness report.** Add the explanatory read model over existing
   generated-body, self-intersection, volume-mesh, manifest, and dispatch
   evidence. No readiness promotion.
3. **Solver-readiness schema hardening.** Add structured blockers/warnings,
   explicit hash-algorithm fields, boundary patch/marker metadata, direct
   negative tests for dispatch rejection codes, and generated-body hardening
   cases.
4. **OpenFOAM adapter skeleton.** Add
   `openfoam-v2512-interfoam-local` metadata, dependency/version probing,
   deterministic case rendering, fake-command unavailable/failed flows, raw
   `force.dat` parser fixtures, log/timeout caps, and forbidden-claim tests.
   Do not enable real `succeeded` execution until mesh evidence gates pass.
5. **Resistance source review.** Add the RFC 0042 source-review packet
   template and source-use mapping tests, then apply it to one candidate
   without automatic promotion.
6. **Resistance validation-only follow-up.** If review metadata passes, run a
   separate workflow for Edinburgh validation fixture ingest with attribution,
   extraction, unit, uncertainty, checksum, and out-of-envelope warnings.
7. **Calibrated-resistance fit workflow.** Keep blocked until a kayak-envelope
   calibration fixture is accepted; then define immutable model versioning,
   source-aware metrics, residual artifacts, and envelope checks.
8. **High-angle stability v1.** Add per-heel metadata to `GZCurve`, implement
   fixed-trim generated-body clipping/capping and sinkage solve behind RFC 0024
   gates, and wire user surfaces only after unavailable/failure behavior is
   test-covered.
9. **Browser hosted demo operation.** Once an operator owner and budget/cap are
   recorded, deploy the existing Trame app or Docker path, run hosted smoke,
   document persistence/cleanup, and preserve all no-claims wording.
10. **UI cleanup with web-primary strategy.** Continue RFC 0036-0039 UI
    maintenance on the web workspace and shared read models; keep desktop
    launch/export/preview/no-claim copy supported without native rewrite.
11. **Sweep/search reconciliation.** Reconcile RFC 0009 status, decide the
    `pending` and `stl` deltas, add objective metadata, and keep optimizer work
    blocked until claim-gated admissibility is machine-enforced.

## Files Updated By Integration

- `docs/DECISION_LOG.md`
- `docs/ROADMAP.md`
- `CHANGELOG.md`
- `docs/workflows/0050-decision-panel-research/OPERATOR_REPORT.md`
- `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`
- `striatum/0050-decision-panel-research/integration/PATCH_SUMMARY.md`
