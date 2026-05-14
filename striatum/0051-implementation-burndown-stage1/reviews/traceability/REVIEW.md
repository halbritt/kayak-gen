---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

author: reviewer-traceability-claude-opus-4.7-001
schema_version: striatum.finding.v1
kind: finding
logical_name: review
run: run_c6989300a86c4c6cb66e44555bb19067
session: sess_855f105ef2da465f9e2674f8c0f00153
job: job_run_c6989300a86c4c6cb66e44555bb19067_review_traceability
lease: lease_374d204501c74daba5dbf843f8c5e82d
date: 2026-05-14

# Traceability Review — Workflow 0051 Stage 1

## Verdict

`accept_with_findings`

All seven implementation lanes are traceable to a workflow 0050 majority
decision and a named RFC, every "what remains deferred" boundary in the
patch summaries lines up with the decision text, no implementation has
silently re-opened a deferred design question, and no patch promotes a
forbidden capability. One scoped contract-boundary follow-up and one
documentation note are remediable in this run.

## Decision-to-Lane Map (D003-D010, RFCs 0036-0043)

| Workflow 0050 decision | RFC anchor | Implementation lane | Patch summary | Traceability |
| --- | --- | --- | --- | --- |
| D010 sweep admissibility (RFC 0009 reconciliation) | RFC 0009 | `implement_docs_status` | `striatum/.../docs_status/PATCH_SUMMARY.md` | RFC index entry flipped from `proposed` to `partial landed sweep-run-record slice` (`docs/rfcs/README.md:25`); RFC 0009 header rewritten with explicit landed/remaining-delta sections (`docs/rfcs/0009-sweep-run-records.md:1-30,116-160`); `docs/ROADMAP.md:94-95,279-309` aligned; `docs/USER_GUIDE.md:175-200` documents current statuses and reserved `stl`. |
| D010 sweep admissibility (objective registry prerequisite) | RFC 0009 | `implement_sweep_objectives` | `striatum/.../sweep_objectives/PATCH_SUMMARY.md` | New `kayakgen/search/objectives.py` adds `ObjectiveMetadata` with metric/label/unit/direction/source_evaluator/availability_rule/claim_state_required/accepted_use_required/role exactly per D010 (`kayakgen/search/objectives.py:25-99`); defaults limited to `GM0_m`, `displacement_error_kg`, `mesh_problem_count` (`kayakgen/search/objectives.py:101-105`); `Rt_N_last` carries `role="explicit_exploratory"` and requires `calibrated_model` + `final_prediction`; reserved `design_fitness` is `claim_gated_reserved`. |
| D003 solver-readiness evidence (Option A + immediate hardening) | RFC 0040 | `implement_readiness_report` | `striatum/.../readiness_report/PATCH_SUMMARY.md` | `ClosedVolumeSolverReadinessReport` matches the RFC 0040 read-model shape (hull_hash, body_ref, body_profile, mesh_package_ref, solver_profile, diagnostic refs, evidence_hashes, gate_status, blockers, warnings, input_semantics) (`kayakgen/eval/mesh_package.py:113-138`); structured `SolverReadinessIssue` records with `code/message/source/ref` (`kayakgen/eval/mesh_package.py:102-110`); explicit SHA-256 algorithm fields on volume-mesh diagnostics; boundary patch/marker metadata; tests `tests/test_solver_readiness.py` cover open-surface, generated-no-volume-mesh, fixture handoff, and synthetic forbidden-promotion cases. Ordinary generated packages remain below `cfd_ready`. |
| D004 CFD solver path (OpenFOAM.com v2512 `interFoam`, watertight-gated) | RFC 0041 | `implement_openfoam_skeleton` | `striatum/.../openfoam_skeleton/PATCH_SUMMARY.md` | Profile name `openfoam-v2512-interfoam-local`, `adapter_name="openfoam_local"`, `required_mesh_readiness="cfd_ready"`, `required_mesh_profile="watertight_solid_resistance_v1"`, `case_template_version="openfoam-v2512-interfoam-dtchull-v1"`, `solver_version_command=["foamVersion"]`, `required_solver_version="v2512"`, expected raw output `postProcessing/forces/0/force.dat`, timeout/log caps all match D004 literally (`kayakgen/eval/cfd/jobs.py:43-60,479-514`). Parser-readable fake output explicitly returns `failed` with `error_kind="solver_success_blocked"` (`kayakgen/eval/cfd/jobs.py:1147-1159`) so no real `succeeded` path can land here. |
| D005 resistance source acceptance (source-review packet first, no promotion) | RFC 0042 | `implement_resistance_source_review` | `striatum/.../resistance_source_review/PATCH_SUMMARY.md` | `SourceReviewVerdict` enum exactly matches RFC 0042 (`citation_only`, `validation_candidate`, `validation_fixture`, `calibration_fixture_candidate`, `calibration_fixture`, `rejected`) and `SOURCE_USE_BY_REVIEW_VERDICT` keeps `rejected → None` so the five RFC 0027 `SourceUse` runtime values are preserved (`kayakgen/eval/calibration.py:13-68`); `ResistanceSourceReviewPacket` carries rights/extraction/measured_quantity/units/hull_envelope/speed_froude_range/uncertainty checklist plus reviewer/verdict/non-promotion reasons (`kayakgen/eval/calibration.py:161-261`); Edinburgh review packet sets `review_verdict="validation_candidate"` with named non-promotion reasons (`kayakgen/eval/calibration.py:366-449`). No source promoted to `validation_fixture` or `calibration_fixture`. |
| D006 calibrated resistance promotion (preserve no-promotion gate) | RFC 0042 / RFC 0027 | `implement_resistance_source_review` (implicit) | same | Resistance output, default registry `SourceUse` values, claim gates, and calibrated-prediction wording are untouched. No `accepted_fit` model version, calibration fixture, or envelope was introduced. |
| D007 high-angle stability (fixed-trim generated-body v1) | RFC 0043 | `implement_high_angle_v1` | `striatum/.../high_angle_v1/PATCH_SUMMARY.md` | `GeneratedBodyGZCurve` adds `method="fixed_trim_generated_body_v1"`, `summary_semantics="grid_bounded"`, `result_semantics="unvalidated_hydrostatic_comparison"`, and `heel_point_metadata` per heel angle (`kayakgen/eval/stability.py:80-137`); default grid `0..90` by 5 deg, strict heel-grid validation rejecting non-finite/non-monotonic values outside `0..90`, caller grids echoed exactly (`kayakgen/eval/stability.py:40-42,779-795`); generated-body branch only runs when RFC 0024 generated-body gate passes (`kayakgen/eval/stability.py:748-776`); synthetic bodies still rejected unless `fixture_only=True`; sealed-deck/flooding/no-safety warnings (`kayakgen/eval/stability.py:60-67`). Real kayak `gz_m`, righting moment, and summaries remain unavailable when any gate fails. |
| D008 browser hosting (out of scope for stage 1) | n/a | (no lane) | n/a | Correctly absent — workflow 0051 RUNBOOK explicitly lists hosted CFD and public production hosting as blocked. |
| D009 desktop parity (web primary, desktop supporting) | n/a | `implement_ui_successors` | `striatum/.../ui_successors/PATCH_SUMMARY.md` | UI work stays in `kayakgen/ui/web/` and web tests; no native desktop rewrite. RFCs 0036/0037/0038/0039 trail correctly: same-seed listener path retained with browser test pinning the behavior (RFC 0036), `EXPORT_MENU_ROWS` consolidated onto `subtitle` (RFC 0037), disabled mesh-package label updated to `Mesh package (CLI only)` (RFC 0038), shared `WebStateSchema` introduced (RFC 0039). No REST payload shapes, export availability, or backend capability changed. |

## Scope Compliance

Every patch stayed inside its declared `write_scope.allowed_paths`. Cross-checked git status against `docs/workflows/0051-implementation-burndown-stage1/workflow.json` and the seven patch summaries:

- `implement_docs_status` touched only `docs/rfcs/README.md`, `docs/rfcs/0009-sweep-run-records.md`, `docs/ROADMAP.md`, `docs/USER_GUIDE.md`, plus its own artifact.
- `implement_sweep_objectives` added `kayakgen/search/objectives.py`, modified `kayakgen/search/compare.py` and `kayakgen/search/__init__.py`, modified `tests/test_compare.py`. (`kayakgen/cli/main.py` and other test files were allowed but unused — narrower is fine.)
- `implement_readiness_report` modified `kayakgen/eval/mesh_package.py`, `kayakgen/eval/volume_mesh.py`, added `tests/test_solver_readiness.py`, modified the listed test files. No edits to `contract.py`, `closed_volume.py`, `generated_closed_body.py`, or `mesh_diagnostics.py` even though they were allowed.
- `implement_openfoam_skeleton` modified `kayakgen/eval/cfd/jobs.py`, `kayakgen/eval/cfd/__init__.py`, `tests/test_cfd_jobs.py`, added `tests/fixtures/openfoam/force.dat`.
- `implement_resistance_source_review` modified `kayakgen/eval/calibration.py` and added `tests/test_calibration.py`. `claims.py` and `resistance.py` were allowed but unmodified (intentionally — the lane was source-review only).
- `implement_high_angle_v1` modified `kayakgen/eval/stability.py` and `tests/test_stability.py` only. `hydrostatics.py` was allowed but unused.
- `implement_ui_successors` modified `kayakgen/ui/web/app.py`, `controllers.py`, `state.py`, and the listed web test files only.

The `OPERATOR_REPORT.md` (root) edits are supervisor heartbeats outside any implementer's scope; they record packet preparation, launch, and completion timestamps and do not change product wording or claims.

## Deferral Handling

All "What Remains Deferred" sections match the workflow 0050 boundary text:

- No production volume mesher, no `cfd_ready` promotion of ordinary generated packages, no real solver success path, no calibrated/validated CFD, no design-fitness claim, no hosted solver — consistent with D003/D004 and RFCs 0040/0041 acceptance criteria.
- Edinburgh stays a `validation_candidate`; no source is promoted to validation/calibration fixture — consistent with D005/D006 and RFC 0042 Open Questions.
- Real kayak `gz_m` is gated behind generated-body diagnostics passing, synthetic bodies remain `fixture_only`, no safety/seaworthiness wording — consistent with D007 and RFC 0043.
- Public hosting, hosted workers, hosted CFD, and PyQt rewrite intentionally absent — consistent with D008/D009.

No patch reopened a workflow 0050 decision question.

## Findings

### F1 — `GeneratedBodyGZCurve` extras cannot flow through `StabilityResult.gz_curve` (must-fix-or-document)

**Where:** `kayakgen/eval/stability.py:112-137`, `kayakgen/eval/contract.py:109-199,353`, `tests/test_stability.py:331-348`.

**What:** The new `GeneratedBodyGZCurve` adds `method` (broader Literal), `summary_semantics`, `result_semantics`, and the load-bearing `heel_point_metadata`. The canonical `GZCurve` in `contract.py` is `extra="forbid"`, and `StabilityResult.gz_curve: GZCurve | None`. The implementer's own test `test_generated_body_v1_metadata_is_scoped_to_direct_evaluator_surface` pins this down: `GZCurve.model_validate(result.model_dump())` raises `ValidationError`. So the per-heel metadata only reaches callers of `evaluate_gz_curve` directly; once a result is round-tripped through `StabilityResult` (or any downstream surface that uses the canonical type), the metadata is silently rejected.

**Traceability impact:** RFC 0043's result contract explicitly authorizes additive per-heel status fields. D007 also calls out per-heel status/residual/iteration metadata as required v1 surface. Today no user surface consumes the metadata (the canonical wiring sets `StabilityResult.gz_curve = None` in this slice), so this does not produce a false claim — but it does mean the v1 evaluator does not yet plumb through the surface RFC 0043 intends.

**Why remediable:** The `remediate_findings` lane has write scope including `kayakgen/eval/` and `tests/`. The fix is to lift the additive fields (`heel_point_metadata`, `method` expansion, `summary_semantics`, `result_semantics`) onto the canonical `GZCurve` so that `StabilityResult` carries the same payload, or to widen `StabilityResult.gz_curve` typing to accept the subtype. The patch summary's "Contract Boundary Note" already documents the intended follow-up.

**Suggested remediation:** Move the additive fields into `kayakgen/eval/contract.py::GZCurve` (still `extra="forbid"` for unknown keys) and let `GeneratedBodyGZCurve` become a no-op subtype, or remove the subtype entirely. Either keeps RFC 0024's body-provenance gate intact while letting the metadata round-trip.

### F2 — Decision Log not updated alongside RFC 0009 reconciliation (non-blocking)

**Where:** `docs/DECISION_LOG.md` (unchanged in this run).

**What:** `implement_docs_status` reconciled the RFC 0009 status in the index, RFC body, roadmap, and user guide — but `docs/DECISION_LOG.md` was outside its write scope. Workflow 0050's `D010` recorded the sweep/search admissibility decision, but there is no decision-log entry tying RFC 0009's status flip from `proposed → partial landed sweep-run-record slice` to a workflow event. This is consistent with the docs_status write scope but leaves a small audit gap.

**Traceability impact:** Low. The RFC index, the RFC itself, and the roadmap all carry the reconciled status; the decision log still cites D010 for the underlying decision. A future reader could cross-check.

**Why remediable:** The `remediate_findings` lane has no `docs/DECISION_LOG.md` in its allowed paths either, so a strict remediation cannot patch the decision log. Recording the reconciliation under `D010`'s implementation entry in `OPERATOR_REPORT.md` (which is in the remediator scope) is sufficient. Alternatively the next workflow can add the decision-log entry.

## Non-Findings (cross-checked but clean)

- No "calibrated", "validated", "production volume mesher", "design fitness", "seaworthy", "capsize", "safety", or "hosted CFD" wording introduced anywhere in the patches.
- `solver_success_blocked` enforces D004's "no real `succeeded` path" boundary at the adapter level, not just in docs.
- `SourceUse` runtime enum still has exactly the five RFC 0027 values; `rejected` is review-only (`tests/test_calibration.py` pins this).
- Default objectives in `objectives.py` exclude `Rt_N_last` and `design_fitness`; raw resistance still triggers exploratory frontier warnings.
- `WebStateSchema` does not change REST payload keys observable from `/api/*` routes (verified by inspecting `controllers.py` deltas and confirming they read state through the schema rather than emitting new keys).
- RFC 0036 "removal-or-pin" choice for `_state_matches_preset_seed`: the implementer correctly pinned-with-test rather than removing, with a concrete browser-test failure observation documented in the patch summary. This is faithful to the RFC's "prove or remove" framing.

## Sources

- `docs/workflows/0051-implementation-burndown-stage1/workflow.json`
- `docs/workflows/0051-implementation-burndown-stage1/RUNBOOK.md`
- `docs/workflows/0051-implementation-burndown-stage1/OPERATOR_REPORT.md`
- `docs/rfcs/0009-sweep-run-records.md`
- `docs/rfcs/0036-trame-seed-listener-proof.md` through `docs/rfcs/0043-high-angle-gz-successor.md`
- `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`
- `striatum/0050-decision-panel-research/final/FINAL_REVIEW.md`
- All seven `striatum/0051-implementation-burndown-stage1/implementation/*/PATCH_SUMMARY.md`
- Source files cited inline above.
