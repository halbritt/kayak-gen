---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept"
---

author: operator [self-declared: operator-0052-final-review]
date: 2026-05-14
run: run_439eb6df3d1e4f12940bedad37c9a4ac
session: sess_2bcf287463e1466694b90fd432ff121e
job: job_run_439eb6df3d1e4f12940bedad37c9a4ac_final_review
lease: lease_c30750a0b6634466907c3fef9c201215

# Final Review — Workflow 0052 Successor Decision Research

## Verdict

`accept`

Workflow 0052 lands six design and sequencing decisions (D011–D016) that are
research-backed, majority-derived, evidence-bound, and strictly
documentation-only. Each decision has a workflow-local research packet, three
independent panel votes (Claude / Codex / Gemini), an integrator-recorded
strict two-of-three majority, a matching row in `docs/DECISION_LOG.md`, and
matching `docs/ROADMAP.md` / `CHANGELOG.md` / operator-report updates that
preserve every existing no-claims boundary. `git diff --check` is clean;
runtime, test, packaging, and `.striatum/` paths are unchanged.

## Coverage — Every Decision Has The Required Evidence Chain

`striatum/0052-successor-decision-research/integration/DECISION_RESULTS.md`
enumerates six decisions. For each one I confirmed: a research packet exists,
three vote artifacts exist, the vote counts in the integrator's table match
what the vote files actually selected, the corresponding `docs/DECISION_LOG.md`
row exists, and the `docs/ROADMAP.md` posture is consistent.

| Decision | Research packet | Claude vote | Codex vote | Gemini vote | Integrator tally | DECISION_LOG | ROADMAP |
| --- | --- | --- | --- | --- | --- | --- | --- |
| High-angle product surface | `research/high_angle_product_surface/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D014 (`docs/DECISION_LOG.md:47`) | `docs/ROADMAP.md:117-120`, `docs/ROADMAP.md:139` |
| OpenFOAM success gate | `research/openfoam_success_gate/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D012 (`docs/DECISION_LOG.md:45`) | `docs/ROADMAP.md:110-113`, `docs/ROADMAP.md:137` |
| Public demo operations | `research/public_demo_ops/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D015 (`docs/DECISION_LOG.md:48`) | `docs/ROADMAP.md:121-124`, `docs/ROADMAP.md:135` |
| Resistance source candidate | `research/resistance_source_candidate/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D013 (`docs/DECISION_LOG.md:46`) | `docs/ROADMAP.md:114-116`, `docs/ROADMAP.md:138` |
| Sweep next delta | `research/sweep_next_delta/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D016 (`docs/DECISION_LOG.md:49`) | `docs/ROADMAP.md:125-127`, `docs/ROADMAP.md:140` |
| Volume-mesher path | `research/volume_mesher_path/RESEARCH.md` | Option A | Option A | Option A | 3-0 A | D011 (`docs/DECISION_LOG.md:44`) | `docs/ROADMAP.md:103-109`, `docs/ROADMAP.md:136` |

Each vote artifact carries the `striatum.synthesis.v1` front matter and names
the panelist byline (`panelist-claude-opus-4.7-*`, `panelist-codex-gpt-5.5-*`,
`panelist-gemini-pro-3.1-*`, or an operator-self-declared Gemini fallback byline
where the wave-one Gemini lanes were repaired). Every vote cites the
workflow-local research packet, names at least one local product/RFC source
(`docs/DECISION_LOG.md`, `docs/ROADMAP.md`, `docs/PRD.md`,
`docs/design/kayak_hull_design_constraints.md`,
`kayakgen/eval/stability.py`, `kayakgen/cli/main.py`,
`kayakgen/search/sweep.py`, `kayakgen/eval/contract.py`,
`kayakgen/ui/web/app.py`, `tests/test_sweep.py`, `tests/test_web_layout.py`,
`docs/WEB_VERIFICATION.md`, and the workflow 0050/0051 final reviews), and
cites independent external references dated 2026-05-14 (USCG Stability
Reference Guide, eCFR 46 CFR §28.570 / §174.015, ISO 12217-3:2022, Maxsurf,
Orca3D, Guillemot Kayaks, OpenFOAM.com v2512 tutorials and forces.C,
Edinburgh DataShare DOI `10.7488/ds/3785`, DigitalOcean App Platform / Render
/ Railway / Fly.io pricing pages, Optuna, SciPy, pymoo, W3C PROV, etc.).

## Majority Derivation — Integrator Tally Matches The Votes

Spot-checked all six panels by reading vote-line text directly:

- `panels/high_angle_product_surface/{claude,codex,gemini}/VOTE.md` — three
  Option A (staged explicit surfacing).
- `panels/openfoam_success_gate/{claude,codex,gemini}/VOTE.md` — three
  Option A (full evidence gate before success).
- `panels/public_demo_ops/{claude,codex,gemini}/VOTE.md` — three Option A
  (defer public operation until operator gates).
- `panels/resistance_source_candidate/{claude,codex,gemini}/VOTE.md` — three
  Option A (Edinburgh validation-only full packet).
- `panels/sweep_next_delta/{claude,codex,gemini}/VOTE.md` — three Option A
  (`pending` candidate state next).
- `panels/volume_mesher_path/{claude,codex,gemini}/VOTE.md` — three Option A
  (OpenFOAM-v2512 `snappyHexMesh` evidence harness).

The tally table at
`striatum/0052-successor-decision-research/integration/DECISION_RESULTS.md:31-38`
matches the vote artifacts exactly. The strict two-of-three majority rule
documented at `integration/DECISION_RESULTS.md:18-24` is applied uniformly,
and the `Unresolved Items` block at `:168-186` truthfully reports zero
sub-majority panels. No workflow 0052 panel had a minority vote — every
decision reached a 3-0 majority.

## No-Claims Boundary — Decisions Preserve Existing Limits

For each at-risk product domain, the text added by this workflow is either a
deferral, an exit criterion gated on named evidence, or a non-goal — never a
current capability claim. I grep-checked the diff for "calibrated",
"final prediction", "design fitness", "production volume", "hosted CFD",
"validated CFD", "seaworth", "safe angle", and "capsize"; every added
occurrence is inside a negation, an exit criterion, an explicit deferral, or
a non-goal list.

- **Volume-mesher path (D011).** Selects OpenFOAM-v2512 `snappyHexMesh` as
  the first production volume-mesher candidate, but lands it strictly as a
  deterministic OpenFOAM-readable evidence harness over
  `generated_hull_plus_deck_closed_body_v1`. Ordinary generated packages,
  real OpenFOAM `succeeded` records, calibrated CFD, final prediction,
  design fitness, hosted worker readiness, and broad `cfd_ready` promotion
  remain unauthorized (`docs/DECISION_LOG.md:44`,
  `docs/ROADMAP.md:103-109`, `docs/ROADMAP.md:213-227`).
- **OpenFOAM success gate (D012).** Keeps
  `openfoam-v2512-interfoam-local` unable to return `succeeded` until five
  named gates bind in one run record (mesh evidence, v2512 provenance,
  deterministic case smoke, corrected v2512 `force.dat` parser,
  raw-unvalidated payload). After the gate opens, `succeeded` means only
  local solver execution plus raw artifact parsing
  (`docs/DECISION_LOG.md:45`, `docs/ROADMAP.md:110-113`,
  `docs/ROADMAP.md:253-258`). No validation, calibration, final prediction,
  design-fitness, or broad readiness claim is authorized.
- **Resistance source candidate (D013).** Selects Edinburgh DataShare DOI
  `10.7488/ds/3785` for a full RFC 0042 source-review packet capped at
  `validation_fixture`; calibration-fixture promotion is explicitly
  blocked because the hull class lies outside the kayak/surfski envelope.
  Resistance output remains `uncalibrated_comparative`
  (`docs/DECISION_LOG.md:46`, `docs/ROADMAP.md:114-116`,
  `docs/ROADMAP.md:138`).
- **High-angle product surface (D014).** Authorizes surfacing fixed-trim
  generated-body v1 only through a staged, opt-in path with explicit
  body/load/trim/provenance warnings and
  `result_semantics="unvalidated_hydrostatic_comparison"`. Default
  `kayakgen stability`, default sweep summaries, comparison frontiers, and
  Pareto objectives remain unchanged; no safety, seaworthiness, capsize,
  ISO, validation, solver-readiness, final-prediction, or design-fitness
  wording is allowed (`docs/DECISION_LOG.md:47`,
  `docs/ROADMAP.md:117-120`, `docs/ROADMAP.md:139`).
- **Public demo operations (D015).** Defers public browser operation until
  operator owner, budget/cap, deployed revision, hosted smoke, persistence,
  cleanup, and public no-claims wording are all recorded. The authorized
  shape, once gates exist, is one fixed-size managed container running the
  existing `kayakgen serve --host 0.0.0.0 --port 8080` or repo Docker path,
  with autoscaling, databases, queues, hosted workers, and persistent
  volumes off unless explicitly budgeted and cleaned up
  (`docs/DECISION_LOG.md:48`, `docs/ROADMAP.md:121-124`,
  `docs/ROADMAP.md:181-202`). Static/Pyodide, production hosting, accounts,
  quotas, collaboration features, and hosted CFD require separate decisions.
- **Sweep next delta (D016).** Schedules the RFC 0009 `pending` candidate
  lifecycle state as the next sweep/search delta with additive
  `pending_count`, explicit transition/resume policy, and pending records
  that are visible but frontier-ineligible. Sweep-side STL artifacts,
  optimizer/search loops, parallel worker queues, calibrated resistance,
  real OpenFOAM `succeeded`, high-angle surfacing, public browser hosting,
  and new design-fitness semantics remain explicitly out of scope
  (`docs/DECISION_LOG.md:49`, `docs/ROADMAP.md:125-127`,
  `docs/ROADMAP.md:140`).

The integrator's `Implementation Burn-Down Queue`
(`integration/DECISION_RESULTS.md:188-221`) sequences follow-up work
consistently with the dependency tracks in `docs/ROADMAP.md:131-140` and
batch text in `docs/ROADMAP.md:142-264`. Each follow-up item is gated on the
same evidence the decision rows require.

## Documentation-Only Boundary

`git status --short` shows exactly the file set the work packet permits for
a final-review job that touches only the workflow's `final/` directory, plus
the integration-lane files that pre-existed at claim time:

```
 M CHANGELOG.md
 M docs/DECISION_LOG.md
 M docs/ROADMAP.md
 M docs/workflows/0052-successor-decision-research/OPERATOR_REPORT.md
?? striatum/0052-successor-decision-research/integration/
?? striatum/0052-successor-decision-research/panels/high_angle_product_surface/gemini/
?? striatum/0052-successor-decision-research/panels/openfoam_success_gate/gemini/
?? striatum/0052-successor-decision-research/panels/public_demo_ops/gemini/
?? striatum/0052-successor-decision-research/panels/resistance_source_candidate/gemini/
?? striatum/0052-successor-decision-research/panels/sweep_next_delta/gemini/
?? striatum/0052-successor-decision-research/panels/volume_mesher_path/gemini/
```

`git status --short -- kayakgen tests src pyproject.toml setup.py setup.cfg
.striatum`: empty. No runtime, test, packaging, or Striatum-state file was
modified by the integration lane, and this final-review lane writes only
this artifact under
`striatum/0052-successor-decision-research/final/FINAL_REVIEW.md`.

`git diff --check`: clean (no whitespace warnings).

Per-file content check:

- `CHANGELOG.md` — adds a single Unreleased entry under `### Added`
  (`CHANGELOG.md:21-30`) describing workflow 0052 as a documentation-only
  majority-decision integration with an explicit "No runtime behavior,
  tests, solver execution, public URL, calibration, watertight readiness,
  default high-angle output, desktop rewrite, optimization behavior, or
  product capability changed" disclaimer. No removals; no capability
  claims.
- `docs/DECISION_LOG.md` — appends rows D011–D016
  (`docs/DECISION_LOG.md:44-49`) in the four-cell receipt format defined at
  `docs/DECISION_LOG.md:6-29`, each citing the relevant RFC and recording
  context, consequence, and revisit triggers. Decision text matches the
  integration's accepted-decision sections.
- `docs/ROADMAP.md` — adds the `Workflow 0052 Decision Posture` section
  (`docs/ROADMAP.md:97-127`); updates the `Dependency Tracks` table and
  several Future Striatum Batches sections to reflect the decisions;
  preserves and reinforces every no-claims rule already in force. The diff
  changes ~190 lines but every added rule text is in a no-claims or
  exit-criterion frame.
- `docs/workflows/0052-successor-decision-research/OPERATOR_REPORT.md` —
  appends timestamped operator checkpoints describing the run lifecycle,
  including the wave-one/wave-two Gemini panel state and the integration
  scope. Operator bookkeeping only; no product-visible claim.
- `striatum/0052-successor-decision-research/**` — workflow-local
  artifacts only: six research packets, eighteen panel votes (six of which
  are repaired Gemini votes carrying an `operator [self-declared]` byline
  with the wave label, recorded in the workflow operator report), the
  integration decision-results synthesis, the integration patch summary,
  and this final-review file.

## Lane / Artifact Consistency Cross-Checks

- Each vote artifact's `author:` byline names the lane and model.
  Claude votes use `panelist-claude-opus-4.7-*` bylines (e.g.
  `panelist-claude-opus-4.7-001` for sweep_next_delta;
  `panelist-claude-opus-4.7-006` for openfoam_success_gate); Codex votes
  use `panelist-codex-gpt-5.5-*` bylines; the six Gemini votes carry the
  `operator [self-declared: operator-0052-panel-wave1-gemini-N]` byline
  documented in `docs/workflows/0052-successor-decision-research/OPERATOR_REPORT.md`
  for the wave-one repair path, except `volume_mesher_path/gemini/VOTE.md`
  which uses `panelist-gemini-pro-3.1-009`. The integrator
  (`decision-integrator-codex-gpt-5.5-001`) and this final reviewer
  (`final-reviewer-claude-opus-4.7-001`) come from the supplied work
  packet, not the job title.
- The integration's `Shared Risks Preserved`
  (`integration/DECISION_RESULTS.md:148-167`) lists six specific failure
  modes (high-angle `GZ` misread as safety/capsize, OpenFOAM `force.dat`
  parser correctness, snappyHexMesh / `checkMesh` over-read as validated
  CFD, Edinburgh out-of-envelope status, public demo cost/uptime/abuse,
  `pending` records carrying fitness/partial-success implications). Each
  risk has a corresponding `revisit` trigger in the relevant decision-log
  row (`docs/DECISION_LOG.md:44-49`).
- The Patch Summary at
  `striatum/0052-successor-decision-research/integration/PATCH_SUMMARY.md`
  enumerates the exact same five edited files plus the two
  workflow-local integration artifacts, and explicitly notes that the
  untracked Gemini panel-vote directories pre-existed integration claim.
  This matches `git status --short` observed at final-review claim time.

## Validation

- `git status --short`: only `CHANGELOG.md`, `docs/DECISION_LOG.md`,
  `docs/ROADMAP.md`, the workflow operator report, and the untracked
  `striatum/0052-successor-decision-research/integration/` and per-panel
  Gemini subdirectories.
- `git status --short -- kayakgen tests src pyproject.toml setup.py
  setup.cfg .striatum`: empty.
- `git diff --check`: clean.
- `git diff --stat HEAD CHANGELOG.md docs/DECISION_LOG.md docs/ROADMAP.md
  docs/workflows/0052-successor-decision-research/OPERATOR_REPORT.md`:
  +10 / +6 / +190 / +10 lines respectively; all within scope.
- Vote-count cross-check: read all eighteen vote artifacts and confirmed
  each vote text matches the entry in the integrator's tally table
  (`integration/DECISION_RESULTS.md:31-38`).
- Forbidden-phrase grep across the `docs/ROADMAP.md` diff (`calibrated`,
  `final prediction`, `design fitness`, `seaworthiness`, `production
  volume`, `hosted CFD`, `validated CFD`, `safe angle`, `capsize`): every
  added occurrence is in a no-claims rule, an exit criterion, a non-goal,
  or a deferred-batch description.
- Cross-checked decision rows D011–D016 against
  `integration/DECISION_RESULTS.md` accepted-decision sections and against
  the relevant RFCs (0040, 0041, 0042, 0024, 0008/0030/0032, 0009/0013).
  Each row's RFC citation, context, consequence, and revisit trigger is
  consistent with the panel votes and the existing RFC index narrative.
- No runtime tests were run: this packet, the reviewed integration, and
  this final-review artifact are documentation and workflow artifacts
  only.

## Findings

None blocking.

### Optional observations (non-blocking, informational)

- Six of the eighteen Gemini vote artifacts (one per panel, wave-one for
  five panels plus one wave-two) carry an
  `author: operator [self-declared: operator-0052-panel-wave1-gemini-N]`
  byline rather than a model-named `panelist-gemini-pro-3.1-*` byline.
  The workflow operator report documents the cause:
  `process_exit_nonzero` on four wave-one Gemini jobs after quota
  exhaustion, and two wave-two jobs whose pre-claim attested supervisor
  startup was lost before packet delivery
  (`docs/workflows/0052-successor-decision-research/OPERATOR_REPORT.md:28-36`).
  The repaired Gemini artifacts are still real, evidence-bound votes
  citing the workflow-local research packets and independent external
  references; they did not change any majority because every panel
  reached 3-0 even before the Gemini bylines were considered (the Claude
  and Codex pair alone already cleared the strict two-of-three rule for
  every decision). If a future Striatum release surfaces a first-class
  operator-substitution byline format, this lane is the natural surface
  to revisit. `volume_mesher_path/gemini/VOTE.md` uses the standard
  `panelist-gemini-pro-3.1-009` byline.
- D016's pending-lifecycle decision and D010's existing
  sweep-admissibility row both name RFC 0009 status reconciliation as a
  prerequisite for optimizer work. RFC 0009 remains indexed as
  `proposed` in `docs/rfcs/README.md`; reconciling that label is
  appropriately deferred to a follow-up workflow rather than retroactively
  edited here. This is consistent with the workflow 0050 final review's
  treatment of the same stale index entry.
- D013 caps the Edinburgh DataShare source at `validation_fixture` because
  the hull class is outside the kayak/surfski calibration envelope. The
  decision row's revisit trigger correctly names the conditions under
  which a kayak-envelope measured source could replace this cap; no
  current source qualifies.

## Summary

Accept. Workflow 0052 produces six design and sequencing decisions that are
each research-backed (workflow-local research packet plus independent
external citations dated 2026-05-14), majority-derived (strict two-of-three
across Claude, Codex, and operator-repaired or model-bylined Gemini votes,
with every panel reaching 3-0), evidence-bound (every consequence and exit
criterion is tied to named RFC, fixture, source-review, OpenFOAM provenance,
or operator evidence), and documentation-only (no runtime, test, packaging,
or `.striatum/` state changes; `git diff --check` clean). The decision-log
rows, roadmap posture, changelog entry, and operator report preserve every
existing no-claims boundary on resistance, CFD, mesh readiness, stability,
validity, hosting, parity, and optimization.
