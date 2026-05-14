---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-claude-opus-4.7-005
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_55145e98ddd44d22965f9aa7d3bdde77
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_calibrated_resistance_claude
lease: lease_2808c35acff348e4a88bfe8952801e49

# Panel Vote — Calibrated Resistance Promotion

## Vote

**Option A (Conservative Default: preserve the current no-promotion gate) as
the operative decision, with Option B recorded as the desired future
accepted-fit gate shape. Reject Option C. Reaffirm Option D's deferral —
design-fitness wording is not authorized by any calibration outcome.**

## Decision Sentence For `docs/DECISION_LOG.md`

Workflow 0050 does not promote any kayak-gen resistance output to calibrated
wording, does not select numeric fit-acceptance thresholds, and does not
authorize a calibrated comparative-ranking claim. The current default
`resistance_curve()` output remains `uncalibrated_comparative`, the existing
`claim_allows_calibrated_prediction` gate in `kayakgen/eval/claims.py` remains
authoritative, and `claim_allows_final_design_fitness` remains separate and
unsatisfied. A later accepted-fit workflow may permit "calibrated resistance
prediction within `[model_version]` envelope" wording only after RFC 0042
source review accepts a kayak-envelope calibration fixture with rights,
extraction, units, uncertainty, fixture ID/version, and envelope; a named
immutable `model_version` reaches `accepted_fit`; RMSE/NRMSE, MAPE with
low-force safeguards, bias by Froude band, max error, monotonicity,
non-negative, and holdout/validation metrics pass pre-declared thresholds;
the evaluated hull/speed lies inside the envelope; and every serialized
output records the concrete `model_version` and fixture IDs. The PRD's
existing "within 25% across the Fn 0.25–0.50 range" criterion is retained as
a provisional **upper-bound** ceiling, not as the final acceptance threshold.

## Evidence

### Research-Packet Evidence

`striatum/0050-decision-panel-research/research/calibrated_resistance/RESEARCH.md`
maps the decision to four options and recommends Option A for the current
decision plus Option B as the desired future gate shape. The packet anchors
that recommendation in:

- `docs/PRD.md:38-42` (current resistance output is exploratory, not
  calibrated) and `docs/PRD.md:51-57` (calibrated prediction is roadmap-only
  pending licensed, relevant kayak-scale validation fixtures).
- `docs/ROADMAP.md:34-40` (No-Claims Rules: resistance output is
  `uncalibrated_comparative`, not a calibrated model, final prediction,
  design-fitness score, or default optimization objective) and
  `docs/ROADMAP.md:166-189` (Batch F sequencing: source review → validation
  fixture ingest → calibration fixture ingest → defer fitting to a separate
  accepted-fit workflow).
- `docs/rfcs/0027-resistance-calibration-acceptance.md:74-122` (claim-gate
  authority: fit metadata schema, minimum metric set, and the strict list of
  conditions under which resistance output may stop saying `uncalibrated`).
- `docs/rfcs/0042-resistance-calibration-fixture-successor.md:86-153` (source
  review and calibration fixture promotion checklist; parser success and
  plausible residuals are explicitly *not* promotion).
- `kayakgen/eval/claims.py:195-227` (the actual `claim_allows_*` helpers).
- `kayakgen/eval/resistance.py:165-189` (default output emits
  `uncalibrated_comparative`).
- `kayakgen/eval/calibration.py:1-5,107-185` (registry says records describe
  candidate sources only; no accepted calibration fixture exists; Edinburgh
  Pacific-canoe is validation-candidate; Sea Kayaker is citation-only;
  Gomes/Tzabiras K1 are validation-candidate with rights/envelope limits).

The external sources cited by the packet (ITTC Resistance Test 7.5-02-02-01;
ITTC Resistance Uncertainty Analysis 7.5-02-02-02; FDA CM&S credibility
guidance Nov 2023; Edinburgh DataShare Pacific-canoe + license; Gomes et al.
2018 K1 study; scikit-learn RMSE/MAPE/R²; MLflow Model Registry workflow;
SemVer 2.0.0) collectively support: mandatory fixture metadata + envelope,
bias-and-precision uncertainty treatment, context-of-use credibility framing,
RMSE+MAPE-with-safeguards over R² alone, and immutable versioned models with
selector aliases at lookup time only — not as substitutes for `model_version`
in serialized fit records.

### Independent Check On Current Code

I verified the load-bearing implementation claims directly rather than
relying on the research packet's quotation:

- `kayakgen/eval/claims.py:195-210` — `claim_allows_calibrated_prediction`
  requires the conjunction of: `claim_state == CALIBRATED_MODEL`;
  `ACCEPTED_USE_FINAL_PREDICTION in accepted_uses`; non-empty
  `calibration_fixture_ids`; non-empty `model_version`; `fit_status` in
  `CANONICAL_PASSING_FIT_STATUSES`; non-empty `fit_metrics`; non-null
  `validity_envelope`; and `not UNCALIBRATED_WARNING_CODES.intersection(claim.warnings)`.
- `kayakgen/eval/claims.py:213-227` — `claim_allows_final_design_fitness` is
  a separate gate requiring `claim_state == VALIDATED_DESIGN_FITNESS`,
  `ACCEPTED_USE_FINAL_DESIGN_FITNESS in accepted_uses`, and a non-null
  `validity_envelope`. No current output satisfies it.
- `kayakgen/eval/resistance.py:165-189` — the default `resistance_curve()`
  emits `claim_state=UNCALIBRATED_COMPARATIVE`,
  `calibration_fixture_ids=[]`, `model_version=None`, `fit_status=None`,
  `fit_metrics={}`, `validity_envelope=None`, and
  `warnings=uncalibrated_resistance_warnings()`.
- `kayakgen/eval/calibration.py:17-87` — the `SourceUse` literals include
  `calibration_fixture_candidate` and `calibration_fixture`, and the
  `calibration_fixture` branch enforces fixture review metadata at construction;
  rows alone cannot promote.

This means the runtime contract already encodes the gate Option A preserves:
removing `uncalibrated` wording requires a coordinated set of evidence that
no current registry record can supply. The strict-conjunction gate is not
hypothetical; it is what `kayakgen` ships today, and adopting Option B or C
now would require either weakening that helper or constructing fixture
metadata that the registry does not have.

### Independent Domain Check

- `docs/PRD.md` Success Criteria / Evaluation: "Matching published kayak
  model-test data within 25% across the Fn 0.25–0.50 range remains a
  calibration-roadmap criterion." This is the same number the research
  packet recommends as a provisional **upper-bound** ceiling — i.e., it is
  the most lenient acceptance threshold the project has ever signalled,
  not the floor. Treating it as a floor would invert the PRD's stance.
- `docs/design/kayak_hull_design_constraints.md` (kayak resistance regime,
  displacement Fn ≲ 0.6) supports a narrow validity envelope: Pacific-canoe
  and K1 sources do not by themselves cover the sea-kayak/surfski envelope
  the project's class presets target. This corroborates the research
  packet's "no cross-class promotion by default" envelope rule.
- `docs/DECISION_LOG.md` D002 records the PRD scope expansion to absorb
  RFCs 0005–0008 but does not promote resistance beyond exploratory. No
  prior decision row authorizes calibrated wording.
- `docs/ROADMAP.md` Scheduling Guidance lines 275-277 explicitly forbid
  starting calibrated-resistance fitting "before at least one kayak-envelope
  measured source is accepted as a calibration fixture with rights,
  extraction, units, fit metadata, and validity envelope." Option A is the
  only option that respects this guidance as written.

### External-Source Spot-Check

I did not re-fetch the external URLs from this session (`WebFetch` is not in
the loaded tool surface), but the research packet's claim-to-source mapping
is internally coherent and consistent with what each of those primary
sources publishes:

- ITTC 7.5-02-02-01 publishes the resistance-test reporting checklist
  (model identity, loading, turbulence stimulation, scale, hydrostatics,
  tank particulars, form factor/correlation, per-speed resistance plus
  sinkage/trim) — that directly supports making fixture metadata fields
  mandatory rather than optional.
- ITTC 7.5-02-02-02 separates bias and precision in uncertainty treatment
  and shows residual-resistance-coefficient uncertainty exceeding
  total-resistance-coefficient uncertainty — supports uncertainty-aware
  acceptance metrics and Froude-band residual review.
- FDA CM&S credibility guidance (Nov 2023) frames model credibility against
  a context-of-use with pre-specified accuracy criteria — supports tying
  calibrated wording to an explicit envelope rather than global claims.
- Edinburgh DataShare Pacific-canoe (CC BY 4.0) and Gomes et al. 2018 K1
  passive-drag — both are good *validation* candidates but neither covers
  the sea-kayak/surfski calibration envelope the PRD presets target.
- scikit-learn RMSE/MAPE/R² docs and SemVer 2.0.0 / MLflow registry — the
  metric and versioning behaviors the research packet relies on (RMSE
  non-negative, MAPE unstable near zero force, R² non-symmetric and can be
  negative; immutable released versions with selector aliases) are
  well-established library behavior consistent with documented contracts.

Nothing in the local code, RFC index, or roadmap contradicts those external
claims, and nothing in them supports Option C's looser "calibrated comparative
ranking" wording or Option B's adoption *now* without an accepted fixture.

## Why Rejected Alternatives Lose

### Option B — Adopt The Calibrated-Prediction Gate Shape *As The Operative Decision Now*

Loses *as the operative decision* (it is fine as a recorded *future* gate
shape) because:

- It would commit the project to numeric fit-acceptance thresholds before
  source uncertainty, row count, speed distribution, fixture hull coverage,
  and holdout behavior are known. The packet correctly observes that the
  PRD's 25%-over-Fn-0.25-0.50 number is an *upper-bound ceiling*, not a
  defensible final threshold. Adopting it as a binding gate now would
  hard-code the most lenient acceptable number into RFC-level commitments.
- It would pre-commit envelope semantics (hull class, L/B_wl, draft, Cp
  ranges, load case, trim policy, water properties, fitted parameter list,
  excluded cases, fallback rule) before any candidate source's actual
  coverage is known. Ranges chosen ahead of a real fixture will either be
  overly conservative (excluding the very fixture you accept) or overly
  generous (inviting out-of-envelope calibrated wording).
- The current source registry has no accepted calibration fixtures —
  `kayakgen/eval/calibration.py:107-185` records only candidates. RFC 0042
  is the workflow that has to land first. Adopting Option B operatively now
  would either (i) be empty in practice because no fixture meets it, or
  (ii) pressure RFC 0042 into rubber-stamping a candidate source against
  pre-committed thresholds — exactly the failure mode the no-claims rules
  exist to prevent.

Option B is the right *target shape*; it is not the right *current decision*.
Recording it as the desired future gate shape captures its value without
binding RFC 0042 review or a later accepted-fit workflow to numbers they do
not yet have evidence to choose.

### Option C — Comparative Calibration For Ranking Only

Loses because:

- The runtime claim model does not have a "calibrated comparative ranking"
  accepted-use value. `ACCEPTED_USE_FINAL_PREDICTION` and
  `ACCEPTED_USE_COMPARATIVE_FILTER` are the relevant values today, and the
  former is the one the calibrated-prediction gate keys on. Creating a new
  accepted-use literal mid-workflow would change the claim taxonomy without
  RFC backing.
- "Calibrated" in UI copy will be over-read by users regardless of the
  qualifier. The research packet's wording matrix and the FDA CM&S
  credibility frame both warn against this. The PRD already positions
  resistance estimates as "useful for ranking nearby candidate hulls" *as
  an uncalibrated comparative filter*; Option C does not add information
  to that disposition, it just relaxes the wording standard.
- Rank-correlation metrics across multiple measured hulls are exactly what
  the project does not have yet — the candidate sources span Pacific
  canoes and K1, not the sea-kayak/surfski preset family. Even if those
  hulls were promoted to validation fixtures, the rank-only claim would
  generalize poorly to design-space ranking inside the project's preset
  envelope. The packet correctly identifies this as the single-hull
  generalization risk.

### Option D — Validated Design Fitness

Loses *as something this decision authorizes*, but its underlying deferral
is correct and must remain in force. No resistance-calibration outcome by
itself authorizes a design-fitness claim. `claim_allows_final_design_fitness`
remains a separate gate keyed on `VALIDATED_DESIGN_FITNESS` /
`ACCEPTED_USE_FINAL_DESIGN_FITNESS`, must be set by a future RFC combining
calibrated resistance with hydrostatics, accepted high-angle stability, design
constraints, user objective weights, uncertainty, and warnings, and is not
set by anything in workflow 0050.

### Doing Nothing / Skipping The Future-Gate Record

Loses (compared to A-plus-Option-B-as-future-target) because RFC 0042 needs a
durable record of what an accepted-fit workflow will eventually have to
deliver. Without it, RFC 0042 reviewers cannot know whether a candidate
source's recorded metadata is sufficient for a future fit, only whether it
clears the source-review checklist. Recording Option B's gate shape as the
target — without committing numeric thresholds — gives the next workflow a
concrete handoff target while keeping the binding decision to Option A.

## Implementation Gates That Must Remain In Force

The following gates are not relaxed by this decision and any consuming
workflow must preserve them:

1. **Source-review gate before promotion.** RFC 0042 source-review packets
   must record rights, measurement type, units, hull class, speed/Froude
   range, trim/sinkage, extraction method, uncertainty, and verdict before
   *any* source-use state advances. Parser success or plausible residuals
   are not promotion.
2. **Calibration-fixture promotion gate.** Promotion to `calibration_fixture`
   requires accepted rights, measured drag/resistance data, kayak-envelope
   applicability, load and speed/Froude ranges, extraction and uncertainty
   treatment, row schema, unit normalization, and a named fixture
   ID/version/envelope/reason. `kayakgen/eval/calibration.py` already
   enforces a fixture-metadata invariant on construction; that invariant
   must not be relaxed for convenience.
3. **Fit-record schema gate.** A named resistance model version may be
   declared only with an immutable `ResistanceFitRecord` capturing
   `model_version`, `fit_status`, `calibration_fixture_ids`,
   `validation_fixture_ids`, `fitted_parameters`, `metrics`, `residuals_ref`,
   `validity_envelope`, and `warnings`. Aliases (`latest`, `default`,
   `champion`) may exist in selector configuration but must not persist as
   the recorded `model_version` on a serialized curve.
4. **Minimum metric set gate.** Acceptance metrics must include force RMSE
   (dimensional), force NRMSE (normalized), force MAPE *with a declared
   low-force epsilon and a `mape_excluded_low_force_rows` count when
   applicable*, mean bias and bias-by-Froude-band, max absolute and max
   percent error, monotonicity-vs-speed and non-negative-resistance checks,
   and holdout RMSE/MAPE or validation-fixture error when enough rows or an
   accepted validation fixture exists. Rank-correlation metrics may
   accompany force metrics but must not substitute for them when wording
   says prediction. R² alone is not an acceptance metric.
5. **Validity envelope gate.** The envelope must be the intersection of
   project design scope and accepted fixture coverage — not the full
   parameter space. It must serialize speed and Fn ranges (initial target
   no broader than the PRD/RFC calibration range around Fn 0.25–0.50),
   hull class and allowed preset family with no cross-class promotion,
   length / waterline beam / `L/B_wl` / draft / displacement-load / `Cp`
   ranges, load case and trim/sinkage assumptions (fixed sink/trim vs free
   trim), water properties and Reynolds-range notes, turbulence/transition
   assumptions where known, fitted-parameter list (e.g. ITTC form factor,
   Michell wave scale, total-resistance residual correction), excluded
   cases, and fallback rule.
6. **Envelope-membership wording gate.** Out-of-envelope evaluation is a
   hard wording gate. Even when a selected `model_version` has an accepted
   fit elsewhere, an evaluated hull/speed outside the envelope must keep
   uncalibrated/out-of-envelope warnings and must not be reported as
   calibrated prediction. The curve remains available as raw comparative
   output with its warnings preserved.
7. **Model versioning gate.** Resistance model versions must be immutable
   (SemVer-compatible, optionally with `+fit.<short_hash>` build metadata),
   recorded alongside algorithm/fit code revisions, fitted parameter
   values, calibration and validation fixture IDs and versions,
   source-review IDs, data checksums, fit metrics, residual artifact
   reference, validity envelope, and accepted review date. Major bumps for
   equation family / fitted-parameter meaning / fixture set / acceptance
   thresholds / envelope semantics. Minor for backward-compatible envelope
   extension or non-breaking metadata. Patch for bug fix or recomputation
   preserving fixture set, envelope, thresholds, and claim semantics. Do
   not mutate an already published fit artifact in place.
8. **Claim-helper gate.** Removing `uncalibrated` wording must route
   through `kayakgen/eval/claims.py::claim_allows_calibrated_prediction`
   *plus* a separate envelope-membership check, not through ad hoc
   string-formatting branches in CLI/web/report code paths. Legacy
   `fit_status` aliases, validation fixtures alone, or non-empty metrics
   alone must continue to fail this gate. The "rejected" source-use state
   must remain a review outcome, not a runtime fixture state.
9. **Design-fitness separation gate.**
   `claim_allows_final_design_fitness` remains a *separate* gate and is
   not satisfied by any calibration outcome. Promoting to
   `validated_design_fitness` requires a future RFC over calibrated
   resistance, hydrostatics, real high-angle `GZ` availability, design
   constraints, user objective weights, uncertainty, and warnings.
10. **Provisional ceiling, not floor.** The PRD's "within 25% across the
    Fn 0.25–0.50 range" remains a provisional **upper-bound** target for
    *eventual* calibrated prediction. It is not the acceptance threshold;
    the accepted-fit workflow must set final thresholds from source
    uncertainty, row count, speed distribution, fixture hull coverage,
    and holdout behavior.

## No-Claims Language That Must Remain In Force

This decision does not relax any of the following, and consuming workflows
must preserve them verbatim where they already appear in `docs/PRD.md`,
`docs/USER_GUIDE.md`, `docs/ROADMAP.md`, and the RFC index:

- Resistance output is `uncalibrated_comparative` — a raw analytical
  screening filter for ranking candidate hulls — not a calibrated model,
  final prediction, design-fitness score, or default optimization
  objective.
- The current `resistance_curve()` default state remains
  `UNCALIBRATED_COMPARATIVE` with empty `calibration_fixture_ids`, null
  `model_version`, empty `fit_metrics`, null `validity_envelope`, and the
  uncalibrated warning set produced by `uncalibrated_resistance_warnings()`.
- No current registry source — Edinburgh Pacific-canoe (CC BY 4.0),
  Sea-Kayaker-derived tables, Gomes/Tzabiras K1 records — becomes a
  calibration fixture by virtue of this decision. They remain candidate
  sources subject to RFC 0042 review.
- A validation fixture does not satisfy the calibrated-prediction gate. A
  source with checked-in rows that exercises parsers, reports, or
  adapter behavior is not a calibration fixture.
- Calibrated resistance, if it is ever produced, does not authorize design
  fitness. `claim_allows_final_design_fitness` remains unsatisfied.
- The PRD's 25%-over-Fn-0.25-0.50 statement remains a roadmap-criterion
  ceiling for *future* calibrated wording. It does not authorize
  calibrated wording today, and it does not survive the accepted-fit
  workflow as a final threshold without source-aware refinement.
- "Calibrated comparative ranking" is not a recognized claim state. The
  runtime accepted-use literals remain `comparative_filter` and
  `final_prediction` (with `final_design_fitness` reserved for the future
  design-fitness gate); no new accepted-use is created here.
- Workflow 0050 does not select a numeric fit-acceptance threshold, an
  accepted calibration fixture, an accepted model version, or an accepted
  envelope. Those are RFC 0042 and the later accepted-fit workflow's job.

## Confidence

**High.**

Rationale: the operative posture is mechanically aligned with `docs/PRD.md`
Roadmap and Success Criteria, `docs/ROADMAP.md` No-Claims Rules and Batch F,
`docs/rfcs/0027-resistance-calibration-acceptance.md` claim-gate authority,
`docs/rfcs/0042-resistance-calibration-fixture-successor.md` source-review
and fixture-promotion requirements, and the runtime claim-helper
implementation I verified directly in `kayakgen/eval/claims.py` and
`kayakgen/eval/resistance.py`. The external evidence cited by the research
packet (ITTC reporting and uncertainty procedures, FDA CM&S credibility
framing, MLflow / SemVer versioning, scikit-learn metric behavior, the
Edinburgh and Gomes datasets) supports the gate shape recorded for the
future but does not support promoting any source today; no candidate source
covers the sea-kayak/surfski envelope the project's presets target. The
recorded-but-not-binding posture on Option B captures the gate shape RFC
0042 reviewers and the eventual accepted-fit workflow will need, without
pre-committing numeric thresholds or envelope semantics that depend on
fixture coverage the project does not yet have.

The only meaningful unknowns are (i) whether any licensable measured
sea-kayak dataset broad enough to fit the default design envelope exists at
all, and (ii) whether the eventual accepted-fit workflow will adopt the 25%
ceiling, a tighter source-uncertainty-derived threshold, or a banded
threshold that varies across the Fn range. Both are correctly deferred —
they are RFC 0042 and accepted-fit-workflow decisions, not workflow 0050
decisions.

## Sources Reviewed

Local:

- `AGENTS.md`
- `docs/PRD.md` (Audience, Delivered Today / Evaluation, Roadmap And
  Deferrals, Success Criteria / Evaluation)
- `docs/USER_GUIDE.md` (referenced via packet; not re-read for this vote
  beyond the no-claims posture)
- `docs/ROADMAP.md` (especially No-Claims Rules, Batch F, Scheduling
  Guidance)
- `docs/DECISION_LOG.md` (D001, D002 — no calibration decision row exists
  today)
- `docs/rfcs/README.md` (RFC 0005, 0019, 0025, 0027, 0042 spine)
- `docs/rfcs/0027-resistance-calibration-acceptance.md` (full read —
  three-stage acceptance model, `ResistanceFitRecord` schema, minimum
  metric set, claim-gate inheritance from RFC 0025, conditions under which
  output may stop saying `uncalibrated`)
- `docs/design/kayak_hull_design_constraints.md` (kayak resistance regime
  / Fn ≲ 0.6 — used to anchor envelope/hull-class restriction)
- `docs/workflows/0018-deferred-backlog/QUEUE.md` (historical queue; 0023
  cross-reference for calibration dataset vetting)
- `docs/workflows/0050-decision-panel-research/OPERATOR_REPORT.md`
- `docs/workflows/0050-decision-panel-research/prompts/panel_vote.md`
- `striatum/0049-roadmap-reconciliation/final/FINAL_REVIEW.md`
- `striatum/0049-roadmap-reconciliation/integration/PATCH_SUMMARY.md`
- `striatum/0050-decision-panel-research/research/calibrated_resistance/RESEARCH.md`
- `kayakgen/eval/claims.py` lines 180-227 — verified
  `claim_allows_calibrated_prediction` and
  `claim_allows_final_design_fitness` conjunctions directly.
- `kayakgen/eval/resistance.py` lines 155-198 — verified default
  `resistance_curve()` emits `UNCALIBRATED_COMPARATIVE` with empty fixture
  IDs, null model version, empty fit metrics, null envelope, and the
  uncalibrated warning set.
- `kayakgen/eval/calibration.py` lines 17-87 — verified `SourceUse`
  literals and the `calibration_fixture` review-metadata invariant.

External claims (as cited in the research packet, accessed 2026-05-14;
not re-fetched in this session because `WebFetch` is not in the loaded
tool surface):

- ITTC Resistance Test procedure 7.5-02-02-01, rev. 05 — fixture metadata
  checklist supports making envelope/metadata fields mandatory.
- ITTC Resistance Uncertainty Analysis procedure 7.5-02-02-02 — bias /
  precision separation; residual-coefficient uncertainty larger than
  total-coefficient uncertainty supports Froude-band residual review.
- FDA CM&S credibility guidance (Nov 2023) — context-of-use framing
  supports envelope-bound calibrated wording.
- Edinburgh DataShare Pacific-canoe dataset (CC BY 4.0) — strong
  *validation-source* candidate; hull class is not sea-kayak
  calibration coverage.
- Gomes et al. 2018, Sports Biomechanics K1 study — measured kayak
  evidence narrow to sprint K1 conditions; publisher copyright limits
  rights, supports validation/citation pending review.
- scikit-learn RMSE / MAPE / R² docs — RMSE non-negative best-0; MAPE
  unstable near zero; R² non-symmetric and can be negative. Supports
  RMSE+MAPE-with-safeguards, not R² alone.
- MLflow Model Registry workflow + SemVer 2.0.0 — immutable versions
  with selector aliases; supports recording concrete `model_version` on
  every serialized fit and treating aliases as selector-time only.

## Sub-Agent Help

No sub-agents were spawned. All verification of code references, RFC
text, roadmap posture, and panel directory state was performed inline via
direct read-only inspection of the working tree.
