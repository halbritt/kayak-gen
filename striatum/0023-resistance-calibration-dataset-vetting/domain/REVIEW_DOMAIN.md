# Domain review - resistance dataset vetting

author: operator [self-declared: operator-domain-review]
run: run_6ca2095f019345e199943d5f46f0676f
job: review_domain
date: 2026-05-13
verdict: accept_with_findings

## Scope

Reviewed whether the candidate sources are appropriate for calibrating,
validating, verifying, or only contextualizing the current raw ITTC/Michell
resistance model for kayak-scale hulls.

## Findings

### D1 - Edinburgh is a strong slender-hull validation candidate, not a kayak calibration set

The Edinburgh dataset contains measured towing-tank force data and CAD for
three slender models, so it can help test raw resistance trend behavior against
real slender-hull experiments. It should not be used to calibrate
`calibrated_kayak_v1` because the tested hulls are Pacific-canoe-like
outrigger/multi-hull forms, not the single-hull touring/sea-kayak design space
in `docs/design/kayak_hull_design_constraints.md`.

Additional mismatch:

- the experimental context includes yaw/leeway and side-force behavior;
- fixed sink and trim conditions are not the same as kayak equilibrium load
  cases;
- hull sections and scale may bias viscous/form-factor behavior away from
  sea-kayak assumptions.

Classification: validation candidate only.

### D2 - Do not tune current raw Michell/ITTC output from this dataset

The current evaluator explicitly returns `raw_ittc_michell`,
`uncalibrated`, and `comparative_filter_only`. Tuning wave scale or friction
form factors from the Edinburgh dataset would produce a canoe-profile fit and
could be mistaken for a kayak calibration. If the dataset is later used
numerically, it should validate trend and unit plumbing first, or be attached
to a separate named profile such as a future canoe/slender-hull validation
profile.

Classification: calibration blocker.

### D3 - Prior K1 and Sea Kayaker conclusions remain unchanged

The K1 studies are closer in craft type but too narrow for touring/sea-kayak
calibration and lack clear reusable fixture rights. The Sea Kayaker table is
class-relevant but model-derived and rights-unclear. None should become
`calibration_fixture`.

Classification: no change from workflow 0012.

## Recommendation

Proceed with a small implementation that adds Edinburgh as a registry
`validation_candidate`, leaves all current resistance curves uncalibrated, and
updates RFC 0012 to record that an open measured validation dataset exists but
does not close the calibration source gate.
