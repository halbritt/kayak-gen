author: operator [self-declared: operator-0036-traceability]

# Traceability review - workflow 0036

run: run_38b1b70956eb48eabbf39449375579ed
job: review_traceability
verdict_intent: accept_with_findings

## Scope

Reviewed RFC 0025 against the existing resistance metadata, CFD dispatch
records, calibration source registry, CLI/web wording, user guide, RFC index,
and changelog language. The review objective was not to require real CFD or a
calibrated model; it was to check whether current raw outputs can still be
mistaken for validated CFD, calibrated resistance, or final design fitness.

## Traceability map

- RFC 0025 defines claim states `raw_unvalidated` and
  `uncalibrated_comparative` for today's CFD dispatch and analytical resistance
  outputs, and requires result records with drag/resistance/residual/fitness
  numbers to expose `claim_state`, accepted uses, fixture IDs, model/fit status,
  validity envelope, and warnings.
- Current analytical curves are conservative but pre-RFC-0025 shaped:
  `ResistanceMetadata` records `model_family = "raw_ittc_michell"`,
  `calibration_status = "uncalibrated"`, `accepted_use =
  ["comparative_filter"]`, empty provenance fields, quadrature metadata, and
  warnings including `not_final_performance_prediction` and
  `uncalibrated_no_validity_envelope`.
- Current CFD dispatch is also conservative but pre-RFC-0025 shaped:
  `SolverProfile`, `CfdJobSpec`, `CfdRunRecord`, and `SolverRawResult` carry
  `result_semantics = "raw_unvalidated"` and the CLI `cfd prepare/status/run`
  commands print `CFD results are raw and unvalidated.`
- The source registry keeps reviewed sources as `citation_only` or
  `validation_candidate`; the Edinburgh Pacific-canoe source is explicitly
  `validation_not_calibration`, and tests assert no default source is a
  `calibration_fixture`.
- Sweep and comparison code currently keeps raw resistance out of default
  Pareto objectives, adds resistance warnings to reports, and requires
  accepted-use provenance before a resistance metric can dominate.
- The user guide, RFC index, and changelog are aligned with the current
  evidence boundary: they say resistance is raw/uncalibrated/comparative, CFD is
  local job-state plumbing, no real solver output is validated, and calibrated
  product claims remain deferred.

## Findings

### T-001 - Result metadata still lacks the RFC 0025 claim-state contract

- Severity: high
- Statement: RFC 0025 requires every result record with drag, resistance,
  residual, or design-fitness numbers to expose `claim_state`, accepted uses,
  fixture IDs, model/fit status, validity envelope, and warnings. Current
  resistance metadata instead exposes older fields such as
  `calibration_status`, `accepted_use`, and optional provenance fields, while
  CFD job/run records expose only `result_semantics = "raw_unvalidated"`.
  These fields are directionally correct, but they are not a shared, lossless
  RFC 0025 claim contract. A downstream report, API route, or future fixture
  adapter still has to infer that `calibration_status = "uncalibrated"` maps to
  `uncalibrated_comparative` and that `result_semantics` maps to
  `raw_unvalidated`.
- Evidence: `docs/rfcs/0025-cfd-calibration-claim-gates.md` lines 55-72 and
  89-105 define the required fields and acceptance criteria;
  `kayakgen/eval/contract.py` lines 13-44 define current resistance metadata
  without `claim_state`; `kayakgen/eval/cfd/jobs.py` lines 45-92 define current
  CFD semantics as `result_semantics` only; `kayakgen/eval/resistance.py` lines
  168-184 populates the current raw resistance metadata.
- Required action: add a shared RFC 0025 claim contract, or a lossless
  equivalent with stable aliases, to resistance curves and CFD job/run records.
  Today's analytical output should emit `claim_state =
  "uncalibrated_comparative"` and today's CFD output should emit `claim_state =
  "raw_unvalidated"`, while preserving existing raw behavior and compatibility
  fields as needed.

### T-002 - Web live metrics display resistance numbers without resistance claim warnings

- Severity: medium
- Statement: The web analysis view correctly labels the curve as a raw
  comparative filter and includes resistance warnings, but the live metrics
  path returns and renders single-speed `Rv_N`, `Rw_N`, and `Rt_N` values
  without carrying the resistance metadata or warning strings. That leaves one
  browser surface where numerical resistance values can be shown without the
  RFC 0025 visible-claim context.
- Evidence: `kayakgen/ui/web/controllers.py` lines 74-96 returns live metrics
  with resistance numbers and only advisory warnings; `kayakgen/ui/web/app.py`
  lines 169-188 renders those numbers directly. The stronger analysis path in
  `kayakgen/ui/web/controllers.py` lines 141-166 includes
  `resistance.metadata.warnings` and the "raw comparative filter" label.
- Required action: have the live metrics payload and rendered metrics lines
  include the same resistance claim state/warnings, or at minimum a visible raw
  comparative label, whenever resistance numbers are displayed. Add a headless
  web test that fails if live metrics include resistance values without claim
  warnings.

### T-003 - CLI evaluate writes raw resistance by default without stdout claim wording

- Severity: low
- Statement: `kayakgen evaluate` writes raw resistance metadata into the JSON,
  but its terminal output only says which file was written. The `cfd`
  subcommands already print the raw/unvalidated warning, so CLI claim wording is
  inconsistent across the two current numeric resistance/CFD surfaces.
- Evidence: `kayakgen/cli/main.py` lines 64-81 runs `resistance_curve()` by
  default and prints only `wrote <path>`; `kayakgen/cli/main.py` lines 178-180,
  198-205, and 223-228 print the CFD raw-results warning for CFD commands.
- Required action: when `kayakgen evaluate` includes resistance, print a compact
  warning such as `Resistance is uncalibrated/comparative only; see metadata`.
  This should mirror, not replace, the JSON metadata.

## No finding

- User guide and changelog language do not overclaim. The user guide states
  the project is not yet a validated performance-prediction or production CFD
  system, describes analytical resistance as uncalibrated comparative output,
  and states all CFD run records are raw and unvalidated. The changelog likewise
  says calibrated resistance, real solver execution, validated CFD outputs, and
  calibrated product claims remain deferred.
- Current CFD dispatch does not expose a real solver success path in built-in
  profiles. The unavailable and mock-failure adapters keep run records raw, and
  watertight-solid dispatch is blocked below `cfd_ready` for generated
  packages.
- Calibration source records do not silently promote validation data. The
  default registry has no `calibration_fixture` records, and the existing tests
  check that validation candidates remain distinct from calibration fixtures.

## Verification

- Read-only targeted tests were attempted with cache/bytecode writes disabled,
  but the environment does not have pytest installed:
  `PYTHONDONTWRITEBYTECODE=1 PYTEST_ADDOPTS='-p no:cacheprovider' python3 -m
  pytest -q tests/test_resistance.py tests/test_cfd_jobs.py
  tests/test_cli.py::test_cfd_prepare_status_and_unavailable_run
  tests/test_web.py::test_analysis_lines_include_units_and_resistance_warnings
  tests/test_compare.py::test_default_comparison_excludes_raw_resistance_metric
  tests/test_compare.py::test_raw_resistance_objective_is_exploratory_and_requires_provenance
  tests/test_pareto.py::test_exploratory_resistance_requires_explicit_accepted_use_provenance`
  failed with `No module named pytest`.
- `git status --short` was clean before editing. Only this review artifact is
  intended to be changed.
