# Pipeline-Integrity Audit Findings — 2026-05-25 full_repo

## Summary

Audit of claim-state, accepted-use, readiness, and acceptance-gate invariants across the full repository at HEAD `313dfdd`. Scope: post-workflow-0037/0038 state including RFC 0059/0060/0061/0062 and the latest web UI inline-help / hydrostatics-registry additions. High-quality pass: all critical/high/medium items cleared; findings are targeted improvements to test coverage and documentation continuity.

---

### AUD-P-001: EMPTY_STABILITY_FIT_REGISTRY consumption verified across all three call sites

severity: info
category: claim_gate
status: closed
claim: D042 requires three RFC 0058 stage-2/3 call sites to consume EMPTY_STABILITY_FIT_REGISTRY rather than bare `()` literals.
evidence:
- `kayakgen/eval/stability/evaluator.py:139` — `resolve_analytical_claim_label(hull, fit_registry=EMPTY_STABILITY_FIT_REGISTRY)`
- `kayakgen/ui/web/generate_frontier_view.py:137` — `fit_registry=EMPTY_STABILITY_FIT_REGISTRY`
- `kayakgen/ui/web/generate_spec_form.py:35` — `from kayakgen.eval.stability.accepted_fit import EMPTY_STABILITY_FIT_REGISTRY`; line 100 — `registry=EMPTY_STABILITY_FIT_REGISTRY`
impact: The RFC 0058 stage-4 graduation gate has a single synchronization point. No regression since workflows 0037/0038 landed.
recommended_action: No action required. Baseline establishment for future audits.
follow_up: wontfix

---

### AUD-P-002: Presentation-layer registries (RFC 0060/0062) remain UI-only; no leak to claim-gate paths

severity: info
category: claim_gate
status: closed
claim: The new HullParameterMetadata (RFC 0060) and HydrostaticsRowMetadata (RFC 0062) registries are presentation-only and must not be imported into evaluator or claim-gate code paths.
evidence:
- `kayakgen/ui/parameter_metadata.py` — imported in `kayakgen/ui/pv_window.py`, `kayakgen/ui/desktop.py`, `kayakgen/ui/web/generate_spec_form.py` only (UI modules); never imported in `kayakgen/eval/` or `kayakgen/search/` or `kayakgen/services/evaluation.py`
- `kayakgen/ui/hydrostatics_metadata.py` — imported in `kayakgen/services/evaluation.py:449` inside `analysis_view_model::hydro_rows` presentation function only; never imported into evaluators
- `tests/test_vocabulary_coverage.py:138-152` — RFC 0060 presentation-term documentation test passes
impact: No risk of the registries accidentally widening a claim state beyond its evidence. The pattern mirrors existing design, preserving claim boundaries.
recommended_action: No action required. Forward baseline for D043 pattern reuse.
follow_up: wontfix

---

### AUD-P-003: Analytical claim label (high-angle GZ) resolution contract holds under empty registry

severity: info
category: claim_gate
status: closed
claim: `resolve_analytical_claim_label(hull, fit_registry)` must return `"unvalidated_hydrostatic_comparison"` when `fit_registry` is empty and no accepted StabilityFitRecord matches the hull.
evidence:
- `kayakgen/eval/stability/high_angle_contracts.py:60-79` — function correctly returns `"unvalidated_hydrostatic_comparison"` when the registry is empty or no matching record is found; returns `"validated_hydrostatic_comparison"` only when an accepted record with matching hull_class and design_hash_envelope is located
- `kayakgen/eval/stability/evaluator.py:139` — calls with `EMPTY_STABILITY_FIT_REGISTRY` by contract
- RFC 0058 stage 2/3: no accepted fit exists yet; all produced GZ curves default to `"unvalidated_hydrostatic_comparison"`
impact: The RFC 0043 result-semantics label is pinned to evidence: no analytical GZ claim is promoted beyond its boundary (empty registry = no validation possible).
recommended_action: No action required. Baseline for stage-4 graduation criteria.
follow_up: wontfix

---

### AUD-P-004: Inline-help copy (workflow 0037) does not make strengthened claims

severity: info
category: claim_gate
status: closed
claim: The new tooltip and disabled-reason copy in workflow 0037 (AUD-O-001/002/003/004/006/007) must avoid naming RFC / claim_state / internal vocabulary and must not assert a stronger computation claim than the underlying state supports.
evidence:
- `kayakgen/ui/web/app.py:104-110` — VALIDITY_BADGE_TITLE_* constants contain "advisory only" language; no claim about final design fitness or validation
- `kayakgen/ui/web/app.py:113-120` — COMPARISON_TOGGLE_*_HELP constants describe two data sources (live frontier vs imported report) without claiming validation status
- `kayakgen/ui/web/app.py:123-129` — MESH_*_CHIP_TITLE constants describe mesh readiness ("independent of whether a mesh package exists") without claiming CFD readiness
- `kayakgen/ui/web/generate_spec_form.py:88-102` — SUBMIT_BLOCKING_REASON_* constants surface user-facing validation failures (missing variables, admissibility gate) without internal jargon
- `tests/test_web_inline_help.py:56-58` — helper validates that no RFC / claim_state terminology appears in badge titles
- `kayakgen/services/evaluation.py:471-475` — mesh diagnostic row labels append threshold guidance ("must be 0", "acceptable") clarifying advisory semantics, not strengthening claims
impact: User-facing copy does not accidentally promote a claim state or suggest a validation status that the underlying evaluator output does not support.
recommended_action: No action required. Workflow 0037 landing is verified.
follow_up: wontfix

---

### AUD-P-005: High-angle GZ default output remains unvalidated across all surfaces

severity: info
category: claim_gate
status: closed
claim: No surface (CLI, sweep, web, desktop) defaults to surfacing high-angle GZ output with a stronger claim label than `"unvalidated_hydrostatic_comparison"`.
evidence:
- `kayakgen/cli/main.py` — `kayakgen stability` default output does not include `--high-angle-gz` flag; the opt-in is explicit
- RFC 0043 stage 3 / D019: CLI output is byte-equal to prior without the explicit opt-in
- D014 staged surfacing: sweep summaries, frontiers, default objectives remain unchanged (no automatic high-angle-GZ surfacing)
- `kayakgen/ui/web/read_models.py:*` — high-angle GZ section in comparison reports is display-only with "unvalidated hydrostatic comparison curves" caption
- No objective in `kayakgen/search/objectives.py` carries a high-angle-GZ metric as a default objective
impact: The `unvalidated_hydrostatic_comparison` semantics are not masked or accidentally promoted by any user-facing default.
recommended_action: No action required. D014 / staged-surfacing contract verified.
follow_up: wontfix

---

### AUD-P-006: Test coverage for vocabulary, registries, and inline-help is complete

severity: info
category: test_gap
status: closed
claim: The claim-gate boundary tests (vocabulary_coverage, hydrostatics_row_metadata, web_inline_help) all exist and are wired correctly.
evidence:
- `tests/test_vocabulary_coverage.py` — 10 parametrized tests covering ClaimState, SourceUse, SourceReviewVerdict, readiness-state literals, RFC decision tokens, RFC 0057/0058 aggregate terms, RFC 0060 presentation terms; all tests documented to close audit findings
- `tests/test_hydrostatics_row_metadata.py` — 12 tests covering registry coverage (7 expected keys), well-formedness (labels/descriptions non-blank trimmed), wiring assertion (analysis_view_model labels match registry), and byte-stable regression on wire payload
- `tests/test_web_inline_help.py` — 11 tests covering validity badge (all four states documented, no RFC jargon), comparison-source toggle (both modes have subtitle copy), mesh chip pair (both chips have tooltips), submit-button disabled reason (wiring and copy), plus AUD-P-004 regression assertion for forbidden-copy scan compatibility
- All three test files run in default suite without external dependencies (no playwright, no trame round-trip)
impact: The claim-gate boundaries (claim_state literals, result_semantics labels, acceptance gates, user-facing copy) are pinned and regression-tested.
recommended_action: No action required. Audit finding closure basis verified.
follow_up: wontfix

---

### AUD-P-007: RawUnvalidatedClaimFields validators enforce claim-state boundaries

severity: info
category: claim_gate
status: closed
claim: The RFC 0025 RawUnvalidatedClaimFields validator must refuse any attempt to declare accepted uses, fixture IDs, fit evidence, or validity envelopes on a raw_unvalidated record.
evidence:
- `kayakgen/eval/claims.py:104-130` — RawUnvalidatedClaimFields class with @model_validator(mode="after") enforcing five boundary checks:
  - line 121-122: accepted_uses must be empty
  - line 123-124: fixture IDs (calibration or validation) must be empty
  - line 125-126: model_version, fit_status, fit_metrics all must be empty
  - line 127-128: validity_envelope must be None
- No CFD adapter (fixture or real OpenFOAM) sets any of these fields on raw_unvalidated output
- No raw analytical resistance record declares anything beyond the raw_cfd_warnings() list
impact: The lowest claim state is mathematically impossible to promote: any accidental promotion is caught at schema validation time, not at runtime.
recommended_action: No action required. Boundary invariant verified.
follow_up: wontfix

---

### AUD-P-008: Artifact-store identity (RFC 0049) contract preserved across workflows 0037/0038 landing

severity: info
category: claim_gate
status: closed
claim: The Hull.record_hash() / Hull.design_hash() contract (RFC 0049 / D030) must remain stable and used consistently by all three identity-consuming sites.
evidence:
- `kayakgen/model/hull.py` — existing `Hull.hash()` method (aliases record_hash); `design_hash` property present; no breaking changes in workflows 0037/0038
- `kayakgen/services/identity.py` — ships `record_hash()`, `design_hash_for_hull()`, `run_hash()` entry points; all use the same hull hash methods
- `kayakgen/eval/stability/high_angle_contracts.py:82-88` — `resolve_analytical_claim_label` consumes `hull.design_hash()` to match against `scope.design_hash_envelope`; no change to this path in workflows 0037/0038
- No workflow 0037/0038 change touches `FilesystemArtifactStore` or `SqliteIndex` paths
impact: The RFC 0049 artifact-store design-hash binding (used by RFC 0058 hull-family-scope matching) remains unbroken.
recommended_action: No action required. Baseline for design_hash-dependent features.
follow_up: wontfix

---

### AUD-P-009: Log redaction (RFC 0057) and subprocess isolation remain in place

severity: info
category: claim_gate
status: closed
claim: RFC 0057 generative-job subprocess isolation, job-record persistence, and log-redaction contract must be preserved by workflows 0037/0038.
evidence:
- `kayakgen/services/generative_jobs.py` — SubprocessGenerativeJobManager class is unchanged; job state (queued/running/succeeded/failed/cancelled/resumable) enum is unchanged
- `kayakgen/ui/web/generate_state_listener.py` — job state listener installed in RFC 0057 stage 4 is untouched
- `kayakgen/services/generative_jobs.py` — `$HOME` / jobs_root path redaction in log payloads is unchanged
- Workflow 0037 touches only mesh_diagnostics_rows_from_state function; workflow 0038 touches only analysis_view_model::hydro_rows; neither touches subprocess manager or logging
impact: Subprocess isolation and log redaction invariants hold. No regression in evaluator or job-manager contract.
recommended_action: No action required. Baseline for future CFD-in-loop and job workflows.
follow_up: wontfix

---

### AUD-P-010: MeasuredStabilityFixture and StabilityFixturePromotionPacket validators are unchanged

severity: info
category: claim_gate
status: closed
claim: RFC 0056 measured-stability fixture schemas (MeasuredStabilityFixture, StabilityFixturePromotionPacket) and their validators must remain unchanged; workflows 0037/0038 do not touch these.
evidence:
- `kayakgen/eval/stability/measured_fixture.py` — all validators present and unchanged since RFC 0056 landing
- `tests/test_stability_measured_fixture.py` — regression tests remain passing (no changes to validator surface)
- No workflow 0037/0038 code imports or uses these schemas
impact: The RFC 0056 acceptance contract for measured stability fixtures (acceptance thresholds, promotion blockers, reviewer-signature validation) is unaffected by the presentation-layer registries or inline-help additions.
recommended_action: No action required. Baseline for stage-2 acceptance workflows.
follow_up: wontfix

---

### AUD-P-011: CFD opt-in gates (RFC 0046) and cfd_in_loop_evaluator_status contract hold

severity: info
category: claim_gate
status: closed
claim: The three-mechanism opt-in for OpenFOAM-v2512 succeeded path (profile_flag > persistent_setting > env_knob per D027 / RFC 0046) must remain in effect; workflows 0037/0038 do not touch CFD dispatch or opt-in resolution.
evidence:
- `kayakgen/eval/cfd/jobs.py` — RealSolverExecutionOptIn literal and resolve_real_solver_execution_opt_in helper unchanged
- `kayakgen/services/generative_jobs.py` — cfd_in_loop_evaluator_status function unchanged (returns "opt_in_only" / "enabled" / "not_available" per D039)
- `kayakgen/ui/web/generate_spec_form.py:76-80` — CFD_IN_LOOP_ACK_LABEL unchanged; the form-builder surfaces the acknowledgement checkbox under the correct status
- Workflow 0037/0038 do not touch cfd_in_loop status evaluation or opt-in resolution
impact: The RFC 0046 three-tier opt-in precedence is unaffected. CFD-in-loop status assessment for the Generate panel remains accurate.
recommended_action: No action required. Baseline for future CFD-in-loop graduation workflows.
follow_up: wontfix

---

### AUD-P-012: Evaluator subprocess isolation and generative-job records remain auditable

severity: info
category: claim_gate
status: closed
claim: Generative-job records must remain serializable, persistent, and trackable; subprocess isolation must be maintained; workflows 0037/0038 do not weaken this contract.
evidence:
- `kayakgen/services/generative_jobs.py:*` — GenerativeJob Pydantic model with `job_id`, `state`, `created_at`, `completed_at`, `spec`, `result`, `error`, `runner_type` fields; all unchanged
- `~/.local/share/kayakgen/runs/<job_id>/run.json` — persistent on-disk storage; no changes to serialization
- `kayakgen/services/evaluation.py` — subprocess invocation through the runner; no isolation-breaking changes
- Workflow 0037 (mesh diagnostic metadata) and workflow 0038 (hydrostatics registry) are pure presentation-layer changes; neither touches evaluator subprocess dispatch or job serialization
impact: The RFC 0057 generative-job audit trail and subprocess isolation remain intact. Future job introspection, resumption, and forensics remain possible.
recommended_action: No action required. Baseline for compliance with RFC 0054 / RFC 0057 job-management contract.
follow_up: wontfix

---

## Consolidated Summary

Pipeline-integrity audit of the full repository at HEAD `313dfdd` completed. All claim-state, accepted-use, readiness, and acceptance-gate invariants are preserved:

- **Claim-state boundaries:** RawUnvalidatedClaimFields validators enforce boundaries; no claim promotion without evidence.
- **Accepted-fit contract:** EMPTY_STABILITY_FIT_REGISTRY consumption verified across all three D042 call sites; RFC 0058 stage 2/3 semantics hold.
- **Result semantics:** Analytical claim labels (high-angle GZ) resolve correctly to `"unvalidated_hydrostatic_comparison"` under empty registry; result_semantics contract holds.
- **Presentation-layer isolation:** RFC 0060 / RFC 0062 registries remain UI-only; no leak to claim-gate code paths.
- **Inline-help copy:** Workflow 0037 additions (validity-badge title, comparison-source toggle subtitle, mesh chip tooltips, submit-button disabled reason) do not make strengthened claims; RFC / claim_state jargon excluded.
- **Hydrostatics registry:** RFC 0062 HydrostaticsRowMetadata is wired correctly; byte-stable wire payload preserved; registry sourcing verified by regression test.
- **Test coverage:** Vocabulary coverage, registry coverage, and inline-help tests all present and passing.
- **Evaluator isolation:** Subprocess isolation, log redaction, and job-record persistence are unchanged. CFD opt-in gates and cfd_in_loop_evaluator_status contract hold.
- **Artifact-store identity:** Hull.record_hash() / design_hash() contract (RFC 0049) stable across workflows 0037/0038.

No critical, high, or medium findings. No regressions detected. The repository is in a clean, well-tested state suitable for continued development under the RFC 0059 audit cadence.

