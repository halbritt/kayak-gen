---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-005
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14
run: run_dc0a506896094745b380fd3ad2535d59
session: sess_b1ce9839de80414a913bfde4278d8d5c
job: job_run_dc0a506896094745b380fd3ad2535d59_panel_calibrated_resistance_codex
lease: lease_c1677c3f88704302ad39fb10e1390a01

# Vote - Calibrated Resistance Promotion

Vote: Option A - Preserve Current No-Promotion Gate.

## Decision Sentence

Keep kayak-gen resistance output in the `uncalibrated_comparative` claim state
and forbid calibrated-prediction, final-prediction, default optimization, or
design-fitness wording until a later accepted-fit workflow records at least one
accepted kayak-envelope calibration fixture, an immutable concrete model
version, persisted accepted fit metrics and residuals, a validity envelope that
contains the evaluated hull and speed, and a passing
`claim_allows_calibrated_prediction` check; record the Option B gate shape as
future target architecture, not as authority to promote current sources or fit
current curves.

## Evidence

The local product boundary already answers the immediate promotion question.
The PRD says current resistance combines ITTC-57 viscous resistance with
Michell wave resistance as an exploratory analytical screening filter, not a
calibrated final prediction (`docs/PRD.md:37-42`). It keeps calibrated
resistance prediction in roadmap scope only after licensed, relevant
kayak-scale validation fixtures exist (`docs/PRD.md:51-57`). Its 25 percent
match over Fn 0.25-0.50 is a calibration-roadmap criterion, not a permission to
claim calibration before evidence exists (`docs/PRD.md:86-91`).

The current roadmap is stricter and should govern this decision. Resistance
output is `uncalibrated_comparative`, not a calibrated model, final prediction,
design-fitness score, or default optimization objective (`docs/ROADMAP.md:34-40`).
Batch F says the next work is source review, source-use mapping, validation
fixture ingest only if rights and extraction pass, calibration fixture ingest
only after a kayak-envelope measured source is accepted, and fitting/wording
only in a separate accepted-fit workflow (`docs/ROADMAP.md:166-185`). Its exit
criteria require accepted fit evidence, calibration fixture IDs, fit metrics,
and a validity envelope containing the evaluated hull and speed before current
curves stop carrying uncalibrated warnings (`docs/ROADMAP.md:187-189`).

RFC 0027 is already the claim-gate authority. Candidate sources do not provide
validation evidence, calibration fixture IDs, or calibrated-model evidence;
validation fixtures can exercise parsers, reports, adapter behavior, and
holdout metrics, but cannot fit the default model or remove uncalibrated
warnings; calibration fixtures require explicit fixture metadata and review
status, and loading rows is insufficient (`docs/rfcs/0027-resistance-calibration-acceptance.md:36-72`).
The initial metric family must include force RMSE and MAPE, Froude-band bias
where enough rows exist, monotonicity and non-negative checks, and holdout or
validation-fixture error when validation evidence is declared
(`docs/rfcs/0027-resistance-calibration-acceptance.md:90-95`). The canonical
passing status is `accepted_fit`, and validation fixtures, legacy aliases, or
non-empty metrics alone must not satisfy calibrated prediction
(`docs/rfcs/0027-resistance-calibration-acceptance.md:97-106`). Resistance
output may stop saying uncalibrated only when the selected curve metadata
satisfies `claim_allows_calibrated_prediction`, references an accepted
calibration fixture, records a named model version with accepted fit,
persists metrics and residuals, passes threshold tests, and is inside the
accepted envelope (`docs/rfcs/0027-resistance-calibration-acceptance.md:108-122`).

RFC 0042 confirms that the next resistance-calibration successor is source
review and fixture promotion, not model fitting or output promotion. A source
may become a calibration fixture only when review explicitly accepts rights,
measured resistance or drag data, kayak-envelope applicability, displacement
and speed/Froude ranges, extraction method, uncertainty treatment, row schema,
unit normalization, and intended fit parameters or a statement that fitting is
deferred. Parser success and plausible residuals are not promotion
(`docs/rfcs/0042-resistance-calibration-fixture-successor.md:135-153`).
Current resistance curves remain `uncalibrated_comparative`; validation
fixtures may support reports, holdout metrics, or parser tests, but must not be
listed as calibration fixture IDs for an accepted fit
(`docs/rfcs/0042-resistance-calibration-fixture-successor.md:189-199`).
RFC 0042 also says no current source is promoted by that RFC alone and
calibration fixture promotion cannot be inferred from row loading, parser
success, or residual metrics (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:201-220`).

The implementation matches the documentation. The default resistance curve
sets `claim_state=UNCALIBRATED_COMPARATIVE`, has no calibration fixture IDs, no
validation fixture IDs, no model version, no fit status, no fit metrics, no
validity envelope, and emits uncalibrated warnings
(`kayakgen/eval/resistance.py:164-190`). The calibrated-prediction helper
requires `calibrated_model`, `final_prediction` in accepted uses, calibration
fixture IDs, model version, a canonical passing fit status, fit metrics,
validity envelope, and no uncalibrated warning codes
(`kayakgen/eval/claims.py:195-210`). Final design fitness is a separate helper
and explicitly has no current satisfying output (`kayakgen/eval/claims.py:213-227`).
The source registry says its records do not imply calibrated output and has no
accepted calibration fixture; Edinburgh is a validation candidate, Sea
Kayaker-derived tables are citation-only, Gomes and Tzabiras are validation
candidates with sprint-K1 and rights/envelope limitations, and the MDPI article
is modeling context only (`kayakgen/eval/calibration.py:1-20`,
`kayakgen/eval/calibration.py:107-205`).

The calibrated-resistance research packet correctly recommends this posture:
choose Option A now, record Option B as the desired future gate shape, and keep
the PRD's 25 percent Fn 0.25-0.50 criterion only as an upper-bound target until
source uncertainty, row coverage, and holdout options are known
(`striatum/0050-decision-panel-research/research/calibrated_resistance/RESEARCH.md:114-146`).

My independent external check, accessed on 2026-05-14, supports an
evidence-first gate rather than immediate promotion:

- ITTC resistance-test procedure 7.5-02-02-01 says a resistance-test report
  should include model identity, loading condition, turbulence stimulation,
  scale, dimensions, hydrostatics, tank particulars, water properties, form
  factor/correlation allowance, and per-speed resistance plus sinkage/trim
  data; it also says uncertainty analysis should be performed
  (https://www.ittc.info/media/11780/75-02-02-01.pdf).
- ITTC uncertainty procedure 7.5-02-02-02 separates bias, precision, and total
  uncertainty for total and residuary resistance coefficients and demonstrates
  that residual-coefficient uncertainty can be much larger than total
  resistance uncertainty (https://ittc.info/media/2021/75-02-02-02.pdf).
- FDA CM&S credibility guidance ties predictive credibility to a specific
  context of use and states that the context of use can be narrower than the
  model's broader capability, which supports envelope-gated wording rather than
  global "calibrated" claims (https://www.fda.gov/media/154985/download).
- Edinburgh DataShare records an open dataset of raw towing-tank hydrodynamic
  forces and CAD models for three slender Pacific-canoe-like hulls, which is
  useful validation-source evidence but not enough for a general sea-kayak
  calibration fixture by itself (https://datashare.ed.ac.uk/handle/10283/4772).
- Gomes et al. is a peer-reviewed single-seat kayak drag study using simulated
  65, 75, and 85 kg kayaker weights, but the metadata records publisher
  copyright and the envelope is sprint-K1 specific
  (https://researchconnect.suny.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/).
- Tzabiras et al. publishes measured K1 resistance rows over Fn 0.035-0.730,
  but it is an Olympic K1 flat-water racing kayak load case, not general
  sea-kayak coverage, and no open fixture license was established in my check
  (https://thesportjournal.org/article/experimental-and-numerical-study-of-the-flow-past-the-olympic-class-k-1-flat-water-racing-kayak-at-steady-speed/).
- scikit-learn's MAPE documentation warns that values can become arbitrarily
  large near zero-valued targets, which supports keeping MAPE behind a
  declared low-force safeguard
  (https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_percentage_error.html).
- MLflow model-registry documentation distinguishes concrete model versions
  from aliases and notes that aliases can be reassigned independently; SemVer
  says released version contents must not be modified. Together they support
  persisting immutable concrete resistance model versions, not only `latest`,
  `default`, or `champion` aliases
  (https://mlflow.org/docs/latest/ml/model-registry/workflow/,
  https://semver.org/).

## Why Rejected Alternatives Lose

Option B - calibrated prediction gate, no design fitness - is the correct
future shape, but it loses as the immediate decision because no current source
is an accepted kayak-envelope calibration fixture, no accepted fit thresholds
exist, and the rights/envelope state of the best known sources is mixed. If
adopted now as more than future architecture, it would turn a gate description
into a premature promotion signal.

Option C - comparative calibration for ranking only - may become useful, but it
does not match the current `final_prediction` accepted-use gate. It would need
a new accepted-use value, explicit rank/order metrics across measured hulls,
and UI/report language such as calibrated comparative ranking. It must not
silently reuse absolute-prediction wording.

Option D - validated design fitness - loses outright for this workflow.
Design-fitness claims require more than calibrated resistance: they need
hydrostatics, design constraints, high-angle stability availability, user
objective semantics, uncertainty, and warning policy. Current high-angle
stability remains unavailable for generated kayaks, and RFC 0027 explicitly
keeps calibrated resistance separate from final design fitness.

An immediate numeric threshold also loses. The PRD's 25 percent over Fn
0.25-0.50 is a useful upper-bound roadmap criterion, but choosing final
thresholds before selecting an accepted source would ignore fixture
uncertainty, row count, speed distribution, hull-class coverage, and holdout
structure.

## Implementation Gates

Before any calibrated wording, fitted default model, optimization default, or
design-fitness use:

1. Add an RFC 0042-style source-review packet/checklist for rights, source
   type, measured quantity, units, hull envelope, speed/Froude range,
   displacement/load, trim/sinkage, extraction method, uncertainty, verdict,
   fixture ID/version, and non-promotion reasons.
2. Preserve the five runtime `SourceUse` values. Keep `rejected` as review
   metadata only, never as a runtime fixture source-use value.
3. Promote validation fixtures only after rights, units, extraction metadata,
   rows, and warnings are complete. Validation fixtures may support parser,
   report, and holdout checks, but cannot fit the default model or remove
   uncalibrated warnings.
4. Promote a calibration fixture only after review accepts rights for
   machine-readable derived rows, measured resistance or drag data, kayak
   envelope applicability, displacement/load and speed/Froude coverage,
   uncertainty treatment, unit normalization, fixture ID/version, accepted use,
   validity envelope, and intended fit parameters.
5. Add an immutable fit-record artifact with concrete `model_family`,
   `model_version`, code revision, data checksums, calibration and validation
   fixture IDs/versions, fitted parameters, residual refs, metrics, warnings,
   review date, and validity envelope.
6. Require at minimum force RMSE, normalized RMSE, MAPE with low-force row
   exclusions, mean and Froude-band bias, max absolute error, max percent error,
   monotonicity and non-negative checks, and holdout or validation-fixture error
   when evidence exists.
7. Implement an envelope membership checker before any wording branch. Out of
   envelope must keep the curve available only as raw comparative fallback with
   explicit warnings.
8. Route CLI, web, report, sweep, and comparison wording through
   `claim_allows_calibrated_prediction` plus the envelope membership check.
   Do not add a resistance-specific parallel claim helper.
9. Keep `claim_allows_final_design_fitness` separate and unsatisfied until a
   future design-fitness RFC lands across resistance, hydrostatics, stability,
   design constraints, objectives, and uncertainty.

No-claims language that must remain in force: current resistance curves are
raw analytical comparative filters; no current source is an accepted
calibration fixture; validation fixtures are not calibration fixtures;
candidate fits are not calibrated predictions; accepted calibrated prediction
is allowed only inside its named model-version envelope; out-of-envelope curves
fall back to raw comparative wording; resistance calibration alone is not final
prediction, default optimization fitness, seaworthiness, safety, high-angle
stability, CFD validation, or final design fitness.

Confidence: high.
