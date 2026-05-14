# Roadmap

Updated: 2026-05-14

This roadmap is the contributor-facing reconciliation point for the current
RFC index, the older deferred workflow queue, and the workflow 0048 successor
RFC backlog. The RFC index remains authoritative for RFC status. The PRD and
user guide remain authoritative for current user-facing behavior. This file
answers a narrower planning question: what work is still outstanding, what is
blocked, and how should future Striatum implementation batches be cut?

## Status Vocabulary

- `ready-now`: dependencies and scope are clear enough for a focused Striatum
  workflow.
- `partial`: a safe slice landed, but remaining acceptance criteria or parity
  work are still open.
- `evidence-gated`: a workflow may prepare structure or review packets, but
  product promotion requires named evidence such as source rights, diagnostic
  hashes, fixture manifests, or accepted fit records.
- `blocked`: a design, source, solver, operations, or infrastructure decision
  is required before implementation should start.
- `background`: useful context retained for traceability, not the current
  implementation target.
- `superseded`: replaced by a successor RFC or workflow path; stale jobs should
  not be claimed.
- `completed-history`: landed work retained only to explain how the roadmap got
  here.

Queue dispositions use the same language, with `still-open` meaning an old
queue item has residual work mapped to a current track below.

## No-Claims Rules

Future roadmap and workflow text must preserve these boundaries unless a later
accepted RFC and implementation artifact provide evidence:

- Resistance output is `uncalibrated_comparative`, a raw comparative filter,
  not a calibrated model, final prediction, design-fitness score, or default
  optimization objective.
- CFD output is local dispatch state, `raw_unvalidated` output, `fixture_only`
  records, or explicit unavailable/failed state. There is no accepted
  OpenFOAM, SU2, Docker, hosted-worker, or other real solver success path.
- Open hull/deck STLs and ordinary generated mesh packages are inspection or
  open-surface candidate artifacts. Only the narrow fixture-backed handoff path
  can report `cfd_ready`; production volume meshing and ordinary watertight
  solver readiness remain roadmap work.
- Generated closed bodies are evaluation evidence, not production solver input,
  unless matching body diagnostics, self-intersection evidence, volume-mesh
  evidence, hashes, artifacts, and solver profile gates all pass.
- High-angle `GZ`, `GZ_max`, range-of-positive-stability, capsize-range, and
  secondary-stability metrics are unavailable for real generated kayaks until
  a generated-body evidence gate and accepted heeled integration model land.
- Class validity, advisory badges, and design warnings are not proof of
  seaworthiness, safety, calibrated performance, final design fitness, or
  solver readiness.
- The web frontend is local/browser-capable with runbook coverage, not a
  completed public hosted demo, full dashboard parity, hosted CFD system, or
  desktop parity rewrite.

## Dependency Tracks

| Track | Current state | Roadmap status | Next work |
| --- | --- | --- | --- |
| Docs, status, and claim hygiene | PRD, user guide, RFC index, changelog, and this roadmap describe current limits. | `ready-now` | Keep these files synchronized after each RFC/workflow landing. Reconcile stale RFC labels before using them as implementation authority. |
| UI and web maintenance | RFCs 0033-0035 landed conservative UI slices; RFCs 0036-0039 are proposed workflow 0048 successors. | `ready-now` | Land small UI cleanup batches: Trame same-seed proof/removal, export-row schema consolidation, disabled mesh-package label polish, and web snapshot/CFD alias schema unification. RFC 0037 should precede RFC 0038 or be bundled with separate gates. |
| Browser hosting and parity | RFC 0008 is partial; RFC 0032 landed local browser acceptance and hosted-demo docs; RFC 0030 remains the broader hosted/browser acceptance proposal. | `partial` / `blocked` | Split hosted public demo operation, console-clean/Lighthouse maintenance, richer plot/dashboard parity, and any desktop parity rewrite into independent workflows. Do not bundle with solver or calibration work. |
| Geometry and mesh evidence | RFCs 0021-0023 and 0028 landed conservative diagnostics, generated-body, fixture-handoff, and plumb-stem safe slices. RFC 0040 is the current gated roadmap above them. | `partial` / `evidence-gated` | Treat RFC 0040 as a sequence: readiness report, generated-body hardening, volume-mesh diagnostic contract, package gates, dispatch gates. Do not schedule it as one "make generated packages `cfd_ready`" feature. |
| CFD dispatch and real adapter | RFC 0015 local dispatch, RFC 0018 local web routes, and RFC 0026 fixture-local-command have landed. RFC 0017 is background; RFC 0041 is the current real-adapter successor. | `blocked` | Make a solver-selection decision, choose a mesh profile, define case-template and raw-output parser gates, then implement one external adapter with required CI not depending on installed solver binaries. Outputs remain `raw_unvalidated`. |
| Resistance evidence and calibration | RFC 0005 landed only as raw filter; RFC 0025/0027 landed claim gates. RFC 0012 remains proposed; RFC 0019 is background; RFC 0042 is the current evidence successor. | `evidence-gated` | Review candidate measured sources, rights, extraction, units, hull envelope, and source-use mapping. Promote validation or calibration fixtures only with accepted review metadata. Fitting and calibrated wording require a later accepted-fit workflow. |
| Stability and high-angle `GZ` | RFC 0011 landed load cases; RFC 0014 landed upright trim slice; RFC 0024 landed structured unavailable/fixture-only handoff. RFC 0020 is background; RFC 0043 is the current successor. | `blocked` | Draft the heeled-integration design gate: accepted body profile, heel grid, trim policy, CG convention, waterline clipping, residuals, deck/flooding assumptions, and warnings. Real kayak curves remain unavailable until then. |
| Sweeps, comparison, and search | `kayakgen sweep` and `compare` are user-facing, while RFC 0009 is still indexed as proposed and RFC 0013 has a landed report/web slice. | `partial` | Reconcile RFC 0009 status against delivered sweep behavior before optimizer work. Defer generative optimization and Pareto-default scoring until objective provenance, resistance claim gates, and stability availability are clearer. |

## Future Striatum Batches

### Batch A: Roadmap And Status Maintenance

Status: `ready-now`

Scope: keep `docs/PRD.md`, `docs/USER_GUIDE.md`, `docs/rfcs/README.md`,
`docs/ROADMAP.md`, `CHANGELOG.md`, and workflow-local reports aligned after
each landing. This includes correcting stale RFC status labels and moving old
queue entries to completed, background, superseded, or still-open disposition.

Exit criteria: docs distinguish delivered behavior from roadmap deferrals and
do not claim calibrated resistance, real CFD success, production volume
meshing, final prediction, design fitness, or real high-angle stability.

### Batch B: UI Cleanup Successors

Status: `ready-now`

Scope: RFCs 0036-0039.

- RFC 0036: prove the Trame same-seed preset listener path through browser
  automation or remove it with equivalent regression coverage.
- RFC 0037: collapse export-row guidance to canonical `subtitle` ownership.
- RFC 0038: polish disabled Mesh package export copy after or with RFC 0037.
- RFC 0039: unify web snapshot keys and CFD alias metadata while preserving
  public REST payload shapes.

Exit criteria: behavior, export availability, backend capability, and no-claim
copy remain unchanged except for explicitly accepted visible copy polish.

### Batch C: Browser Hosting And Parity

Status: `partial` / `blocked`

Scope: RFC 0008, RFC 0030, RFC 0032, and the unresolved UI parity portions of
RFC 0033.

Work should be split into small workflows:

- public hosted demo operation using the documented local command/Docker path;
- console-clean and Lighthouse acceptance upkeep;
- full plot/dashboard parity beyond compact analysis;
- desktop parity rewrite or embedding work, only if still desired;
- mobile/view-only acceptance only after the desktop browser path is stable.

Exit criteria: each workflow states exactly which browser or parity criterion
it closes and does not imply hosted CFD workers, web-side mesh-package
authoring, real solvers, or calibrated outputs.

### Batch D: Geometry Evidence And Solver Readiness

Status: `evidence-gated`

Scope: RFC 0040 over RFCs 0010, 0016, 0021, 0022, 0023, 0028, and related
partials from RFCs 0004/0006.

Recommended order:

1. Add a closed-volume solver-readiness report that explains evidence and
   blocker reasons without changing package readiness.
2. Harden generated-body diagnostics across default, plumb, mixed-rake,
   `beam_wl_m != beam_oa_m`, draft, `Cp`, and `Cm` cases.
3. Define volume-mesh diagnostics with body refs, diagnostic hashes, mesher
   metadata, quality summaries, artifact checksums, warnings, and blockers.
4. Gate mesh-package handoff and dispatch preparation on matching evidence.

Exit criteria: ordinary generated packages still remain below
watertight-required solver-profile acceptance unless matching evidence exists.
Any fixture evidence is labeled as fixture evidence, not production meshing.

### Batch E: Real CFD Adapter Decision And Implementation

Status: `blocked`

Scope: RFC 0041, with RFC 0017 as background and RFC 0026 as the landed
fixture boundary.

Prerequisites:

- one solver target selected by decision record;
- explicit installation/version/platform notes;
- chosen mesh profile and readiness gate;
- deterministic case-template version;
- expected raw outputs and parser scope;
- required tests that do not require the solver binary.

Exit criteria: where dependencies are installed, one local external adapter can
prepare, run, fail, and collect raw records truthfully. Missing dependencies
remain `unavailable`, command/parser failures remain `failed`, and successful
records remain `raw_unvalidated`.

### Batch F: Resistance Source Evidence

Status: `evidence-gated`

Scope: RFC 0042, with RFC 0019 as background and RFC 0027 as the claim-gate
authority.

Recommended order:

1. Add a source-review packet/checklist for rights, extraction, measured
   quantity, units, hull envelope, speed/Froude range, uncertainty, and verdict.
2. Apply it to one candidate source without promoting it unless evidence is
   complete.
3. Add source-use mapping checks so `rejected` stays a review outcome, not a
   runtime fixture source-use value.
4. Add validation fixture ingest only if rights and extraction metadata pass.
5. Add calibration fixture ingest only after a kayak-envelope measured source
   is accepted.
6. Defer fitting and calibrated-output wording to a separate accepted-fit
   workflow.

Exit criteria: current curves keep `uncalibrated_comparative` warnings until a
named model version has accepted fit evidence, calibration fixture IDs, fit
metrics, and a validity envelope that contains the evaluated hull and speed.

### Batch G: High-Angle Stability Design Gate

Status: `blocked`

Scope: RFC 0043, preserving RFC 0024's structured unavailable handoff.

Prerequisites:

- generated-body evidence accepted for stability use;
- heeled-volume integration design accepted;
- heel grid, trim policy, CG convention, waterline clipping, residuals,
  convergence warnings, and deck/flooding assumptions recorded.

Exit criteria: until all gates pass, CLI, sweep, comparison, desktop, and web
surfaces continue to show unavailable results rather than numeric high-angle
`GZ` or secondary-stability summaries. Fixture-only math tests cannot satisfy
user-facing stability claims or ranking.

### Batch H: Sweep, Comparison, And Optimization

Status: `partial`

Scope: RFC 0009, RFC 0013, future search/optimization RFCs.

First step: reconcile RFC 0009 with the current user-facing sweep command and
run-record behavior. Then decide what remains open before any optimizer work:
candidate provenance, objective metadata, warnings, validity records, and
whether resistance/stability metrics are admissible for ranking.

Exit criteria: candidate comparison can use only metrics whose claim state and
availability are explicit. Optimization must not silently treat raw resistance,
raw CFD, advisory validity, or unavailable stability as final design fitness.

## Current RFC Disposition

| RFCs | Current disposition | Roadmap status |
| --- | --- | --- |
| 0004, 0028 | Historical plumb-bow and current plumb-stem closure semantics are partial safe slices. Independent `stern_rake` and generated closed-body cap/ring semantics exist, but open STLs remain inspection surfaces and broader solver readiness maps to RFC 0040. | `partial` |
| 0005, 0012, 0019, 0025, 0027, 0042 | Raw analytical resistance landed; source registries and claim gates exist; calibration fixture promotion is now RFC 0042. | `evidence-gated` |
| 0006, 0029, 0031 | Canonical constraints, presets, validity metadata, and surfacing slices landed. RFC 0029 is background superseded by RFC 0031. Future shape parameters and any remaining desktop/manual surfacing stay open only as focused follow-ups. | `partial` / `background` |
| 0008, 0030, 0032, 0033 | Local Trame shell, compact analysis, comparison loading, local browser acceptance, hosted-demo docs, and workspace safe slices landed. Public hosted operation, richer dashboards, and desktop parity rewrite remain separate work. | `partial` |
| 0009, 0013 | Comparison report/web slice landed; sweep behavior is user-facing but RFC 0009 is still indexed proposed. Reconcile status before search/optimization. | `partial` |
| 0011, 0014, 0020, 0024, 0043 | Load cases and upright trim landed; high-angle `GZ` is structured unavailable or fixture-only. RFC 0043 supersedes remaining RFC 0020 implementation scope. | `blocked` |
| 0015, 0017, 0018, 0026, 0041 | Local dispatch, local web routes, unavailable/mock states, and fixture-local-command landed. RFC 0017 is background; RFC 0041 is the real external adapter successor. | `blocked` |
| 0010, 0016, 0021, 0022, 0023, 0040 | Mesh packages, synthetic diagnostics, self-intersection checks, generated body construction, and fixture handoff landed. RFC 0040 is the evidence roadmap for production solver readiness. | `evidence-gated` |
| 0034, 0035 | Workspace follow-up and UI cleanup safe slices landed. Residual workflow 0047 final-review findings became RFCs 0036-0039. | `completed-history` |
| 0036, 0037, 0038, 0039 | Workflow 0048 proposed UI successors; they are small maintenance scopes with no backend or capability changes. | `ready-now` |

## Deferred Queue Reconciliation

`docs/workflows/0018-deferred-backlog/QUEUE.md` is historical. It still frames
0026-0031 as the active queue, but current planning runs through RFC 0043.
Use this table instead of claiming the stale queue prompts directly.

| Old queue item | Disposition | Current mapping |
| --- | --- | --- |
| 0019 legacy RFC partial closure | `completed-history` with residual `still-open` work | Safe package/core slices landed. Later RFC 0028 addressed independent rake and generated closed-body plumb semantics. Production solver readiness maps to RFC 0040. |
| 0020 browser acceptance and demo | `partial` / `still-open` | Headless, browser smoke, local browser acceptance, and hosted-demo docs advanced. Public hosted operation, console-clean/Lighthouse upkeep, full plot/dashboard parity, and desktop parity rewrite stay in browser/parity batches. |
| 0021 web plots and comparison UI | `completed-history` | Compact web analysis/comparison and report loading landed. Richer dashboard work is new UI/browser scope. |
| 0022 generalized trim and GZ stability | `partial` / `still-open` | Load components and upright trim landed. Real high-angle stability maps to RFC 0043. |
| 0023 resistance calibration dataset vetting | `background` | Pacific-canoe metadata remains validation-only source context. Fixture promotion maps to RFC 0042. |
| 0024 watertight solid mesh profile | `partial` / `still-open` | Blocked profile and fixture-backed handoff exist. Production volume meshing and real solver-readiness promotion map to RFC 0040. |
| 0025 CFD solver dispatch and jobs | `partial` / `still-open` | Local job/profile/run plumbing landed. Real solver execution, Docker/container execution, hosted workers, and validated outputs map to RFC 0041 and later validation/calibration work. |
| 0029 web CFD job routes history entry | `partial` / `still-open` | Local `/api/cfd/*` routes and panel landed. Hosted queues, auth, cancellation guarantees, web-side mesh-package creation, and real solver success remain future scope. |
| 0026 docs roadmap and user guide | `completed-history` | User-facing docs reconciliation landed. Workflow 0049 replaces the stale queue with this roadmap. |
| 0027 closed-volume geometry contract | `superseded` as a queue prompt, with residual `still-open` work | Safe slices landed across RFCs 0021-0023 and 0028. Future production solver-readiness evidence maps to RFC 0040. |
| 0028 real CFD solver adapter | `superseded` / `still-open` | The fixture adapter landed under RFC 0026. External solver work now maps to RFC 0041 and remains blocked on solver/profile decisions. |
| 0029 web CFD job routes queued section | `completed-history` for local route slice, residual `still-open` work | Duplicate of the history entry. Keep the local-web-dispatch summary and map hosted/real-solver web concerns to browser parity and RFC 0041. |
| 0030 resistance calibration fixture | `superseded` / `evidence-gated` | RFC 0042 narrows this to source review and fixture promotion before any calibration or fit workflow. |
| 0031 high-angle `GZ` and secondary stability | `superseded` / `blocked` | RFC 0024 landed structured unavailable handoff. RFC 0043 is the successor design gate for any real generated-kayak high-angle `GZ`. |

## Scheduling Guidance

- Start with `ready-now` UI cleanup and docs/status maintenance when the goal is
  fast backlog burn-down.
- Do not parallelize two batches that write the same UI schema/copy surface
  unless one workflow explicitly owns integration; RFC 0037 and RFC 0038 are
  the known dependency pair.
- Do not start real solver work before the solver-selection and mesh-profile
  gates are written down. If the selected solver needs watertight input, it
  must consume RFC 0040/RFC 0023 evidence instead of creating readiness itself.
- Do not start high-angle `GZ` implementation before the heeled integration
  design is accepted. Fixture-only numerical tests may precede product output
  only if every artifact is labeled `fixture_only`.
- Do not start calibrated resistance fitting before at least one kayak-envelope
  measured source is accepted as a calibration fixture with rights, extraction,
  units, fit metadata, and validity envelope.
- Treat optimization/search as a later consumer of evidence, not as a shortcut
  around missing calibration, stability, or solver-readiness decisions.
