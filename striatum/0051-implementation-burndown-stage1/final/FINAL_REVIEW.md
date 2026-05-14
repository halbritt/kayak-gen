---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept"
---

author: final-reviewer-claude-opus-4.7-001
schema_version: striatum.finding.v1
kind: finding
logical_name: final_review
run: run_c6989300a86c4c6cb66e44555bb19067
session: sess_dd399aa9d53d49dbab8043ebc9a6bfcb
job: job_run_c6989300a86c4c6cb66e44555bb19067_final_review
lease: lease_da45b375e2e64a8d994d7e4d2f126026
date: 2026-05-14

# Final Review — Workflow 0051 Implementation Burn-Down Stage 1

## Verdict

`accept`

Workflow 0051 executed exactly the scaffolded shape: seven disjoint Codex
implementation lanes against the workflow 0050 / RFC 0009-0043 accepted scope,
three independent reviews (Claude traceability, Codex ops/tests, Gemini
claims), a deduplicated findings ledger, a Codex remediation pass on both
must-fix items, and validated evidence. Both must-fix findings are remediated
with regression tests. Both non-blocking ledger items remain non-blocking
successor scope and are recorded in the operator report. Every no-claims
boundary that workflow 0050 fixed is still in place. `git diff --check` is
clean, `python -m pytest -q` reports `383 passed`, and `python -m compileall
-q kayakgen tests` is clean.

## Scope Compliance — All Implementation Within Accepted Scope

Each of the seven parallel implementation lanes mapped one-to-one to an
accepted RFC and a workflow 0050 decision, and stayed inside its declared
write scope. I reconfirmed this against the patch summaries, the implementer
file lists, and the worktree diff:

| Lane | RFC / decision | Scope outcome |
| --- | --- | --- |
| `implement_docs_status` | RFC 0009 / D010 | RFC index, RFC 0009 header/body, ROADMAP, USER_GUIDE only. No runtime change. |
| `implement_ui_successors` | RFCs 0036-0039 / D009 | `kayakgen/ui/web/{app,controllers,state}.py`, three web test files. No REST payload, export availability, or backend capability change. |
| `implement_sweep_objectives` | RFC 0009 / D010 | New `kayakgen/search/objectives.py`, `compare.py`, `__init__.py`, `tests/test_compare.py`. Defaults stay `GM0_m`, `displacement_error_kg`, `mesh_problem_count`. |
| `implement_readiness_report` | RFC 0040 / D003 | `kayakgen/eval/mesh_package.py`, `volume_mesh.py`, four test files including new `tests/test_solver_readiness.py`. Ordinary packages stay below `cfd_ready`. |
| `implement_openfoam_skeleton` | RFC 0041 / D004 | `kayakgen/eval/cfd/{jobs,__init__}.py`, `tests/test_cfd_jobs.py`, `tests/fixtures/openfoam/force.dat`. Profile name, mesh-gate, version probe, raw parser, and `solver_success_blocked` match the decision text literally. |
| `implement_resistance_source_review` | RFC 0042 / D005-D006 | `kayakgen/eval/calibration.py`, new `tests/test_calibration.py`. Edinburgh stays `validation_candidate`. |
| `implement_high_angle_v1` | RFC 0043 / D007 | `kayakgen/eval/stability.py`, `tests/test_stability.py`. Default `0..90` by 5 deg grid, fixed upright trim, per-heel metadata, sealed-body/no-safety warnings. |

D008 (browser hosting) is correctly absent from stage 1 — RUNBOOK explicitly
keeps hosted CFD and public production hosting blocked. No lane reopened a
workflow 0050 decision.

## Findings Resolution

The findings ledger
(`striatum/0051-implementation-burndown-stage1/ledger/FINDINGS_LEDGER.md`)
recorded `accept_with_must_fix_findings` over MF1 (OpenFOAM stale output) and
MF2 (generated-body GZ metadata round-trip), plus two non-blocking items
(NB1 stale web CFD status copy, NB2 absent RFC 0009 reconciliation row in
`docs/DECISION_LOG.md`).

### MF1 remediated — OpenFOAM reruns clear stale outputs

`kayakgen/eval/cfd/jobs.py:1008-1026` adds a `_clear_openfoam_run_outputs(case)`
call inside `OpenFoamLocalAdapter.run()` before the subprocess invocation. Any
prior `case/openfoam/postProcessing/forces/**` content and the prior
`openfoam-raw-result.json` are removed before the configured command starts.
Cleanup failures are persisted as a terminal `failed` record with the new
`error_kind="output_cleanup_failed"`. The regression test the ledger required
exists at `tests/test_cfd_jobs.py:1242-1296`: it runs a fake interFoam command
that writes parser-readable `force.dat`, asserts the resulting
`solver_success_blocked` failure persists the raw manifest, then reruns the
same prepared job with a zero-exit/no-output command and asserts the second
run is `missing_output` with no `drag_force_n`, no `openfoam-raw-result.json`,
and no surviving `force.dat`.

### MF2 remediated — Canonical `GZCurve` round-trips v1 metadata

`kayakgen/eval/contract.py:109-242` adds typed `GZHeelPointMetadata` (with
`extra="forbid"` of its own), expands `GZCurve.method` to include
`"fixed_trim_generated_body_v1"`, and adds `heel_point_metadata`,
`summary_semantics` (`"grid_bounded"` only), and `result_semantics`
(`"unvalidated_hydrostatic_comparison"` only). `GZCurve` itself stays
`extra="forbid"`, and the new `_availability_matches_payload` validator
requires `len(heel_point_metadata) == len(heel_deg)` for computed
`fixed_trim_generated_body_v1` results. The regression at
`tests/test_stability.py:332` replaces the prior rejection-pinning test with
the round-trip test the ledger required: a generated-body v1 evaluator result
now survives `GZCurve.model_validate(result.model_dump())` and
`StabilityResult` validation without dropping metadata.

### NB1 (web CFD status copy) and NB2 (DECISION_LOG row for RFC 0009)

Both stay non-blocking by the ledger's own disposition. NB1 is correctly
deferred — the fixture-local-command line is misleading but the
raw/unvalidated warnings are still correct, no false claim is surfaced, and
the remediation lane did not have web-UI write scope. NB2's underlying
decision (D010) is already in `docs/DECISION_LOG.md`; the missing item is a
durable bookkeeping row that the remediation lane could not author because
`docs/DECISION_LOG.md` was outside its write scope. The operator report at
`docs/workflows/0051-implementation-burndown-stage1/OPERATOR_REPORT.md`
records the RFC 0009 reconciliation event. A future docs workflow can add
the durable row if the project wants the explicit receipt; that is exactly
what the ledger's "non-blocking" framing authorizes.

## No-Claims Boundaries — Still Intact

I cross-checked every no-claims boundary listed in
`docs/ROADMAP.md:33-59`, in the workflow 0051 RUNBOOK, and in the workflow
0050 final review against the current worktree:

- **Calibrated resistance.** No source promoted to `validation_fixture` or
  `calibration_fixture`. `SOURCE_USE_BY_REVIEW_VERDICT` keeps
  `rejected → None`; the five runtime `SourceUse` values are unchanged. The
  Edinburgh review packet sets `validation_candidate` with named
  non-promotion reasons. Sweep objective metadata keeps `Rt_N_last` as
  `explicit_exploratory` with `claim_state_required="calibrated_model"` and
  `accepted_use_required="final_prediction"`, and the reserved
  `design_fitness` objective is `claim_gated_reserved`.
- **Real CFD success.** No real `succeeded` path. Parser-readable fake
  OpenFOAM output explicitly returns
  `error_kind="solver_success_blocked"`. Solver readiness gating
  (`required_mesh_profile="watertight_solid_resistance_v1"`, readiness
  `cfd_ready`) is enforced before the adapter runs.
- **Production volume meshing / ordinary `cfd_ready` promotion.** The
  `ClosedVolumeSolverReadinessReport` is explanatory only. Ordinary
  generated packages remain `cfd_surface_candidate`; only the existing
  fixture-backed handoff can report `ready_for_profile`.
- **Generated closed body as production input.** Generated-body evidence
  still requires matching diagnostics, hashes, and profile gates before any
  promotion. The high-angle v1 evaluator only runs after the RFC 0024
  generated-body gate passes; synthetic bodies still require
  `fixture_only=True`.
- **High-angle stability / safety / seaworthiness.** v1 results are labeled
  `result_semantics="unvalidated_hydrostatic_comparison"` and
  `summary_semantics="grid_bounded"`. The assumptions and warnings list
  fixed upright trim, hull-fixed passive CG, sealed deck/no cockpit opening,
  deck immersion, flooding/downflooding not modeled, active paddler not
  modeled, and no safety/seaworthiness claim.
- **Browser hosting and desktop parity.** No browser hosting work landed.
  UI changes stayed in `kayakgen/ui/web/`; no native desktop rewrite.

## Documentation Updates

`CHANGELOG.md` (Unreleased / Fixed) records the must-fix remediation
explicitly, including that the OpenFOAM path remains
failed/raw-unvalidated and that high-angle stability output remains an
unvalidated hydrostatic comparison. `OPERATOR_REPORT.md` (root) and
`docs/workflows/0051-implementation-burndown-stage1/OPERATOR_REPORT.md`
both record the lane completions, review verdicts, ledger outcome, and
remediation validation, with byline overrides and the
`--allow-no-process-execution` artifact-publication note disclosed in
context.

## Validation Evidence

I reran the gates the workflow promises in this session:

- `git diff --check` — passed (no output).
- `python -m pytest -q` — `383 passed in 116.80s` against the combined
  worktree.
- `python -m compileall -q kayakgen tests` — clean.

`ruff` is intentionally absent from this environment; every implementation
patch summary and the ops/tests review record this as an environment
limitation rather than a product finding. No required test was skipped
without justification.

## Risks And Follow-Ups (Non-Blocking)

- NB1 (web CFD status copy) should be picked up by a small web-controllers
  workflow whenever the next UI cleanup batch lands.
- NB2 (DECISION_LOG row for RFC 0009 reconciliation) is durable bookkeeping
  the operator report already covers; a future docs-only workflow can add
  the explicit row.
- The OpenFOAM adapter remains parser-readable but `solver_success_blocked`.
  A real `succeeded` path is still gated on RFC 0040 production
  volume-mesh evidence, exactly as D004 requires.
- Generated-body v1 high-angle GZ results are computable through the
  evaluator but remain `result_semantics="unvalidated_hydrostatic_comparison"`
  and are not yet surfaced on CLI/sweep/comparison/desktop/web. That is the
  intended posture per D007 until product-surface gates land.

## Sources

- `docs/PRD.md`, `docs/USER_GUIDE.md`, `docs/ROADMAP.md`,
  `docs/DECISION_LOG.md` (D003–D010), `docs/rfcs/README.md`,
  `docs/rfcs/0009-sweep-run-records.md`,
  `docs/rfcs/0036-0043*.md`.
- `docs/workflows/0051-implementation-burndown-stage1/RUNBOOK.md`,
  `OPERATOR_REPORT.md`, `prompts/final_review.md`,
  `workflow.json`.
- `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`,
  `striatum/0050-decision-panel-research/final/FINAL_REVIEW.md`.
- All seven
  `striatum/0051-implementation-burndown-stage1/implementation/*/PATCH_SUMMARY.md`.
- `striatum/0051-implementation-burndown-stage1/reviews/{claims,traceability,ops_tests}/REVIEW.md`.
- `striatum/0051-implementation-burndown-stage1/ledger/FINDINGS_LEDGER.md`.
- `striatum/0051-implementation-burndown-stage1/remediation/PATCH_SUMMARY.md`.
- Source files cited inline (`kayakgen/eval/cfd/jobs.py`,
  `kayakgen/eval/contract.py`, `kayakgen/eval/stability.py`,
  `tests/test_cfd_jobs.py`, `tests/test_stability.py`).
