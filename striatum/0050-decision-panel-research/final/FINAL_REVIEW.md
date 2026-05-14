---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept"
---

author: final-reviewer-claude-opus-4.7-001
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_c87d8b30619a47cbacf482b4e0125ac0
job: job_run_dc0a506896094745b380fd3ad2535d59_final_review
lease: lease_985eef0066e049a791cbb9c6015e0c61

# Final Review — Workflow 0050 Decision Panel Research

## Verdict

`accept`

Workflow 0050 lands eight design and sequencing decisions that are
research-backed, majority-derived, evidence-bound, and strictly
documentation-only. Each decision has a workflow-local research packet, three
independent panel votes (Claude / Codex / Gemini), an integrator-recorded
strict two-of-three majority, a matching row in `docs/DECISION_LOG.md`, and
matching `docs/ROADMAP.md` / `CHANGELOG.md` updates that preserve every
existing no-claims boundary. `git diff --check` is clean; runtime, test,
packaging, and `.striatum/` paths are unchanged.

## Coverage — Every Decision Has The Required Evidence Chain

`striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`
enumerates eight decisions. For each one I confirmed: a research packet
exists, three vote artifacts exist, the vote counts in the integrator's
table match what the vote files actually selected, the corresponding
`docs/DECISION_LOG.md` row exists, and the `docs/ROADMAP.md` posture is
consistent.

| Decision | Research packet | Claude vote | Codex vote | Gemini vote | Integrator tally | DECISION_LOG | ROADMAP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Solver-readiness evidence | `research/solver_readiness/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D003 (`docs/DECISION_LOG.md:36`) | `docs/ROADMAP.md:68-71`, `docs/ROADMAP.md:139-176` |
| CFD solver path | `research/solver_path/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D004 (`docs/DECISION_LOG.md:37`) | `docs/ROADMAP.md:72-75`, `docs/ROADMAP.md:191-217` |
| Resistance source acceptance | `research/resistance_sources/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D005 (`docs/DECISION_LOG.md:38`) | `docs/ROADMAP.md:76-78`, `docs/ROADMAP.md:218-245` |
| Calibrated resistance promotion | `research/calibrated_resistance/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D006 (`docs/DECISION_LOG.md:39`) | `docs/ROADMAP.md:79-81`, `docs/ROADMAP.md:244-245` |
| High-angle stability model | `research/high_angle_stability/RESEARCH.md` | Option B | Option B | Option B | 3-0 B | D007 (`docs/DECISION_LOG.md:40`) | `docs/ROADMAP.md:82-85`, `docs/ROADMAP.md:248-275` |
| Browser hosting posture | `research/browser_hosting/RESEARCH.md` | Option A | Option B | Option B | 2-1 B | D008 (`docs/DECISION_LOG.md:41`) | `docs/ROADMAP.md:86-89`, `docs/ROADMAP.md:155-167` |
| Desktop parity strategy | `research/desktop_parity/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D009 (`docs/DECISION_LOG.md:42`) | `docs/ROADMAP.md:90-91`, `docs/ROADMAP.md:128-141` |
| Sweep/search admissibility | `research/sweep_optimization/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D010 (`docs/DECISION_LOG.md:43`) | `docs/ROADMAP.md:92-95`, `docs/ROADMAP.md:277-296` |

Each vote artifact carries the schema-conforming `striatum.synthesis.v1`
front matter, names a panelist byline, cites the workflow's research packet,
cites at least one local product/RFC source, and cites independent external
references (Trame docs, Maxsurf, eCFR/IMO, OpenFOAM tutorials, Pyodide,
GitHub Pages, Fly.io, Trimesh, VTK, etc., dated 2026-05-14). No panel
lacked a two-of-three majority. The single 2-1 split (browser hosting) is
flagged in the integrator's `Dissent And Risks` section
(`integration/DECISION_RESULTS.md:181-188`) and is carried through as an
implementation gate rather than silently overridden.

## Majority Derivation — Integrator Tally Matches The Votes

Spot-checked all eight panels by reading vote-line text directly:

- `panels/solver_readiness/{claude,codex,gemini}/VOTE.md` — three Option A
  (readiness report first).
- `panels/solver_path/{claude,codex,gemini}/VOTE.md` — three Option A
  (OpenFOAM.com v2512 `interFoam`, watertight-gated).
- `panels/resistance_sources/{claude,codex,gemini}/VOTE.md` — three Option A
  (source-review packet first, no fixture promotion).
- `panels/calibrated_resistance/{claude,codex,gemini}/VOTE.md` — three
  Option A (preserve current no-promotion gate).
- `panels/high_angle_stability/{claude,codex,gemini}/VOTE.md` — three
  Option B (fixed-trim generated-body v1).
- `panels/browser_hosting/claude/VOTE.md` — Option A (defer until owner
  /budget exist); `codex/VOTE.md` and `gemini/VOTE.md` — Option B (narrow
  server-backed exploratory demo). Integrator records 2-1 Option B with
  Claude's dissent adopted as an implementation gate.
- `panels/desktop_parity/{claude,codex,gemini}/VOTE.md` — three Option A
  (web primary, desktop supporting).
- `panels/sweep_optimization/{claude,codex,gemini}/VOTE.md` — three Option A
  (conservative default whitelist, with objective registry as a
  prerequisite to optimizer work).

The tally table at `integration/DECISION_RESULTS.md:33-41` matches the vote
artifacts exactly. The strict two-of-three majority rule documented at
`integration/DECISION_RESULTS.md:18-24` is applied uniformly, and the
`Unresolved Items` block at `:212-228` truthfully reports zero
sub-majority panels.

## No-Claims Boundary — Decisions Preserve Existing Limits

For each at-risk product domain, the new text added by this workflow is
either a deferral, an exit criterion gated on named evidence, or a non-goal
— never a current capability claim:

- **Solver readiness / `cfd_ready` / production volume meshing.** D003
  preserves the narrow fixture-backed `watertight_solid_resistance_v1`
  evidence path; production readiness is a four-stage RFC 0040 ladder
  (`docs/ROADMAP.md:139-176`). Exit criteria forbid ordinary generated
  packages from clearing watertight-required solver-profile acceptance.
- **External CFD solver.** D004 authorizes only profile metadata,
  dependency detection, deterministic case rendering, unavailable/failed
  states, and fixture-parser coverage; no real OpenFOAM `succeeded` path is
  authorized until matching volume-mesh evidence exists
  (`integration/DECISION_RESULTS.md:74-77`; `docs/ROADMAP.md:191-217`). All
  real-solver output remains `raw_unvalidated`.
- **Resistance source promotion.** D005 keeps `rejected` as a review
  outcome and refuses to promote any current source
  (`integration/DECISION_RESULTS.md:82-94`; `docs/ROADMAP.md:218-245`).
  Edinburgh is named only as a permitted later validation-only candidate.
- **Calibrated resistance.** D006 preserves `uncalibrated_comparative` and
  defers calibrated wording to a later accepted-fit workflow with
  immutable model version, fit metrics, residuals, validity envelope, and
  `claim_allows_calibrated_prediction` gate
  (`integration/DECISION_RESULTS.md:96-110`).
- **High-angle stability.** D007 authorizes a model design only. Real
  generated-kayak `gz_m`, righting moment, and summary values remain
  unavailable until the v1 model lands behind RFC 0024 gates
  (`integration/DECISION_RESULTS.md:125-129`; `docs/ROADMAP.md:268-275`).
  Results when implemented are labeled unvalidated hydrostatic comparison
  curves, explicitly not safety, seaworthiness, capsize, design-fitness,
  or solver-readiness claims.
- **Browser hosting.** D008 explicitly does not deliver a public URL; a
  hosted-demo workflow is operationally gated on operator owner,
  budget/cap, deployment revision, environment, persistence, smoke, and
  cleanup evidence (`integration/DECISION_RESULTS.md:139-145`;
  `docs/ROADMAP.md:155-167`). Static/Pyodide and production hosted app
  paths require separate RFCs.
- **Desktop parity.** D009 rejects native rewrite and deprecation; parity
  is shared core/read models and claim copy, not pixel parity
  (`integration/DECISION_RESULTS.md:147-159`).
- **Sweep / search / optimization.** D010 keeps default Pareto objectives
  limited to `GM0_m`, `displacement_error_kg`, and `mesh_problem_count`;
  raw resistance is admissible only as explicit exploratory comparison;
  optimizer work waits for RFC 0009 reconciliation and objective metadata
  (`integration/DECISION_RESULTS.md:161-176`; `docs/ROADMAP.md:277-296`).

I grep-checked the at-risk vocabulary in `docs/ROADMAP.md` (`calibrated`,
`final prediction`, `design fitness`, `production volume`, `hosted CFD`,
`seaworthiness`). Every match is in a no-claims rule, an exit criterion,
or a non-goal. None promotes capability.

## Documentation-Only Boundary

`git status --short` shows exactly the file set the work packet permits
for a final-review job that touches only the workflow's `final/`
directory, plus the integration-lane files that pre-existed at claim time:

```
 M CHANGELOG.md
 M OPERATOR_REPORT.md
 M docs/DECISION_LOG.md
 M docs/ROADMAP.md
 M docs/workflows/0050-decision-panel-research/OPERATOR_REPORT.md
?? striatum/0050-decision-panel-research/
```

`git status --short -- kayakgen tests src pyproject.toml setup.py setup.cfg
.striatum`: empty. No runtime, test, packaging, or Striatum-state file was
modified by the integration lane, and this final-review lane writes only
this artifact under
`striatum/0050-decision-panel-research/final/FINAL_REVIEW.md`.

`git diff --check`: clean (no whitespace warnings).

Per-file content check:

- `CHANGELOG.md` — adds a single Unreleased entry under `### Added`
  describing workflow 0050 as documentation-only design records, with an
  explicit "no runtime/tests/solver/public URL/calibration/watertight
  readiness/high-angle stability output/desktop rewrite/optimization
  behavior/product capability changed" disclaimer. No removals; no
  capability claims.
- `docs/DECISION_LOG.md` — appends rows D003–D010 in the four-cell
  receipt format defined at `docs/DECISION_LOG.md:6-29`, each citing the
  relevant RFC and recording context, consequence, and revisit triggers.
  Decisions match `integration/DECISION_RESULTS.md` text.
- `docs/ROADMAP.md` — adds the `Workflow 0050 Decision Posture` section
  (`:62-95`); updates the Dependency Tracks table and the Future Striatum
  Batches text to reflect the decisions; preserves and reinforces every
  no-claims rule already in force.
- `docs/workflows/0050-decision-panel-research/OPERATOR_REPORT.md` and
  the root `OPERATOR_REPORT.md` — append timestamped operator checkpoints
  describing the run lifecycle, including the integration-lane override
  rationale. Operator bookkeeping only; no product-visible claim.
- `striatum/0050-decision-panel-research/**` — workflow-local artifacts
  only: eight research packets, twenty-four panel votes, the integration
  decision-results synthesis, the integration patch summary, and this
  final-review file.

The integration patch summary at
`striatum/0050-decision-panel-research/integration/PATCH_SUMMARY.md:53-62`
documents that publishing required `--allow-no-process-execution` because
the integration artifacts were created through Codex `apply_patch`, which
does not emit a Striatum `process_executions` row for the integrator's
exact artifact paths. The override rationale recorded is appropriate:
artifact created by Codex apply_patch; git status and file content
validate the artifact remains in the allowed integration scope. This
matches the workflow 0049 operator-pattern precedent and is consistent
with the workflow-local operator report.

## Lane / Artifact Consistency Cross-Checks

- Each vote artifact's `author:` byline names the lane and model
  (`panelist-claude-opus-4.7-*`, `panelist-codex-gpt-5.5-*`,
  `panelist-gemini-pro-3.1-*`). Bylines for the integrator
  (`decision-integrator-codex-gpt-5.5-003`) and this final reviewer
  (`final-reviewer-claude-opus-4.7-001`) come from the supplied work
  packet, not the job title.
- The integrator's `Implementation Burn-Down Queue`
  (`integration/DECISION_RESULTS.md:230-269`) sequences follow-up work
  consistently with the dependency tracks in `docs/ROADMAP.md:99-110`.
  Each follow-up item is gated on the same evidence the decision rows
  require.
- The integrator's `Shared Risks Preserved`
  (`integration/DECISION_RESULTS.md:189-211`) lists eight specific failure
  modes (e.g., misreading `cfd_ready` as solver success, vendoring
  OpenFOAM templates without license review, conflating validation and
  calibration fixtures). Each risk has a corresponding `revisit` trigger
  in the relevant decision-log row.

## Validation

- `git status --short`: only `CHANGELOG.md`, root `OPERATOR_REPORT.md`,
  `docs/DECISION_LOG.md`, `docs/ROADMAP.md`,
  `docs/workflows/0050-decision-panel-research/OPERATOR_REPORT.md`, and
  the untracked `striatum/0050-decision-panel-research/` directory.
- `git status --short -- kayakgen tests src pyproject.toml setup.py
  setup.cfg .striatum`: empty.
- `git diff --check`: clean.
- Vote-count cross-check: spot-read all twenty-four vote artifacts and
  confirmed each vote text matches the entry in the integrator's tally
  table (`integration/DECISION_RESULTS.md:33-41`).
- Forbidden-phrase grep across `docs/ROADMAP.md` (`calibrated`,
  `final prediction`, `design fitness`, `seaworthiness`,
  `production volume`, `hosted CFD`): every occurrence is in a no-claims
  rule, an exit criterion, a non-goal, or a deferred-batch description.
- Cross-checked decision rows D003–D010 against
  `integration/DECISION_RESULTS.md` accepted-decision sections and
  against the relevant RFCs (0040, 0041, 0042, 0024+0043, 0008+0030+0032,
  0034+0035, 0009+0013); each row's RFC citation, context, consequence,
  and revisit trigger is consistent with the panel votes and the existing
  RFC index narrative.
- No runtime tests were run: this packet, the reviewed integration, and
  this final-review artifact are documentation and workflow artifacts
  only.

## Findings

None blocking.

### Optional observations (non-blocking, informational)

- The integration lane used `--allow-no-process-execution` to publish its
  artifacts because `apply_patch` does not emit a Striatum
  `process_executions` row for the integrator's exact artifact paths. The
  override rationale is recorded at
  `striatum/0050-decision-panel-research/integration/PATCH_SUMMARY.md:53-62`
  and matches the workflow 0049 precedent
  (`striatum/0049-roadmap-reconciliation/final/FINAL_REVIEW.md` Optional
  observations section). If a future Striatum release tightens publish
  enforcement, this pattern is the natural surface to revisit.
- D008 is the only 2-1 split. Claude's dissent (defer until owner and
  budget exist) is preserved verbatim as an implementation gate in
  `integration/DECISION_RESULTS.md:181-188` and in the D008 consequence
  text. No public URL is delivered by this workflow, so the dissent's
  operational concerns are not yet live; the next hosted-demo workflow
  must satisfy them before any public URL is treated as accepted.
- The roadmap edits leave RFC 0009 still indexed as `proposed` in
  `docs/rfcs/README.md`. D010's revisit trigger and the Batch H text
  both name RFC 0009 status reconciliation as a prerequisite for
  optimizer work, so the stale label is intentionally addressed at the
  policy level rather than retroactively edited here. Reconciling the
  RFC index entry is appropriately deferred to a follow-up workflow.

## Summary

Accept. Workflow 0050 produces eight design and sequencing decisions that
are each research-backed (workflow-local research packet plus independent
external citations), majority-derived (strict two-of-three across Claude,
Codex, Gemini), evidence-bound (every consequence and exit criterion is
tied to named RFC, fixture, source-review, or operator evidence), and
documentation-only (no runtime, test, packaging, or `.striatum/` state
changes; `git diff --check` clean). The decision-log rows, roadmap
posture, and changelog entry preserve every existing no-claims boundary
on resistance, CFD, mesh readiness, stability, validity, hosting, parity,
and optimization.
