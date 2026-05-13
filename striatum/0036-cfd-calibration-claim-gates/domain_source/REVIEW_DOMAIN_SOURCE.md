author: operator [self-declared: operator-0036-domain-source]
run: run_38b1b70956eb48eabbf39449375579ed
job: review_domain_source
date: 2026-05-13
verdict intent: accept_with_findings

# Domain source review - workflow 0036

## Scope

Reviewed whether the source language and current code contracts keep raw solver
output, validation-only datasets, empirical comparison, calibrated resistance,
and final design-fitness claims separate. Sources reviewed were the workflow
source list plus the local metadata and comparison code needed to understand
where those claims are surfaced.

## Summary

The domain direction is honest: the PRD, RFCs, source registry, resistance
metadata, and CFD job records all say the current outputs are raw,
uncalibrated, or validation-only rather than calibrated final predictions.
The gap is contract shape. RFC 0025 introduces a shared claim taxonomy, but the
implementation still uses older per-evaluator fields such as
`calibration_status`, `accepted_use`, and `result_semantics`. That is safe for
today's raw outputs, but not yet strong enough to prevent future validation
fixtures, fitted models, and final design scoring from being conflated.

## Findings

### DS-001 - Resistance output does not yet expose the RFC 0025 claim contract

Severity: high

RFC 0025 requires every resistance result to expose `claim_state`,
`accepted_uses`, fixture ID lists, model version, fit status, validity envelope,
and warnings, and says current RFC 0005 curves remain
`uncalibrated_comparative` (`docs/rfcs/0025-cfd-calibration-claim-gates.md`
lines 55-72). The current `ResistanceMetadata` instead exposes
`model_family`, `calibration_status`, optional calibration/source fields,
`accepted_use`, verification fixtures, quadrature, and warnings
(`kayakgen/eval/contract.py` lines 18-31). `resistance_curve` truthfully emits
`raw_ittc_michell`, `uncalibrated`, `comparative_filter`, and the
`not_final_performance_prediction` / `uncalibrated_no_validity_envelope`
warnings (`kayakgen/eval/resistance.py` lines 168-184), but it never emits the
claim state name `uncalibrated_comparative` or empty
`calibration_fixture_ids` / `validation_fixture_ids`.

Required action: add the RFC 0025 claim fields to resistance metadata. The
current raw ITTC/Michell curve should map to `claim_state =
"uncalibrated_comparative"`, `accepted_uses = ["comparative_filter"]`, empty
fixture ID lists, no fit status, no validity envelope, and the existing final
prediction warnings. Keep backward-compatible aliases only if needed.

### DS-002 - CFD records are raw/unvalidated, but use a local field name

Severity: medium

The CFD job code is careful not to overclaim: the module docstring says solver
physics are not validated or calibrated, `SolverProfile`, `CfdJobSpec`,
`CfdRunRecord`, and `SolverRawResult` all carry `result_semantics =
"raw_unvalidated"`, and unavailable or failed adapters report raw/unvalidated
wording (`kayakgen/eval/cfd/jobs.py` lines 45-92, 130-141, and 342-391).
That is semantically aligned with RFC 0025's `raw_unvalidated` state. However,
RFC 0025 also says resistance and CFD metadata cannot omit claim state and that
CLI/web/report/sweep metadata should use the same claim names or lossless
equivalents (`docs/rfcs/0025-cfd-calibration-claim-gates.md` lines 91-102).
`result_semantics` is close, but consumers looking for the shared
`claim_state` contract would not find the rest of the gate fields.

Required action: either rename this field to `claim_state` or provide a
documented lossless compatibility layer that also exposes the RFC 0025 fields:
accepted uses, empty calibration and validation fixture IDs, model version,
fit status, validity envelope, and warnings.

### DS-003 - Source registry cannot represent validation fixtures distinctly

Severity: medium

The current source registry language is conservative. It says records do not
calibrate current resistance output, classifies Edinburgh as a
`validation_candidate`, and labels K1 / Sea Kayaker sources as validation or
citation-only rather than calibration fixtures (`kayakgen/eval/calibration.py`
lines 1-13 and 40-128). That matches the prior source reviews. The state enum,
however, only allows `citation_only`, `validation_candidate`, and
`calibration_fixture` (`kayakgen/eval/calibration.py` line 13). RFC 0019's
fixture schema needs a separate `validation_fixture` state
(`docs/rfcs/0019-resistance-calibration-fixtures.md` lines 47-63), and RFC
0025 also names `calibration_fixture_candidate` before promotion to
`calibration_fixture` (`docs/rfcs/0025-cfd-calibration-claim-gates.md` lines
47-53 and 79-84).

Required action: extend source and fixture state vocabulary so a reviewed
dataset can move from source candidate to `validation_fixture` without becoming
a calibration fixture, and so plausible calibration sources can be recorded as
`calibration_fixture_candidate` until rights, extraction, hull-envelope,
measurement, uncertainty, and validity-envelope review is complete.

### DS-004 - Tests cover today's warnings, not the full forbidden-promotion matrix

Severity: medium

The existing tests assert useful current guardrails: resistance curves are
`uncalibrated`, comparative-only, and carry final-prediction warnings
(`tests/test_resistance.py` lines 113-128); the default source registry has no
calibration fixtures and Edinburgh remains validation-not-calibration
(`tests/test_resistance.py` lines 168-189); and CFD unavailable runs remain
`raw_unvalidated` (`tests/test_cfd_jobs.py` lines 249-255). RFC 0025 also asks
for one negative test for each forbidden overclaim: raw CFD as validated,
validation fixture as calibration fixture, uncalibrated resistance as
calibrated, and calibrated resistance as final design fitness
(`docs/rfcs/0025-cfd-calibration-claim-gates.md` lines 103-105). The reviewed
test files do not yet cover that full promotion matrix.

Required action: add focused negative tests around the shared claim contract
once DS-001 through DS-003 land. The tests should prove that validation-only
fixtures cannot remove uncalibrated warnings, raw CFD cannot become validated
drag, uncalibrated resistance cannot become a calibrated model, and calibrated
resistance cannot become final design fitness without the future scoring RFC.

## Gate recommendation

Accept with findings. The reviewed language is truthful enough to proceed, but
the implementation should land the shared claim-state contract before any real
fixture adapter, fitted model, CFD success path, or design-fitness scoring work
is allowed to build on these records.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 pytest -q tests/test_resistance.py tests/test_cfd_jobs.py -p no:cacheprovider` could not run because `pytest` is not installed in this worktree environment.
