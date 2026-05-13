I have everything I need. Branch-local diff, tests, and live behavior all check out within the safe-now slice the ledger accepted; F-004 and parts of F-005 remain explicitly deferred. Emitting the final-review artifact to stdout per the output contract.

# Final Review — Workflow 0038 Resistance Calibration Acceptance

Verdict intent: accept_with_findings

## Scope

This review verifies the RFC 0027 resistance-calibration-acceptance "safe-now" slice landed on branch `striatum/0038-resistance-calibration-acceptance` (commit `8bdd535 Land RFC 0027 calibration acceptance slice`, plus earlier review/ledger commits `2b70564` and `77aa0c4`). I read `AGENTS.md` first, then `SOURCES.md`, the final-reviewer role/prompt, all four upstream review artifacts (domain/source, traceability, ops, ledger), the implementation patch summary, the branch-local diff against `main`, and the implementer's recorded tests. I also reran the suite and exercised the claim gate and fixture validators directly to verify behavior on this worktree.

The workflow promotion gates I am charged with: **fixture promotion, accepted-fit metadata, metrics, envelope warnings, and default uncalibrated fallback behavior**, with the expectation that all five are covered by tests and docs.

## Sub-agent / parallel-worker usage

This Claude Opus 4.7 final-reviewer lane performed the review directly without spawning sub-agents. Rationale: the assigned SOURCES.md was a tight set (six RFCs + a small implementation footprint + four test files), the branch-local diff is only 14 files / +1013/-47, and the upstream review/ledger artifacts already represented four sub-agent passes (domain/source, traceability, ops, ledger consistency). Splitting that further would have duplicated their disjoint scopes rather than added independent signal. Parallel/concurrent tool calls were used where independent (diff inspection vs. test execution vs. live import smoke checks).

## Verification

Local commands run in `/tmp/kayak-gen-ledger-worktrees/0038`:

- `.venv/bin/python -m pytest -q` → **184 passed, 2 skipped** (skips are `kayakgen[web]` and Playwright browser deps, unchanged from main).
- `.venv/bin/python -m pytest -q tests/test_resistance.py tests/test_compare.py tests/test_cli.py` → **62 passed**.
- `git diff --check main..HEAD` → clean (no whitespace errors).
- Direct import smoke checks (recorded below) of the claim gate, the new fit-status alias mapping, the strengthened `ResistanceSourceRecord` validators, and the default `resistance_curve()` metadata.

The implementer's recorded results (62 / 184–2) reproduce here.

## Gate-by-gate verification

### Fixture promotion — accept

- `kayakgen/eval/calibration.py` now validates both `calibration_fixture` and `validation_fixture` records. Calibration fixtures require fixture_id, measured_quantity, measurement_units, hull_envelope, uncertainty_notes, validity_ranges, `fixture_review_status="accepted"`, non-empty `rights_status`, non-empty `extraction_status`, and `measured_data=True`. Validation fixtures require a strictly weaker but non-empty subset (fixture_id, measured_quantity, measurement_units, rights_status, extraction_status). Live check confirmed: `measured_data=False`, `rights_status=""`, and `extraction_status=""` are each rejected with a message that names `calibration_fixture`; an under-described validation fixture is rejected with a message that names `validation_fixture`.
- Tests `test_calibration_fixture_rejects_weak_source_evidence` (parametrized), `test_validation_fixture_requires_reproducible_fixture_metadata`, and the pre-existing `test_calibration_fixture_requires_review_metadata` cover the negative axes; `test_default_resistance_source_registry_has_no_calibration_fixtures` keeps the registry honest.
- `docs/rfcs/0027-resistance-calibration-acceptance.md` now carries the normative mapping table tying RFC 0027's three stage labels to the existing five `SourceUse` literal values, with the explicit "do not add a `candidate_source` literal or any parallel source-state enum" guardrail. This resolves F-002 / T-002 / O-003 / O-004.

### Accepted-fit metadata — accept

- `kayakgen/eval/claims.py` defines the canonical `ResistanceFitStatus` literal (`not_fit | candidate_fit | accepted_fit | rejected_fit`), a `LegacyResistanceFitStatus` literal for `passed | accepted | fit_passed`, a `SerializedResistanceFitStatus` union, and `CANONICAL_PASSING_FIT_STATUSES = {accepted_fit}`. `ClaimMetadata.fit_status` and `RawUnvalidatedClaimFields.fit_status` are now typed against the union; `ResistanceMetadata.fit_status` in `kayakgen/eval/contract.py` is likewise typed.
- A new `ResistanceFitRecord` class is defined in `kayakgen/eval/contract.py` with `model_config = ConfigDict(extra="forbid")` and the RFC 0027 fields (model_version, fit_status, calibration/validation fixture IDs, fitted_parameters, metrics, residuals_ref, validity_envelope, warnings). It is schema-only for now and is not yet emitted by `resistance_curve()`; that's consistent with the deferred F-004 slice.
- `claim_metadata_from_fields` now takes an explicit `map_legacy_fit_status` flag and preserves legacy strings unless callers opt into the RFC 0027 migration mapping. `map_legacy_fit_status_alias` provides the explicit migration helper.

### Metrics — accept

- `claim_allows_calibrated_prediction` (`kayakgen/eval/claims.py:194-211`) is now strict: it requires `claim_state=="calibrated_model"`, `accepted_uses` to contain `final_prediction`, non-empty `calibration_fixture_ids`, a non-empty `model_version`, `fit_status in CANONICAL_PASSING_FIT_STATUSES` (i.e., exactly `accepted_fit`), non-empty `fit_metrics`, a non-null `validity_envelope`, and the absence of any uncalibrated warning code. The previous "passes if `fit_metrics` is merely non-empty" branch is removed, closing F-001 / O-001.
- Live check confirmed: a record with `fit_status="rejected_fit"` plus metrics → `False`; with legacy `"passed"` plus metrics → `False`; with `accepted_fit` plus metrics → `True`; with `accepted_fit` but empty `fit_metrics` → `False`.
- Tests cover the matrix: `test_candidate_or_rejected_fit_with_metrics_cannot_claim_calibrated_prediction` (parametrized), `test_legacy_fit_aliases_do_not_claim_calibrated_prediction` (parametrized over the three legacy aliases), `test_accepted_fit_complete_contract_allows_calibrated_prediction`, `test_accepted_fit_without_metrics_cannot_claim_calibrated_prediction`, `test_validation_only_metadata_cannot_claim_calibrated_prediction`. The compare-side coverage adds `test_complete_accepted_fit_contract_allows_resistance_objective`, the parametrized `test_comparison_rejects_candidate_or_rejected_fit_with_metrics`, `test_comparison_rejects_validation_only_resistance_metadata`, and an extended `test_calibrated_prediction_requires_full_claim_contract` parametrization that now includes the empty-`fit_metrics` case.

### Envelope warnings — accept for the in-scope path; deferred for the out-of-envelope/raw-fallback path

- The default raw evaluator still emits the envelope-related warnings `uncalibrated_no_validity_envelope` and `not_final_performance_prediction` (plus `comparative_filter_only`); live import confirmed. `test_resistance_curve_shape_and_units` asserts those warnings, that `validity_envelope is None`, and that no calibration/validation fixture IDs leak into the default record.
- The shared gate continues to require `validity_envelope` to be non-null and forbids any uncalibrated warning code on a `calibrated_model` claim. That is sufficient to keep promotion blocked in the safe-now scope.
- Explicit envelope-membership checks (e.g., per-speed Fn-in-range, hull-class-in-envelope) and an out-of-envelope-→-raw-fallback wording branch are explicitly deferred to F-004; the ledger authorized that deferral and no calibrated path exists for them to gate. Tests for "accepted-fit-in-envelope vs out-of-envelope vs raw-fallback" wording remain owed once a calibrated path lands.

### Default uncalibrated fallback — accept

- `resistance_curve()` continues to emit `claim_state="uncalibrated_comparative"`, `model_family="raw_ittc_michell"`, `calibration_status="uncalibrated"`, empty `calibration_fixture_ids` and `validation_fixture_ids`, `model_version=None`, `fit_status=None`, `fit_metrics={}`, `validity_envelope=None`, and the three uncalibrated warnings. The CLI `evaluate` path retains its hard-coded "Resistance is uncalibrated/comparative only; see metadata." wording, which remains the correct user-facing copy for the present default.
- `test_resistance_curve_shape_and_units`, `test_resistance_claim_state_is_serialized_and_not_promoted`, and `test_resistance_metadata_round_trips_optional_provenance_fields` cover the default record contents, the round-trip serialization, and the negative claim-gate behavior; both now also assert `fit_metrics == {}`. No record in the default registry is a `calibration_fixture` (verified by registry test).

## Docs and traceability

- `docs/rfcs/0027-resistance-calibration-acceptance.md` adds the `SourceUse` reconciliation table, explicitly anchors the RFC to `claim_allows_calibrated_prediction`, restates the RFC 0025 forbidden-overclaim rules, and rewrites the "Resistance output may stop saying uncalibrated only when…" list and the Implementation Path to point at the same gate. This closes F-006 / T-005.
- `docs/workflows/0038-resistance-calibration-acceptance/SOURCES.md` is expanded to cover the supporting files that the reviews actually relied on (`kayakgen/eval/claims.py`, `kayakgen/eval/contract.py`, `kayakgen/search/compare.py`, `kayakgen/ui/web/controllers.py`, `tests/test_cli.py`, `tests/test_compare.py`, `tests/test_web.py`).
- `CHANGELOG.md` records the hardened RFC 0027 gates and the rejection of weak calibration/validation fixture metadata.
- `striatum/0038-resistance-calibration-acceptance/implementation/PATCH_SUMMARY.md` correctly enumerates F-001/F-002/F-003/F-005/F-006 as addressed and F-004 (plus parts of F-005) as deferred, with the sub-agent usage recorded.

## Findings recorded (non-blocking)

These are visible deferrals from the ledger-authorized safe slice. They are appropriate for follow-up workflows, not for this gate.

### FR-001 — Calibrated CLI/web/report wording branch and envelope-membership check remain deferred

Severity: medium. The CLI still hard-codes the uncalibrated copy in `kayakgen/cli/main.py:82-84`; no read of `claim_state`, no branch on `claim_allows_calibrated_prediction`, no envelope-membership check, and no out-of-envelope-→-raw-fallback wording exists in CLI, `kayakgen/ui/web/controllers.py`, or the report writers in `kayakgen/search/compare.py`. The ledger's F-004 explicitly defers this until a selected calibrated model path exists. Once it lands, the four-branch wording test matrix (uncalibrated / accepted-fit-in-envelope / accepted-fit-out-of-envelope / raw-fallback) is owed.

### FR-002 — `ResistanceFitRecord` schema is defined but not wired

Severity: low. `kayakgen/eval/contract.py::ResistanceFitRecord` is `extra="forbid"` and contains the RFC 0027 fields, but no producer constructs it and no consumer reads it; only the `fit_status` literal alignment on `ResistanceMetadata.fit_status` is currently load-bearing. That is consistent with the deferred fitting work, but the unused class is worth either using or trimming in the next slice so the schema does not drift from the gate it is meant to feed.

### FR-003 — Deferred parts of F-005 remain open

Severity: low. Fixture row loading, monotonic speed ordering, declared validity-range checks, persisted residual artifact references, validation-fixture holdout metrics, out-of-envelope warning behavior, and raw fallback wording all remain unimplemented. The ledger authorized this deferral. Tracking them on the F-004 follow-up workflow is appropriate.

### FR-004 — `PASSED_FIT_STATUSES` backward-compat alias

Severity: low / informational. `PASSED_FIT_STATUSES` is retained as a re-export of `CANONICAL_PASSING_FIT_STATUSES` for migration compatibility. It now equals `{accepted_fit}` and cannot be widened without breaking the gate, so this is safe. It is worth removing once any out-of-tree consumers have migrated, to avoid future readers re-introducing the old "or fit_metrics non-empty" branch.

## Decision

The implementation matches the ledger-authorized safe-now scope, the five workflow gates (fixture promotion, accepted-fit metadata, metrics, envelope warnings, default uncalibrated fallback) are each covered by tests and by RFC 0027 / CHANGELOG / `SOURCES.md` documentation, the default uncalibrated user-facing behavior is unchanged, and the deferred items are visible and correctly bounded. Promotion gates are tightened, not loosened; legacy aliases and metrics-only records no longer pass the calibrated-prediction gate; weak calibration-fixture and under-described validation-fixture metadata are now rejected with explicit error messages; and the RFC explicitly anchors to RFC 0025's promotion rule and to `claim_allows_calibrated_prediction` so the next slice has a single gate to extend.

Accepted with the four non-blocking findings above recorded for the follow-up workflow that adds candidate fitting, calibrated output paths, envelope-membership checks, and raw-fallback wording.
