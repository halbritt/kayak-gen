---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept_with_findings
---

author: reviewer-traceability-claude-opus-4.7-001

# Workflow 0055 Traceability Review

## Scope

Verified every workflow 0055 change traces back to a row in
`docs/workflows/0055-rfc-0058-stage1-stability-fit-schemas/STAGE_1_DECISIONS.md`
(D-1 .. D-12) or to RFC 0058's stage-1 acceptance criteria. Cross-checked
the workflow.json job scopes, the two implementer patch summaries
(`stability_fit_schemas` and `docs_sync`), the scaffold commit
`89f59b4`, and the uncommitted working-tree changes that comprise the
landing:

- `kayakgen/eval/stability/accepted_fit.py` (new)
- `tests/test_stability_accepted_fit.py` (new)
- `CHANGELOG.md`, `docs/DECISION_LOG.md`, `docs/ROADMAP.md`,
  `docs/rfcs/README.md`,
  `docs/rfcs/0058-stability-calibration-acceptance.md`,
  `docs/workflows/0055-rfc-0058-stage1-stability-fit-schemas/OPERATOR_REPORT.md`.

RFC 0058's `## Acceptance Criteria` was inspected end-to-end; each
stage-1 line item is mapped against an implementing surface below.
The "Out of scope (deferred)" list in `STAGE_1_DECISIONS.md` was used
as the scope-creep mirror — anything from that list appearing on disk
would be a finding.

## Decision-by-decision traceability

| Decision | Implementing track | Concrete artefact | Status |
| --- | --- | --- | --- |
| D-1 module path + tests location | `implement_stability_fit_schemas` | `kayakgen/eval/stability/accepted_fit.py` (sibling to RFC 0056's `measured_fixture.py`); `tests/test_stability_accepted_fit.py`. | ✓ |
| D-2 five records + `extra="forbid"` + `schema_version="1"` | `implement_stability_fit_schemas` | `HullFamilyScope`, `StabilityFitMetrics`, `ReviewerSignature`, `StabilityFitRecord`, `StabilityFixturePromotionPacket` — each `model_config = ConfigDict(extra="forbid")` with `schema_version: Literal["1"] = "1"`. | ✓ |
| D-3 `HullFamilyScope` shape + empty-envelope refusal | `implement_stability_fit_schemas` | `HullFamilyScope.hull_class: str = Field(min_length=1)` + `design_hash_envelope: list[str]` with `_design_hash_envelope_non_empty` validator (`accepted_fit.py:54-67`); empty-envelope refusal pinned by `test_hull_family_scope_requires_design_hash_envelope`. | ✓ |
| D-4 `StabilityFitMetrics` four required fields + ranges | `implement_stability_fit_schemas` | `rmse_m`, `mape_fraction`, `max_error_m` all `Field(ge=0)`; `coverage_fraction` `Field(ge=0, le=1)` (`accepted_fit.py:70-79`). | ✓ |
| D-5 threshold defaults + `strict` toggle + warning recording | `implement_stability_fit_schemas` | `DEFAULT_STABILITY_FIT_RMSE_M=0.005`, `DEFAULT_STABILITY_FIT_MAPE_FRACTION=0.05`, `DEFAULT_STABILITY_FIT_MAX_ERROR_M=0.01`, `DEFAULT_STABILITY_FIT_COVERAGE_FRACTION=0.9` constants exported; `_strict_thresholds` validator raises `stability_fit_metrics_outside_default_thresholds` when `strict=True` and any metric is outside the threshold, and appends `strict_check_skipped` to `warnings` when `strict=False` (`accepted_fit.py:16-19, 136-173`). Both branches pinned by `test_stability_fit_record_strict_thresholds_refuse_bad_metrics` and `test_stability_fit_record_strict_false_skips_thresholds_and_records_warning`. | ✓ |
| D-6 `ReviewerSignature` fields | `implement_stability_fit_schemas` | `reviewer_label: str (min_length=1)`, `reviewer_role: str (min_length=1)`, `signed_at: datetime` (`accepted_fit.py:82-90`). | ✓ |
| D-7 `StabilityFitRecord` field set + accepted-verdict invariants | `implement_stability_fit_schemas` | All required fields present (`accepted_fit.py:93-111`); `_valid_heel_range_ordered` enforces `low < high`; `_accepted_verdict_has_acceptance_metadata` enforces `accepted_at is not None` and `rejection_reasons == []` when verdict is `accepted` (`accepted_fit.py:113-134`). `fixtures: list[FixtureRef] = Field(min_length=1)` enforces ≥1 fixture. Pinned by `test_accepted_fit_requires_accepted_at_and_no_rejection_reasons`. | ✓ |
| D-8 `FixtureRef` value object + SHA-256 shape + no disk check | `implement_stability_fit_schemas` | `FixtureRef.fixture_id/path/sha256` with `_fixture_sha256_is_lower_hex` against `^[0-9a-f]{64}$` (`accepted_fit.py:32-51`); module never opens the filesystem (deferred to a later stage per the RFC). Pinned by `test_fixture_ref_sha256_must_be_64_lowercase_hex` covering short/uppercase/non-hex cases. | ✓ |
| D-9 promotion-packet shape + refusal rules | `implement_stability_fit_schemas` | All five review verdicts (`rights_review`, `hull_identity_review`, `calibration_drift_review`, `hysteresis_review`, `free_equilibrium_review`) typed `Literal["accepted","rejected","deferred"]`; `rig_design_match: bool`; `promotion_target` literal; `_measured_fixture_promotion_requires_all_reviews` validator enforces all-accepted + `rig_design_match=True` + `rejection_reasons=[]` (`accepted_fit.py:176-219`). Each refusal branch pinned: `test_promotion_packet_refuses_non_accepted_review_verdict`, `test_promotion_packet_refuses_non_matching_rig_design`, `test_promotion_packet_refuses_rejection_reasons_for_promotion`. | ✓ |
| D-10 no fixture/fit promoted by this RFC | `implement_stability_fit_schemas` + `synchronize_docs` | The test surface uses `acceptance_verdict="rejected"` and `promotion_target="validation_candidate"`; no on-disk fixture/fit record is shipped; the stage-1 RFC note + D038 + CHANGELOG entry all repeat the no-promotion boundary. | ✓ |
| D-11 stage-2 surfaces NOT landed | scope guard | `resolve_analytical_claim_label`, `cfd_in_loop_evaluator_status`, and `kayakgen stability` are absent from the diff (verified by `grep`-equivalent inspection of the new module and the unchanged CLI surface). | ✓ |
| D-12 docs sync set | `synchronize_docs` | `CHANGELOG.md` Unreleased "Added" entry; `docs/DECISION_LOG.md` row D038; `docs/ROADMAP.md` new "Stability calibration acceptance" track row; `docs/rfcs/0058-stability-calibration-acceptance.md` status flip to `landed (schemas only)` + stage-1 implementation-note paragraph; `docs/rfcs/README.md` updated row; workflow's `OPERATOR_REPORT.md` records the docs sync. | ✓ |

## RFC 0058 acceptance-criteria coverage

| RFC 0058 criterion | Stage-1 coverage |
| --- | --- |
| `StabilityFitRecord`, `HullFamilyScope`, `StabilityFixturePromotionPacket`, `StabilityFitMetrics`, `ReviewerSignature` Pydantic records under `kayakgen/eval/stability/accepted_fit.py` with byte-stable canonical JSON and `schema_version="1"`. | Met. Round-trip pinned by `test_stability_fit_record_round_trips_canonical_json`. |
| `resolve_analytical_claim_label` implemented, defaults to `unvalidated_hydrostatic_comparison`. | **Explicitly deferred to stage 2** per STAGE_1_DECISIONS.md D-11. Stage-1 note in RFC 0058 calls this out. |
| `cfd_in_loop_evaluator_status` implemented, defaults `opt_in_only`. | Explicitly deferred to stage 2. |
| New `kayakgen stability` sub-app. | Explicitly deferred (stage 3 per `STAGE_1_DECISIONS.md` § "Out of scope"). |
| No fixture is promoted by this RFC. | Met. |
| RFC 0043's default `result_semantics="unvalidated_hydrostatic_comparison"` remains the only legal label. | Met — code grep of `kayakgen/` shows no changes to the analytical evaluator's label resolution. |
| All existing forbidden-claim scrub-list tokens remain enforced; no new safety / seaworthiness / final-prediction / design-fitness wording. | Met — diff does not touch `tests/test_web_layout.py` or the renderer's `FORBIDDEN_COPY_*` constants. |
| Docs sync (USER_GUIDE, ARCHITECTURE_MAP, DDD, SPEC, PRD, ROADMAP, DECISION_LOG) updated in the same landing. | Partial. CHANGELOG, ROADMAP, DECISION_LOG (D038), RFC 0058, RFC README, OPERATOR_REPORT are updated. USER_GUIDE / ARCHITECTURE_MAP / DDD / SPEC / PRD are not updated, which is consistent with stage 1 shipping no user-facing CLI/feature surface; see F2 below. |

## Scope-creep check

Compared the on-disk diff against `STAGE_1_DECISIONS.md` § "Out of scope
(deferred)":

- `kayakgen stability` CLI sub-app — **absent on disk.** ✓
- `resolve_analytical_claim_label` — absent. ✓
- `cfd_in_loop_evaluator_status` — absent. ✓
- Frontier-view colour-mapping for validated points — absent. ✓
- Form-builder evaluator-block hiding the CFD-in-loop ack when
  graduated — absent. ✓

No scope creep. The implementer track wrote exactly the schemas +
validators + tests promised; the docs track wrote exactly the
synchronization surface the workflow.json allowed.

## Findings

- **F1 (non-blocking, doc-only)** —
  `docs/workflows/0055-rfc-0058-stage1-stability-fit-schemas/STAGE_1_DECISIONS.md`
  row D-9 prose says "four review verdicts" but lists five
  (`rights_review`, `hull_identity_review`, `calibration_drift_review`,
  `hysteresis_review`, `free_equilibrium_review`). The implementation
  ships five, which matches both RFC 0058 (`### Promotion-review packet`)
  and the validator that requires all five to be `"accepted"`.
  Recommendation: fix the decisions-doc count from "four" to "five" in
  remediation so future workflow audits don't have to reconcile the
  number.

- **F2 (non-blocking, scope clarification)** — RFC 0058's `## Acceptance
  Criteria` lists `USER_GUIDE.md`, `ARCHITECTURE_MAP.md`, `DDD.md`,
  `SPEC.md`, `PRD.md` among the docs to update "in the same landing."
  Stage 1 deliberately ships no user-facing CLI/feature surface, so
  those docs do not need new content yet; the stage-1 implementation
  note inside the RFC body already calls out the narrower landing.
  Recommendation: add a one-line aside to the RFC 0058 stage-1 note
  (or to `STAGE_1_DECISIONS.md` D-12) explicitly stating that
  USER_GUIDE/ARCHITECTURE_MAP/DDD/SPEC/PRD are deferred until the
  stage-2/3 CLI + read-model landing surfaces user-visible behavior.
  This prevents a future review from reading the RFC's acceptance
  list as an undelivered obligation.

- **F3 (non-blocking, RFC-body drift)** — RFC 0058's `### Promotion-review
  packet` proposal originally typed the verdict fields as structured
  classes (`RightsReviewVerdict`, `HullIdentityReviewVerdict`,
  `CalibrationDriftReviewVerdict`, `HysteresisReviewVerdict`,
  `FreeEquilibriumReviewVerdict`). Stage 1 chose the simpler
  `Literal["accepted","rejected","deferred"]` per `STAGE_1_DECISIONS.md`
  D-9, which is a valid narrowing — but the RFC body still describes
  the structured-verdict shape. Recommendation: append a sentence to
  the RFC 0058 stage-1 implementation note that records the
  `Literal[...]` narrowing relative to the original RFC body, so the
  body and the landed code don't drift silently.

None of the above is a blocker; all three are doc-side cleanups the
remediator can fold in without re-opening implementation scope.

## Verdict

**accept_with_findings**

Workflow 0055 lands exactly the stage-1 scope promised by
`STAGE_1_DECISIONS.md` D-1 .. D-12 and the stage-1 subset of RFC
0058's acceptance criteria. No scope creep, no claim-label drift, no
new fixture/fit promotion. The three findings above are doc-side
cleanups suitable for the bounded remediation cycle declared in
`workflow.json`.
