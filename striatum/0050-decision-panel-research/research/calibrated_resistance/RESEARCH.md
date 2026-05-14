---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: researcher-codex-gpt-5.5-003
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: research
date: 2026-05-14

# Calibrated Resistance Promotion Research

## Decision Question

What fit metrics, validity envelope, model-versioning rules, and wording threshold must be accepted before kayak-gen may describe resistance output as a calibrated prediction or use it in a design-fitness claim?

## Local Project Constraints

Current resistance output is explicitly an exploratory analytical screening filter, not a calibrated final prediction (`docs/PRD.md:38-42`). The PRD keeps calibrated resistance prediction in roadmap scope only after licensed, relevant kayak-scale validation fixtures exist (`docs/PRD.md:51-57`).

The roadmap no-claims rules are stronger: resistance output is `uncalibrated_comparative`, not a calibrated model, final prediction, design-fitness score, or default optimization objective (`docs/ROADMAP.md:34-40`). Batch F says current curves keep `uncalibrated_comparative` warnings until a named model version has accepted fit evidence, calibration fixture IDs, fit metrics, and a validity envelope that contains the evaluated hull and speed (`docs/ROADMAP.md:166-189`).

RFC 0027 is the current claim-gate authority. It requires fit metadata with `model_version`, `fit_status`, calibration and validation fixture IDs, fitted parameters, metrics, residuals, a validity envelope, and warnings (`docs/rfcs/0027-resistance-calibration-acceptance.md:74-88`). Initial metrics must include force RMSE, MAPE over the fitted speed range, Froude-band bias where enough rows exist, monotonicity/non-negative checks, and holdout or validation-fixture error if a validation fixture is declared (`docs/rfcs/0027-resistance-calibration-acceptance.md:90-95`). It also says validation fixtures, legacy aliases, or non-empty metrics alone must not satisfy the calibrated-prediction gate (`docs/rfcs/0027-resistance-calibration-acceptance.md:97-122`).

The implementation matches that boundary. `claim_allows_calibrated_prediction` currently requires `claim_state == "calibrated_model"`, `final_prediction` in accepted uses, non-empty calibration fixture IDs, non-empty model version, canonical `accepted_fit`, non-empty fit metrics, non-null validity envelope, and no uncalibrated warning codes (`kayakgen/eval/claims.py:195-210`). `claim_allows_final_design_fitness` is separate and no current output satisfies it (`kayakgen/eval/claims.py:213-227`). The default `resistance_curve()` still emits `uncalibrated_comparative`, empty fixture/model/fit fields, no validity envelope, and uncalibrated warnings (`kayakgen/eval/resistance.py:165-189`).

Current source records are not enough to promote. The registry explicitly says records describe candidate sources and do not imply calibrated output (`kayakgen/eval/calibration.py:1-5`). It has no calibration fixtures; Edinburgh Pacific-canoe data is a validation candidate, Sea Kayaker-derived tables are citation-only, and Gomes/Tzabiras K1 records are validation candidates with fixture-rights or envelope limits (`kayakgen/eval/calibration.py:107-185`).

RFC 0042 narrows the next work to source review and fixture promotion, not fitting. A source-review packet must record rights, measurement type, units, hull class, speed/Froude range, trim/sinkage, extraction method, uncertainty, and verdict (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:86-103`). Calibration fixture promotion requires accepted rights, measured drag/resistance data, kayak-envelope applicability, load and speed/Froude ranges, extraction and uncertainty treatment, row schema, unit normalization, and a named fixture ID/version/envelope/reason; parser success or plausible residuals are not promotion (`docs/rfcs/0042-resistance-calibration-fixture-successor.md:135-153`).

## External Evidence

External sources were accessed on 2026-05-14.

| Source | Claim supported |
| --- | --- |
| [ITTC Resistance Test, procedure 7.5-02-02-01, revision 05](https://www.ittc.info/media/11780/75-02-02-01.pdf) | A resistance-test report should include model identity, loading condition, turbulence stimulation, scale, main dimensions, hydrostatics, wetted surface, tank particulars, water properties, form factor/correlation allowance, and per-speed resistance plus sinkage/trim data. This supports making fixture metadata and envelope fields mandatory, not optional. |
| [ITTC Resistance Uncertainty Analysis example, procedure 7.5-02-02-02](https://ittc.info/media/2021/75-02-02-02.pdf) | ITTC uncertainty treatment separates bias and precision and reports uncertainty for total and residual resistance coefficients; the example shows residual coefficient uncertainty much larger than total coefficient uncertainty. This supports uncertainty-aware acceptance metrics and Froude-band residual review. |
| [FDA CM&S credibility guidance, November 2023](https://www.fda.gov/media/154985/download) | For physics-based models, credibility is trust in predictive capability for a context of use, and adequacy should be judged against the question, model risk, evidence, credibility goals, and pre-specified accuracy or agreement criteria. This supports tying calibrated wording to an explicit context-of-use/validity envelope rather than global claims. |
| [Edinburgh DataShare Pacific-canoe dataset](https://datashare.ed.ac.uk/handle/10283/4772) and [license text](https://datashare.ed.ac.uk/bitstream/handle/10283/4772/license_text?isAllowed=y&sequence=3) | The dataset includes raw towing-tank hydrodynamic forces and CAD models for three slender hulls, with CC BY 4.0 license text. It is strong validation-source evidence, but its hull class remains Pacific-canoe-like rather than sea-kayak calibration coverage. |
| [Gomes et al. 2018, Sports Biomechanics record](https://researchconnect.suny.edu/en/publications/effect-of-wetted-surface-area-on-friction-pressure-wave-and-total/) | This peer-reviewed K1 kayak study used experimental passive-drag data at simulated 65/75/85 kg kayaker weights and reports drag-component findings. It is relevant measured kayak evidence, but it is narrow to sprint K1 conditions and publisher copyright, so it supports validation/citation unless rights and envelope review pass. |
| [scikit-learn RMSE docs](https://scikit-learn.org/1.6/modules/generated/sklearn.metrics.root_mean_squared_error.html), [MAPE docs](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.mean_absolute_percentage_error.html), and [R2 docs](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.r2_score.html) | RMSE is non-negative with best value 0; MAPE is a relative loss but can become arbitrarily large near zero-valued targets; R2 can be negative and is not symmetric. This supports using RMSE/NRMSE and MAPE together, with MAPE safeguards and not relying on R2 alone. |
| [MLflow Model Registry workflow docs](https://www.mlflow.org/docs/latest/ml/model-registry/workflow/) and [Semantic Versioning 2.0.0](https://semver.org/) | Maintained model registries distinguish concrete model versions from aliases/tags, while SemVer requires immutable released versions and a clear public API. This supports immutable resistance model versions, optional aliases only at selection time, and recorded fit/source lineage in every serialized result. |

## Fit Metrics

The next accepted-fit workflow should require both fitted-data and out-of-sample or validation-fixture metrics. A single in-sample residual number is not enough to remove `uncalibrated` wording.

Recommended minimum metric record:

- `force_rmse_N`: primary dimensional error metric, computed over total measured resistance or drag force rows.
- `force_nrmse_pct`: RMSE normalized by mean measured force or by a fixture-declared reference force, so different speed/load fixtures can be compared.
- `force_mape`: useful user-facing percent error, but compute only where measured force is above a declared epsilon; otherwise report `mape_excluded_low_force_rows`.
- `mean_bias_pct` and `bias_pct_by_fn_band`: signed bias overall and by low/mid/high Froude bands.
- `max_abs_error_N` and `max_abs_pct_error`: catches speed-local failures hidden by averages.
- `nonnegative_resistance_passed` and `monotonic_speed_passed`: current physical sanity checks should remain gates.
- `holdout_rmse_N`, `holdout_mape`, or `validation_fixture_error`: required when enough rows or an accepted validation fixture exists.
- `rank_correlation` or pairwise ordering accuracy only if the claim is comparative ranking across multiple hulls. This metric should not substitute for force-error metrics when the wording says prediction.

Component metrics should be conditional. If a source measures only total resistance, fit total resistance and do not claim calibrated viscous/wave decomposition. If a source includes component decomposition or a defensible method for deriving it, record component residuals separately and state which model parameters were fitted.

## Validity Envelope

The envelope should be the intersection of project design scope and the accepted fixture coverage, not the whole kayak-gen parameter space. It should be serialized in every accepted fit and checked for each evaluated hull/speed before calibrated wording appears.

Recommended envelope fields:

- speed and `Fn` ranges, with the initial project target likely no broader than the PRD/RFC calibration range around Fn 0.25-0.50;
- hull class and allowed preset family, e.g. sea kayak, performance sea kayak, surfski, or sprint K1, with no cross-class promotion by default;
- length, waterline beam, `L/B_wl`, draft, displacement/load, and Cp ranges;
- load case and trim/sinkage assumptions, including whether tests were fixed sink/trim or free trim;
- water properties, Reynolds-range notes, turbulence stimulation or transition assumptions where known;
- fitted parameter list, e.g. ITTC form factor, Michell wave scale, total-resistance residual correction;
- excluded cases and fallback rule.

Out of envelope must be a hard wording gate: keep the curve available as raw comparative output, preserve warnings, and do not list the result as calibrated prediction even if the selected model version has an accepted fit elsewhere.

## Model Versioning Rules

Use immutable versions for calibrated resistance models. A serialized resistance result should never contain only an alias such as `latest`, `default`, or `champion`; it should record the concrete `model_version` and enough lineage to reproduce the fit.

Recommended fields:

- `model_family`, e.g. `raw_ittc_michell` or future `calibrated_ittc_michell_kayak`;
- immutable `model_version`, preferably SemVer-compatible plus optional build metadata, e.g. `1.0.0+fit.<short_hash>`;
- algorithm code revision, fit code revision, fitted parameter values, calibration fixture IDs and versions, validation fixture IDs and versions, source-review IDs, data checksums, fit metrics, residual artifact reference, validity envelope, and accepted review date;
- optional selector alias in configuration, but the generated curve must resolve and persist the immutable version.

Version bump guidance:

- Major: equation family, fitted-parameter meaning, fixture set, acceptance thresholds, or envelope semantics change in a way that can change calibrated claims.
- Minor: backward-compatible envelope extension, additional validation evidence, or non-breaking metadata addition.
- Patch: bug fix or recomputation that preserves the same fixture set, envelope, thresholds, and claim semantics. Do not mutate an already published fit artifact in place.

## Wording Thresholds

The wording gate should be stricter than the fit calculation. Producing residuals is not enough.

Allowed wording matrix:

| State | Required evidence | Allowed wording |
| --- | --- | --- |
| Current default | `uncalibrated_comparative`, no accepted fit, no calibration fixture IDs, no envelope | "Raw analytical resistance estimate" or "comparative screening filter"; keep "not a final performance prediction." |
| Candidate fit | `candidate_fit` or `rejected_fit`, even with metrics | "Candidate calibration fit under review"; do not use for prediction, default ranking, or user-facing performance claims. |
| Accepted calibrated prediction, in envelope | `claim_allows_calibrated_prediction` passes, envelope membership check passes, residuals/metrics are persisted | "Calibrated resistance prediction within [model_version] envelope"; show model version, source IDs, fit error summary, and warning scope. |
| Accepted fit, out of envelope | accepted fit exists but hull/speed/load fails envelope | "Outside calibration envelope; using raw comparative fallback" or equivalent; keep uncalibrated/out-of-envelope warning. |
| Design fitness | future `validated_design_fitness` gate plus a separate RFC combining calibrated resistance with hydrostatics, stability availability, constraints, and user objectives | Not allowed from resistance calibration alone. |

If a panel wants an initial numeric calibrated-prediction bar before a first source is selected, the safest provisional ceiling is the existing product criterion: do not allow calibrated prediction unless published kayak-scale measured data is matched within 25% over the Fn 0.25-0.50 range. That should be treated as an upper bound, not a final target. The accepted-fit workflow should refine it using source uncertainty, row count, speed distribution, fixture hull coverage, and holdout behavior.

## Viable Options

### Option A - Conservative Default: Preserve Current No-Promotion Gate

Do not choose numeric fit thresholds in workflow 0050. Decide only that calibrated wording remains blocked until RFC 0042 source review accepts a kayak-envelope calibration fixture and a later accepted-fit workflow defines thresholds, envelope checks, and versioning.

This is the lowest-risk option and matches the current roadmap. It gives the next workflow a clean job: review sources and fixture promotion without implying calibration.

### Option B - Calibrated Prediction Gate, No Design Fitness

Adopt the gate shape now and permit a later workflow to use "calibrated resistance prediction" only when:

- at least one kayak-envelope `calibration_fixture` is accepted with rights, measured resistance rows, units, extraction, uncertainty, fixture ID/version, and envelope;
- a named model version has `accepted_fit`;
- RMSE/NRMSE, MAPE with low-force safeguards, bias by Froude band, max error, monotonicity, non-negative checks, and holdout/validation errors pass pre-declared thresholds;
- the evaluated hull and speed are inside the envelope;
- every output records concrete model version and fixture IDs.

This option can support calibrated prediction within a narrow envelope. It still cannot support design fitness.

### Option C - Comparative Calibration For Ranking Only

Allow a future model to be described as calibrated for comparative ranking, not absolute force prediction, if rank/order metrics across multiple measured hulls pass while force-error metrics remain too weak.

This may match the product's early design-loop use, but it does not fit the current `final_prediction` claim name cleanly. It would need a new accepted-use value and explicit UI copy such as "calibrated comparative ranking," otherwise users will read it as absolute performance prediction.

### Option D - Validated Design Fitness

Defer entirely. A design-fitness claim should require a separate RFC and gate over calibrated resistance, hydrostatics, real high-angle stability availability, design constraints, user objective weights, uncertainty, and warnings. Resistance calibration alone must not set `validated_design_fitness`.

## Recommendation

Choose Option A for the current decision: no calibrated resistance or design-fitness wording yet, and no final numeric acceptance threshold before a kayak-envelope source is accepted. The evidence clearly supports preserving the existing gate because the current source registry has no accepted calibration fixture, source rights/envelopes remain mixed, and the implementation already has a strict claim helper that blocks premature promotion.

Also record Option B as the desired future gate shape. The panel can provisionally retain the PRD's 25% match-over-Fn-0.25-0.50 criterion as an upper-bound target for calibrated prediction, but the accepted-fit workflow should set final thresholds only after source uncertainty, row coverage, and holdout options are known.

## Risks And Unknowns

- There may be no licensable measured sea-kayak dataset broad enough to fit the default design envelope; K1 and Pacific-canoe sources are useful but narrow or out-of-envelope.
- A single hull/source can produce plausible force residuals while failing design-space generalization. Holdout data or multiple hulls matter.
- MAPE is intuitive but unstable near zero force; RMSE alone can hide relative high-speed or low-speed bias.
- ITTC-style uncertainty handling shows residual resistance uncertainty can be much larger than total-resistance uncertainty; acceptance thresholds should consider source uncertainty and speed bands.
- Current Michell implementation has known sharp-ended kayak limitations; calibration may hide numerical artifacts unless the fit records quadrature/settings and model-family assumptions.
- "Calibrated" in UI copy will be over-read. Wording must always include model version, envelope, and fallback warnings.
- Design-fitness claims require stability and objective semantics that are not available today.

## Implementation Gates Before Any Work

- Complete RFC 0042-style source-review packets before ingesting or promoting fixture rows.
- Preserve the five current `SourceUse` runtime values; keep `rejected` as a review outcome, not a runtime fixture state.
- Add fixture row schema only after rights, extraction, measured quantity, units, uncertainty, hull envelope, and review verdict are complete.
- Add an immutable fit-record artifact with metrics, residuals, fixture IDs, code/data hashes, model version, and validity envelope.
- Implement an envelope membership checker before any calibrated wording branch.
- Route CLI/web/report wording through `claim_allows_calibrated_prediction` plus envelope membership.
- Keep `claim_allows_final_design_fitness` separate and unsatisfied until a future design-fitness RFC lands.

## Sub-Agent Help

No spawned sub-agents were used. I used parallel read-only local inspections and current external primary-source research.
