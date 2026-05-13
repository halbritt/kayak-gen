# Findings ledger - workflow 0038 resistance calibration acceptance

session: sess_1eb736a04ed9413fae6d56e8300e25e7
job: job_run_7d439091034943ec90848192c9f49136_findings_ledger
lease: lease_96543c1b972746a489d28ef21654908b
role: ledger
lane_model: codex / GPT-5.5
date: 2026-05-13
gate_result: accept_with_findings

## Scope

This ledger consolidates the domain/source, traceability, and ops review
artifacts for RFC 0027 resistance calibration acceptance. The accepted
implementation slice is limited to schema, metadata, source-state alignment,
claim-gate hardening, and negative tests that keep current resistance output
uncalibrated.

This ledger does not authorize candidate fitting, accepted fitting, fixture
promotion, calibrated prediction output, final design-fitness scoring, or any
removal of uncalibrated warnings from the current raw ITTC/Michell evaluator.

## Sub-agent help used

Four read-only sub-agents were used with disjoint scopes:

- domain-source extractor over `REVIEW_DOMAIN_SOURCE.md` and source files;
- traceability extractor over `REVIEW_TRACEABILITY.md` and source files;
- ops/test extractor over `REVIEW_OPS.md` and source files;
- consistency checker over all three review artifacts and ledger instructions.

All sub-agents were instructed not to edit files, call `striatum`, publish or
complete jobs, push branches, update reports, or emit any line beginning with
the forbidden attribution prefix. The ledger artifact was written locally by
this ledger role.

## Stats

- Review artifacts read: 3
- Raw review findings/statements: 15
- Deduplicated accepted findings: 6
- Safe-now areas: typed fit-state metadata, claim-gate hardening,
  source/fixture taxonomy reconciliation, source-record validation, negative
  overclaim tests, RFC 0027 cross-reference cleanup
- Deferred areas: candidate fitting, accepted fitting, fixture row promotion,
  calibrated output wording, out-of-envelope raw fallback behavior, accepted
  residual/metric artifacts

## Accepted findings

### F-001 - Fit-state metadata and calibrated-prediction gate are too loose

- Severity: high
- Review sources: T-001, O-001, O-002, O-006, DS-004
- Classification: safe-now schema/metadata and claim-gate work
- Affected files: `kayakgen/eval/claims.py`,
  `kayakgen/eval/contract.py`, `kayakgen/eval/resistance.py`,
  `tests/test_resistance.py`, `tests/test_compare.py`

RFC 0027 defines `ResistanceFitRecord.fit_status` as
`not_fit`, `candidate_fit`, `accepted_fit`, or `rejected_fit`, and says
resistance output may stop saying uncalibrated only when a named model has an
`accepted_fit`. Current metadata still exposes loose `fit_status: str | None`
and `fit_metrics: dict[str, float]`. The current calibrated-prediction helper
accepts legacy statuses `passed`, `accepted`, and `fit_passed`, and also allows
promotion when `fit_metrics` is merely non-empty. That means a rejected or
candidate-style record with metrics can satisfy the helper if the other fields
are forged.

Required remediation:

- Add a typed fit-status contract for RFC 0027, either as a
  `ResistanceFitRecord` model or as a typed metadata subset.
- Make `accepted_fit` the canonical passing status for calibrated prediction.
- Remove metrics-only promotion from `claim_allows_calibrated_prediction`.
- Treat legacy fit-status aliases only as an explicit migration/mapping path,
  not as the canonical gate.
- Add negative tests proving `candidate_fit` and `rejected_fit` do not pass even
  with metrics, plus a positive synthetic contract test for `accepted_fit`.
- Keep `resistance_curve()` default metadata as `uncalibrated_comparative` with
  no model version, fit status, fit metrics, or validity envelope.

### F-002 - RFC 0027 fixture-stage names diverge from the shipped source-state vocabulary

- Severity: medium
- Review sources: T-002, O-003, O-004
- Classification: safe-now schema/RFC taxonomy reconciliation
- Affected files: `docs/rfcs/0027-resistance-calibration-acceptance.md`,
  `kayakgen/eval/calibration.py`, `tests/test_resistance.py`

RFC 0027 describes three stages: `candidate_source`, `validation_fixture`, and
`calibration_fixture`. The existing `SourceUse` literal has five states:
`citation_only`, `validation_candidate`, `validation_fixture`,
`calibration_fixture_candidate`, and `calibration_fixture`. The RFC does not
yet say whether `candidate_source` is a bucket over the three pre-fixture
states or a replacement taxonomy.

Required remediation:

- Reconcile RFC 0027's three-stage language with the existing `SourceUse`
  literal before adding fit-record work.
- Prefer a normative mapping table that keeps the five existing states unless a
  separate migration explicitly collapses them.
- Do not introduce a parallel source-state taxonomy.
- Keep current default registry records as candidates or citation-only records;
  no current record becomes a fixture from this reconciliation alone.

### F-003 - Fixture validation is partially implemented but still too weak for promotion

- Severity: medium
- Review sources: DS-001, DS-002, O-003, O-004, T-002
- Classification: safe-now source/fixture metadata validation
- Affected files: `kayakgen/eval/calibration.py`,
  `tests/test_resistance.py`

The current `ResistanceSourceRecord` model captures useful provenance fields,
and calibration fixtures already require fixture ID, measured quantity, units,
hull envelope, uncertainty notes, validity ranges, and
`fixture_review_status="accepted"`. That is a good partial guard. The ops review
found two remaining gaps: accepted calibration fixtures can still validate with
`measured_data=False` and empty rights/extraction strings, and
`validation_fixture` records have no minimum fixture metadata at all.

Required remediation:

- Strengthen `calibration_fixture` validation to require measured data,
  non-empty rights status, non-empty extraction status, and the existing review
  metadata fields.
- Define minimum metadata for `validation_fixture` records that is weaker than
  the calibration-fixture gate but sufficient for reproducible validation.
- Add negative tests for model-derived calibration fixtures, empty rights,
  empty extraction status, and under-described validation fixtures.
- Keep validation fixtures distinct from calibration fixtures; validation-only
  records must not remove uncalibrated warnings or populate calibration fixture
  IDs.

### F-004 - Calibrated wording, envelope checks, and raw fallback are not implemented

- Severity: medium
- Review sources: T-003, O-005, T-004, O-006
- Classification: deferred calibrated-output work
- Affected files: `kayakgen/cli/main.py`, future web/report wording sites,
  claim-gate tests

Current CLI evaluation always calls the raw `resistance_curve()` path and, when
resistance is present, prints a hard-coded uncalibrated/comparative warning.
That is correct for today's default output. RFC 0027 also requires future
calibrated wording to appear only when selected curve metadata satisfies the
accepted-fit gate, and future out-of-envelope or raw-fallback cases must keep a
warning. There is currently no selected calibrated model path, no envelope
membership check, and no raw fallback branch.

Required remediation:

- Defer calibrated wording until F-001's accepted-fit gate, a selected model
  version, accepted fixture IDs, persisted metrics/residuals, and validity
  envelope checks exist.
- When that future path exists, route CLI/web/report wording through the shared
  claim metadata and explicit envelope checks.
- Add tests for uncalibrated wording, accepted-fit in-envelope wording,
  accepted-fit out-of-envelope warning, and raw-fallback wording.
- Do not remove or soften the current uncalibrated warning in ordinary
  evaluation.

### F-005 - RFC 0027 negative-test matrix is incomplete

- Severity: medium
- Review sources: T-004, O-006, DS-003
- Classification: mixed; safe-now negative tests plus deferred fitting/output
  tests
- Affected files: `tests/test_resistance.py`, `tests/test_compare.py`, future
  CLI/web/report tests

Existing tests cover useful baselines: raw resistance metadata stays
uncalibrated, metadata serialization does not promote, the default registry has
no calibration fixtures, missing calibration-fixture review metadata is
rejected, and comparison reports reject incomplete calibrated claim contracts.
The remaining RFC 0027 matrix is not covered.

Required remediation:

- Safe now: add negative tests for candidate/rejected fit statuses with metrics,
  weak calibration-fixture source evidence, under-described validation fixtures,
  and validation-only metadata failing `claim_allows_calibrated_prediction`.
- Deferred until fitting/output paths exist: accepted fit metadata with
  persisted residual references, validation fixtures participating in metrics,
  out-of-envelope warning behavior, raw fallback wording, fixture row loading,
  units, monotonic speed ordering, declared validity ranges, and residual
  artifact references.
- Tie tests to the shared claim contract rather than only legacy
  `calibration_status` or `accepted_use` strings.

### F-006 - RFC 0027 should anchor explicitly to RFC 0025 claim gates

- Severity: low
- Review sources: T-005, consistency checker
- Classification: safe-now documentation/traceability cleanup
- Affected files: `docs/rfcs/0027-resistance-calibration-acceptance.md`,
  `docs/workflows/0038-resistance-calibration-acceptance/SOURCES.md`

RFC 0027 references RFC 0025 but does not explicitly name the existing
promotion helper or the precise RFC 0025 promotion rule it inherits. The review
work also relied on `kayakgen/eval/claims.py`, `kayakgen/eval/contract.py`,
`tests/test_compare.py`, and CLI/report tests even though those are not all
listed in workflow `SOURCES.md`.

Required remediation:

- Add explicit RFC 0025 anchors in RFC 0027 around calibrated-model promotion
  and forbidden overclaims.
- State that `claim_allows_calibrated_prediction` is the gate to extend rather
  than creating a parallel helper.
- Consider adding the discovered supporting files to the workflow source list
  in a future workflow maintenance pass.

## No-action findings

- The default raw ITTC/Michell evaluator remains correctly marked
  `uncalibrated_comparative`, comparative-filter-only, and not a final
  performance prediction.
- The default resistance source registry contains candidate and citation-only
  records but no accepted calibration fixture.
- Domain/source review findings that described existing rights, extraction,
  measured-quantity, metadata, and validation-only behavior are accepted as
  support for the schema foundation, not as evidence that real calibration
  fixtures, fit records, or calibrated output are complete.

## Safe-now implementation scope

Implementers may:

- type the RFC 0027 fit-status contract and serialize it;
- harden `claim_allows_calibrated_prediction` so only `accepted_fit` passes;
- reconcile RFC 0027 fixture stages with the existing `SourceUse` states;
- strengthen `ResistanceSourceRecord` validation for calibration and validation
  fixtures;
- add negative tests for forbidden promotion and weak fixture metadata;
- preserve backward-compatible aliases where needed, as long as aliases cannot
  promote a record by themselves;
- update RFC/workflow traceability wording to point at RFC 0025 claim gates.

Implementers must not:

- add or tune a candidate fitting algorithm in this safe slice;
- mark any fit as accepted;
- promote any current source to `validation_fixture` or `calibration_fixture`;
- ingest numeric fixture rows or residual artifacts as accepted evidence;
- make calibrated wording appear in CLI/web/report output;
- allow validation-only fixtures, unreviewed data, or loose metrics to remove
  uncalibrated warnings.

## Deferred items

- Selecting a sea-kayak calibration dataset.
- Promoting Edinburgh, Gomes, Tzabiras, Sea Kayaker-derived, or any other
  current source into an accepted calibration fixture.
- Candidate fitting, fitted parameter storage, accepted metrics, residual
  artifact references, and model-version selection.
- Validity-envelope membership checks and out-of-envelope raw fallback behavior.
- Calibrated CLI/web/report wording.
- Final Pareto or design-fitness scoring that uses calibrated resistance.

## Implementation guidance

Start with F-002 and F-001 so taxonomy and fit-state names are canonical before
claim-gate hardening lands. Then apply F-003 fixture validation and F-005
negative tests against the same contract. F-004 remains a future output slice:
the current uncalibrated warning is the correct user-facing behavior until an
accepted fixture, accepted fit, persisted metrics/residuals, and envelope check
exist.
