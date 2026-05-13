author: operator [self-declared: operator-0036-ops]

# Ops review - workflow 0036 CFD calibration claim gates

run: run_38b1b70956eb48eabbf39449375579ed
job: review_ops
date: 2026-05-13
verdict_intent: accept_with_findings

## Scope Read

Read `AGENTS.md`, workflow 0036 `SOURCES.md`, `prompts/review_ops.md`, RFCs
0005, 0012, 0015, 0017, 0019, and 0025, plus `kayakgen/eval/cfd/jobs.py`,
`kayakgen/eval/resistance.py`, `kayakgen/eval/calibration.py`,
`tests/test_cfd_jobs.py`, and `tests/test_resistance.py`. I also checked the
CLI, comparison-report, sweep, and web-controller surfaces because the prompt
explicitly asks for CLI/web/report wording and forbidden-overclaim coverage.

Focused test commands attempted:

```text
python -m pytest tests/test_cfd_jobs.py tests/test_resistance.py tests/test_compare.py tests/test_web.py
python3 -m pytest tests/test_cfd_jobs.py tests/test_resistance.py tests/test_compare.py tests/test_web.py
```

Result: not executed in this environment. `python` is not on PATH, and
`python3 -m pytest` reports `No module named pytest`.

## Positive Coverage

Current raw paths are conservative. Resistance curves still emit
`calibration_status="uncalibrated"`, `accepted_use=["comparative_filter"]`, and
the final-prediction/no-validity-envelope warnings
(`kayakgen/eval/resistance.py:168`). CFD job specs, run records, solver
profiles, and adapter results are typed as `raw_unvalidated`
(`kayakgen/eval/cfd/jobs.py:40`, `kayakgen/eval/cfd/jobs.py:54`,
`kayakgen/eval/cfd/jobs.py:74`, `kayakgen/eval/cfd/jobs.py:131`). Dispatch
also rejects forged watertight `cfd_ready` manifests unless a closed-volume
validator accepts profile-scoped diagnostic evidence (`tests/test_cfd_jobs.py:130`).

The report layer has useful exploratory safeguards: explicit resistance
objectives become `exploratory_frontier`, require accepted-use provenance, and
surface candidate warnings when only raw comparative resistance is present
(`tests/test_compare.py:167`). CLI CFD prepare/status/run paths echo that CFD
results are raw and unvalidated (`kayakgen/cli/main.py:178`,
`kayakgen/cli/main.py:205`, `kayakgen/cli/main.py:228`).

## Findings

### O-001 - Result schemas do not yet expose the RFC 0025 claim contract

- Severity: high
- File(s): `kayakgen/eval/contract.py`, `kayakgen/eval/cfd/jobs.py`
- Statement: RFC 0025 requires every drag/resistance/residual/design-fitness
  result record to expose `claim_state`, `accepted_uses`,
  `calibration_fixture_ids`, `validation_fixture_ids`, `model_version`,
  `fit_status`, `validity_envelope`, and `warnings`
  (`docs/rfcs/0025-cfd-calibration-claim-gates.md:55`). Current resistance
  metadata still uses the older `model_family`, `calibration_status`, and
  `accepted_use` fields without `claim_state`, fixture IDs, fit status, model
  version, or a single validity envelope (`kayakgen/eval/contract.py:13`).
  Current CFD records use `result_semantics="raw_unvalidated"` but likewise do
  not carry accepted uses, fixture IDs, fit status, validity envelope, or claim
  warnings as first-class fields (`kayakgen/eval/cfd/jobs.py:54`,
  `kayakgen/eval/cfd/jobs.py:74`, `kayakgen/eval/cfd/jobs.py:131`).
- Required action: add a shared claim metadata model or a lossless equivalent
  to resistance and CFD result records. Populate current analytical resistance
  as `uncalibrated_comparative` and current CFD as `raw_unvalidated`. Add JSON
  round-trip and omission tests proving claim state cannot be absent.

### O-002 - Report gating can trust self-declared final-prediction fields

- Severity: high
- File(s): `kayakgen/search/compare.py`, `tests/test_compare.py`
- Statement: Comparison reports mark `Rt_N_last` accepted when
  `calibration_status != "uncalibrated"` and `"final_prediction"` appears in
  `accepted_use` (`kayakgen/search/compare.py:179`). That is stronger than RFC
  0025 permits because the current schema has no calibration fixture IDs,
  accepted fit status, model version, or validity envelope to verify before a
  resistance metric becomes accepted provenance. The existing report tests
  block raw comparative resistance, but they do not cover a forged or premature
  calibrated/final-prediction metadata record (`tests/test_compare.py:167`).
- Required action: gate accepted report provenance on the full claim contract:
  `claim_state="calibrated_model"`, nonempty accepted calibration fixture IDs,
  passed fit status/metrics, model version, and an applicable validity envelope.
  Add negative tests for uncalibrated resistance as calibrated, validation
  fixture as calibration fixture, calibrated metadata without fixture/fit
  evidence, and calibrated resistance as final design fitness.

### O-003 - Calibration source records can name calibration fixtures without fixture-review fields

- Severity: medium
- File(s): `kayakgen/eval/calibration.py`, `tests/test_resistance.py`
- Statement: The default registry correctly avoids calibration fixtures, but
  the schema permits `intended_use="calibration_fixture"` while requiring only
  source-level fields such as title, URL, rights status, extraction status, and
  hull class (`kayakgen/eval/calibration.py:13`, `kayakgen/eval/calibration.py:16`).
  RFC 0025 promotion requires explicit review metadata, fixture IDs, measured
  quantity, rights status, extraction status, hull envelope, and measured
  quantity before calibration claims may advance
  (`docs/rfcs/0025-cfd-calibration-claim-gates.md:96`). Current tests assert
  the default registry has no calibration fixtures, but not that an attempted
  calibration fixture without review fields is rejected (`tests/test_resistance.py:157`).
- Required action: split candidate source records from calibration fixture
  manifests, or add validators that require fixture review metadata, measured
  quantity/units, validity ranges, and explicit promotion evidence when
  `intended_use="calibration_fixture"`. Add negative tests that validation-only
  sources cannot remove uncalibrated resistance warnings or become calibration
  fixtures by changing one enum field.

### O-004 - Web compact metrics show resistance numbers without claim wording

- Severity: medium
- File(s): `kayakgen/ui/web/controllers.py`, `kayakgen/ui/web/app.py`,
  `tests/test_web.py`
- Statement: The analysis view includes resistance warnings and metadata
  (`kayakgen/ui/web/controllers.py:141`), but the compact metrics path returns
  and displays `Rv_N`, `Rw_N`, and `Rt_N` without any resistance claim metadata
  (`kayakgen/ui/web/controllers.py:74`, `kayakgen/ui/web/app.py:178`). The only
  warnings appended there are advisory design warnings, not
  `comparative_filter_only` or `not_final_performance_prediction`
  (`kayakgen/ui/web/app.py:190`). The web test checks the analysis lines include
  `comparative_filter_only`, but not the always-visible compact metrics panel
  (`tests/test_web.py:81`).
- Required action: carry resistance claim metadata through `metrics_from_state`
  and render a short compact warning such as `Resistance: raw comparative
  filter, not final prediction` beside the at-speed drag numbers. Add a web
  unit test for the compact metrics text.

## Recommendation

Accept the safe-now raw behavior, but keep the workflow findings open until the
claim contract is first-class across schemas and report/web gates. The current
implementation avoids today's obvious overclaims, yet it still relies on
inference from legacy fields in the places future calibrated/validated claims
will need hard gates.
