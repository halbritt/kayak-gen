I have what I need to produce the traceability review. Drafting the artifact now.

Note: I did not spawn sub-agents; the source list was tight (six RFCs plus three implementation files plus one test file plus the workflow's own scaffolding), so I read the files directly. No parallel sub-agent help was used.

# Workflow 0038 Traceability Review

Verdict intent: accept_with_findings

## Scope

This review maps RFC 0027 (Resistance Calibration Acceptance) against the named source set: RFC 0005 raw-filter status, RFC 0012 resistance provenance and source registry, RFC 0019 calibration-fixture schema and promotion review, RFC 0025 claim-state taxonomy, current resistance metadata (`kayakgen/eval/resistance.py`, `kayakgen/eval/contract.py`, `kayakgen/eval/claims.py`, `kayakgen/eval/calibration.py`), CLI wording (`kayakgen/cli/main.py`), and the resistance test suite (`tests/test_resistance.py`).

## Sub-agent use

No sub-agents were spawned. The SOURCES.md list was small and disjoint, so the assigned reviewer agent read each file directly. The reviewer role and scope were preserved end-to-end.

## RFC ancestry map

| RFC 0027 contract | Predecessor evidence | Current code/test reality |
|---|---|---|
| Three-stage acceptance: candidate source → validation fixture → calibration fixture | RFC 0019 promotion review (rights, extraction, hull class, validity envelope); RFC 0012 source registry with `citation_only`, `validation_candidate`, no `calibration_fixture` records | `kayakgen/eval/calibration.py:13-19` `SourceUse` Literal exposes `citation_only`, `validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`, `calibration_fixture`; validator at `kayakgen/eval/calibration.py:46-67` enforces fixture review metadata; `tests/test_resistance.py:201-256` covers registry contents, validation-only behavior, and rejected promotion |
| Fit record states `not_fit`/`candidate_fit`/`accepted_fit`/`rejected_fit` with metrics, fixture IDs, validity envelope | RFC 0025 generic `fit_status: str \| None` and `fit_metrics: dict[str, float]` on every result record; RFC 0012 future `ResistanceCalibration` model sketch | `kayakgen/eval/contract.py:31-33` exposes `fit_status: str \| None`, `fit_metrics: dict[str, float]`, `validity_envelope: dict[str, Any] \| None`. The four-state taxonomy is **not** typed; there is no `ResistanceFitRecord` class |
| Resistance output may stop saying uncalibrated only with accepted fixture, named model version, accepted fit, persisted metrics/residuals, and in-envelope evaluation | RFC 0025 calibrated-prediction gate (`claim_allows_calibrated_prediction`); RFC 0012 keeps current output `uncalibrated` until a dataset is selected | `kayakgen/eval/claims.py:139-153` already gates `calibrated_model` on accepted use, fixture IDs, model version, fit status or metrics, validity envelope, and absence of uncalibrated warnings. Current curves always emit `UNCALIBRATED_COMPARATIVE` (`kayakgen/eval/resistance.py:165-189`) |
| Validation fixtures may inform metrics without listing as calibration fixture IDs | RFC 0019 distinguishes validation vs calibration; RFC 0025 reserves separate fixture-ID lists | `ResistanceMetadata.calibration_fixture_ids` and `validation_fixture_ids` are separate at `kayakgen/eval/contract.py:29-30`; `tests/test_resistance.py:225-247` asserts a validation fixture does not promote the claim |
| CLI/web/report wording mirrors the same claim metadata | RFC 0025 final-line requirement that copy uses the same claim names or lossless equivalents | `kayakgen/cli/main.py:82-84` hard-codes "Resistance is uncalibrated/comparative only" without reading `claim_state`. No conditional calibrated-wording branch exists yet |
| Raw RFC 0005 ITTC/Michell output preserved as exploratory comparative tier | RFC 0005 landed-raw-filter status; RFC 0012 raw curve metadata defaults | `kayakgen/eval/resistance.py:174-188` sets `model_family="raw_ittc_michell"`, `calibration_status="uncalibrated"`, `accepted_use=[comparative_filter]`, warnings include `not_final_performance_prediction` and `uncalibrated_no_validity_envelope` |

The dependency graph in RFC 0027 is internally consistent: it does not reach past RFC 0025's claim taxonomy and does not change RFC 0019's fixture schema or RFC 0005's raw-filter output. It also does not preempt the deferred sea-kayak calibration source selection (workflow 0012/0023) — explicit Non-Goal at RFC 0027 lines 31–33 and consistent with `default_resistance_source_registry()` containing no `calibration_fixture` records.

## Findings

### T-001 — Fit-status taxonomy is named in RFC 0027 but not typed in metadata or claim helpers

RFC 0027 names four fit states (`not_fit`, `candidate_fit`, `accepted_fit`, `rejected_fit`) and proposes a `ResistanceFitRecord` dataclass. Current code treats `fit_status` as a free-form `str | None` on both `ResistanceMetadata` (`kayakgen/eval/contract.py:32`) and `ClaimMetadata` (`kayakgen/eval/claims.py:57`). The calibrated-prediction gate at `kayakgen/eval/claims.py:147-150` accepts the legacy strings `{"passed", "accepted", "fit_passed"}` (see `kayakgen/eval/claims.py:37` `PASSED_FIT_STATUSES`); the RFC 0027 string `accepted_fit` is not in that set, so a record fit per RFC 0027 wording would silently fail the calibrated gate or be quietly promoted only by also writing one of the legacy aliases.

Required action: in the RFC 0027 implementation path, land a typed Literal for the four fit states (either on `ResistanceMetadata.fit_status` or a new `ResistanceFitRecord` model) and either replace or extend `PASSED_FIT_STATUSES` so `accepted_fit` is the canonical passing value. Other legacy aliases should be removed or explicitly mapped before this RFC's CLI wording switch is wired.

### T-002 — RFC 0027 fixture-state names diverge from the `SourceUse` literals RFC 0019 already shipped

RFC 0027 uses the labels `candidate_source`, `validation_fixture`, and `calibration_fixture`. The implemented `SourceUse` Literal at `kayakgen/eval/calibration.py:13-19` has five members: `citation_only`, `validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`, `calibration_fixture`. RFC 0027's `candidate_source` is not the same set as `citation_only ∪ validation_candidate ∪ calibration_fixture_candidate`, and the RFC does not say whether it intends to collapse those three into one stage or only relabel the most-mature pre-validation state.

Required action: before landing the fit-record work, RFC 0027 should add a normative table that lines its three stages up against the existing `SourceUse` literals (which RFC 0019 enumerated as five intentional states). Either keep the five-state Literal and treat RFC 0027 stages as buckets over it, or amend RFC 0019 to collapse them with a migration note. Do not introduce a parallel taxonomy.

### T-003 — CLI/report wording is hard-coded uncalibrated; the calibrated/raw-fallback wording branch is unimplemented

RFC 0027 acceptance criterion 7 says calibrated wording may appear only when the selected curve satisfies the accepted-fit gate, and the proposal section requires a raw-fallback warning when outside the envelope. The current CLI (`kayakgen/cli/main.py:82-84`) unconditionally prints "Resistance is uncalibrated/comparative only; see metadata." for every `evaluate` call. There is no read of `curve.metadata.claim_state`, no branch on `claim_allows_calibrated_prediction`, and no fallback wording when a hypothetical accepted-fit curve is evaluated outside its envelope. The Trame web frontend and report writers in `kayakgen.search.compare` are out of this review's read set but were named in RFC 0025 §"Acceptance Criteria" as needing the same treatment.

Required action: the RFC 0027 implementation must route the CLI line (and any equivalent web/report copy) through `claim_state` and `claim_allows_calibrated_prediction`, with explicit tests for each branch — uncalibrated, accepted-fit-in-envelope, accepted-fit-out-of-envelope, and raw-fallback. The current hard-coded copy can stay until the gate lands, but the RFC should call out that line as the wording site rather than leaving discovery to the implementer.

### T-004 — Tests cover validation-only and rejected promotion; fit-acceptance and envelope-warning tests are still owed

`tests/test_resistance.py` already covers most RFC 0027 negative cases: `test_calibration_fixture_requires_review_metadata` (rejected promotion), `test_validation_fixture_does_not_promote_resistance_claim` (validation-only behavior), `test_default_resistance_source_registry_has_no_calibration_fixtures` (no canonical calibration shipping), and `test_resistance_claim_state_is_serialized_and_not_promoted` (no quiet promotion via serialization). RFC 0027 acceptance criterion 6 also requires tests for **accepted fit metadata**, **out-of-envelope warnings**, and **raw fallback wording**. None of those three exist today, and the schema they would test (a typed `ResistanceFitRecord` and a typed warning code such as `outside_validity_envelope`) does not exist yet either — see T-001.

Required action: add these three test categories in the same step that introduces the typed fit record and CLI wording switch. The validation-only test should be extended to assert that a validation-fixture-only `ResistanceMetadata` still fails `claim_allows_calibrated_prediction`, and the accepted-fit test should be the positive counterpart of `test_resistance_claim_state_is_serialized_and_not_promoted`.

### T-005 — RFC 0027 should explicitly point at RFC 0025 promotion rules and at the `ClaimMetadata` contract it inherits

RFC 0027 references RFC 0019 and RFC 0025 in its context paragraph but does not say which RFC 0025 promotion rule it relies on for the fit-status gate or which existing helper (`claim_allows_calibrated_prediction`) it expects the implementation to extend. RFC 0025 lines 89–105 already list the promotion rule for "a model may become calibrated only after fitting code records accepted calibration fixture IDs, fitted parameters, metrics, residuals, and the envelope where claims apply." RFC 0027's acceptance criterion 4 is the same rule restated, but the cross-reference is implicit. RFC 0025 acceptance test 4 ("uncalibrated resistance as calibrated") is the negative test that RFC 0027's accepted-fit test must not break.

Required action: in a short revision pass on RFC 0027, add explicit anchors to RFC 0025 §"Proposal" promotion rules and to `kayakgen/eval/claims.claim_allows_calibrated_prediction` so the implementer does not reinvent the gate. RFC 0027 should also state that `fit_status="accepted_fit"` must be added to the calibrated-prediction gate's accepted set rather than via a parallel helper.

## Traceability Summary

RFC 0027 is the right successor RFC for resistance calibration acceptance. It does not duplicate RFC 0019's fixture schema, it does not override RFC 0025's claim taxonomy, and it does not weaken RFC 0005's raw-filter posture or RFC 0012's "uncalibrated until a dataset is selected" stance. The acceptance criteria are testable against the existing metadata and registry contracts, and the negative-test posture is consistent with RFC 0025's overclaim-prevention tests.

The findings are alignment items between RFC 0027's proposed taxonomy and the contracts/wording sites that already exist. They are appropriate for implementation-step work, not for blocking the RFC. T-002 (taxonomy reconciliation with RFC 0019's `SourceUse` Literal) is the most load-bearing because it changes the schema; T-001 (typed fit states) and T-005 (explicit cross-references to the existing gate) should land in the same revision pass so the implementation does not fork the gate logic. T-003 and T-004 (CLI wording branch plus the three missing test categories) are deliverables of the implementation path step 4 ("Add acceptance metrics and negative tests for overclaiming"), and the RFC already places them there — they only need to be named more precisely.

Accept RFC 0027 with the findings recorded above, on the understanding that the implementation path's step 1 (fixture promotion status and review metadata) is already largely landed in `kayakgen/eval/calibration.py`, and the next concrete work is the typed fit record (step 2) plus the wording/gate alignment (steps 3–5).
