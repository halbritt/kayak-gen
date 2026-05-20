---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept
---

author: final-reviewer-claude-opus-4.7-001

# Workflow 0054 Final Review (daemon-driven rerun)

## Scope

Re-run of the workflow 0054 final review under the daemon-driven
runner on branch `striatum/0054-daemon-driven-rerun-5`. Confirms RFC
0057 stage 4 is within accepted scope, the 12 operator decisions
in `docs/workflows/0054-rfc-0057-stage-4-ui-polish/STAGE_4_DECISIONS.md`
are reflected in shipped behavior, all review findings are closed or
recorded as non-blocking successors, blocked items remain blocked,
and validation evidence is green.

The prior `final/FINAL_REVIEW.md` (cowboy-mode at `f27f181`) is
superseded by this artifact; the cowboy run's `accept` verdict is
preserved as historical context in `ledger/FINDINGS_LEDGER.md`.

## Decision fidelity — STAGE_4_DECISIONS.md

| # | Decision | Shipped artefact | Verified |
| --- | --- | --- | --- |
| D-1 | Form-builder primary + collapsible raw-JSON escape | `kayakgen/ui/web/generate_spec_form.py::render_spec_form_section`; `build_spec_from_form_state` round-trips to `SweepSpec`/`SearchSpec`; `app.ctrl.apply_form_to_json` integrator callback wires the form into the canonical wire format. | ✅ |
| D-2 | Live admissibility filter + inline errors | `admissible_objective_metrics()` (display-only + claim-gated filter); `objective_refusal_reason()`; `GenerateSpecFormError(code="objective_not_admissible", refusal=...)` for inline rendering. | ✅ |
| D-3 | Pre-fill from current hull; NSGA-II `(12, 4)`; budget `max_evaluations=64` | `initialize_form_state()` with `BASE_HULL_KEYS`, `DEFAULT_NSGA2_POPULATION_SIZE=12`, `DEFAULT_NSGA2_GENERATIONS=4`, `DEFAULT_MAX_EVALUATIONS=64`. Every field overridable. | ✅ |
| D-4 | CFD-in-loop opt-in row with explicit acknowledgement | `_evaluators_block(state, cfd_in_loop_acknowledged=...)` and `CFD_IN_LOOP_ACK_LABEL = "I accept evaluation may take orders of magnitude longer"`; `GenerateSpecFormError(code="cfd_in_loop_ack_required")` blocks submission until ticked. | ✅ |
| D-5 | Soft 4-job in-flight warning; no hard cap | `CONCURRENCY_ADVISORY_THRESHOLD = 4`; `refresh_concurrency_advisory(app)` reads `manager.list()` and writes `state.generative_concurrency_advisory`. | ✅ |
| D-6 | 2D scatter synced with sortable table; colour by `claim_state`, shape by `ConvergenceFlag` | `kayakgen/ui/web/generate_frontier_view.py::build_frontier_view_model` returns aligned `rows` + `scatter_points`; `_CLAIM_STATE_COLOR_TOKENS` and `_CONVERGENCE_MARKERS` carry the mapping; `render_frontier_view_section` renders `VDataTable` + matplotlib widget. | ✅ |
| D-7 | 2D scatter + objective-pair selector + colour-mapped third axis | `refresh_frontier_view` exposes `generative_frontier_z_metric` only when ≥3 metrics are available; `_z_color_ratio` normalises the third axis; `color_axis = {metric, min, max}` is part of the view-model. | ✅ |
| D-8 | Click-to-load full handoff with undo toast | `apply_candidate_to_hull(app, payload)` snapshots `HULL_STATE_FIELDS` into `state.generative_handoff_prior`; `undo_candidate_handoff(app)` restores the snapshot; `VDataTable.click_row=(ctrl.load_generative_candidate, ...)`. | ✅ |
| D-9 | 1 s while `{queued, running}`, 10 s otherwise; cancellable; no SSE | `compute_cadence_seconds`; `install_generate_state_listener` runs a daemon thread; `stop_generate_state_listener` is idempotent; `_wrap_manual_refresh` coalesces manual + auto refreshes; `_refresh_terminal_details` fans out per-job refresh after terminal transitions. | ✅ |
| D-10 | Subprocess default; `--jobs-in-process` explicit opt-in; print chosen manager | `kayakgen/cli/main.py::serve` defaults to `SubprocessGenerativeJobManager` (Typer flag at `kayakgen/cli/main.py:621`) and prints the manager kind on startup; `KayakgenApp.__init__` also defaults to `SubprocessGenerativeJobManager(jobs_root=_default_generative_jobs_root_for_app())`. | ✅ |
| D-11 | `$HOME → ~`; paths under resolved `jobs_root → <jobs_root>`; no-op for redaction-free | `_redact_log_text(text, *, home_dir, jobs_root)` with longest-prefix-first replacement; `generative_job_log_payload()` routes through it; byte-stable for empty input. | ✅ |
| D-12 | One-click "Fork with new seed" on succeeded rows; new manager primitive + route | `kayakgen/services/generative_jobs_fork.py::fork_generative_job_payload` (NSGA-II + EHVI seed patch; sweeps refused with `ForkError`); `POST /api/generative-jobs/{job_id}/fork`; per-succeeded-row buttons via `app._render_generate_job_fork_buttons()` + `render_fork_button(self, job_summary=payload)`; `GenerativeJob.forked_from` lineage field is the only schema addition; source-job claim state and read-model semantics unchanged. | ✅ |

## Blocked items remain blocked

- **Real solver execution.** No stage-4 surface elevates the RFC 0041/0046 opt-in posture. `result_semantics="raw_unvalidated"` envelope is untouched.
- **Calibrated fitting.** RFC 0027 / 0054 own those gates; stage 4 makes no calibrated promotion or comparative-to-calibrated transition.
- **Hosted / public deployment.** D023 still defers it. Subprocess default is local-only.
- **Safety, seaworthiness, design-fitness, final-prediction claims.** `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces` stays green; reviewer/claims confirmed all new copy (CFD ack, concurrency advisory, "Fork with new seed", fixed display-only caption, refusal labels).
- **3D scatter for ≥4 objectives, "rerun N forks at once", SSE/WebSocket push.** None present in the codebase; traceability spot-checked.
- **No new `claim_state`, `readiness_level`, or `accepted_uses` literal.** View-model carries `raw_unvalidated` / `uncalibrated_comparative` only.

## Findings disposition

Source reviews (under `striatum/0054-rfc-0057-stage-4-ui-polish/reviews/`):

- `reviews/claims/REVIEW.md` — **PASSED**. CFD ack copy, concurrency advisory, objective admissibility, fork label, log redaction, frontier metric scrub, and `test_web_layout` forbidden-claim scan all verified green. No remediation required.
- `reviews/ops_tests/REVIEW.md` — **accepted with one medium finding (MF-1)** + a non-blocking coverage note (NB-1).
- `reviews/traceability/REVIEW.md` — **`accept_with_findings`**. All 12 decisions traced. Four non-blocking items (NB-T1–NB-T4) recorded; NB-T1 already closed inside the rerun via working-tree polish; NB-T2 / NB-T3 / NB-T4 are integrator-scoped mechanics inside authorised write scopes.

Ledger items (`ledger/FINDINGS_LEDGER.md`):

- **MF-1** (cancellation tests could pass when cancellation was ignored) — **closed**. The remediation pass (`remediation/PATCH_SUMMARY.md`) added a controlled `_ControlledRunner` cancellation test in `tests/test_generative_jobs_manager.py`, a controlled REST-route cancellation test in `tests/test_generative_jobs_web.py`, and a file-backed subprocess-runner cancellation test in `tests/test_generative_jobs_subprocess.py`. Each requires terminal `state="resumable"`, `error.kind="cancelled_by_operator"`, and `resumable_from_checkpoint is True`; the subprocess test also asserts `cancel.flag` cleanup after the child writes terminal state. Spot-verified: `tests/test_generative_jobs_manager.py:176-177,198-199`, `tests/test_generative_jobs_subprocess.py:152,172,191-192`, `tests/test_generative_jobs_web.py:266-267`.
- **NB-1** (sleep-sensitive auto-poll assertions) — recorded as a non-blocking successor. The auto-poll tests passed locally; replacing the short wall-clock sleeps with a fake clock / stepped poll loop is residual robustness work, not a stage-4 defect.
- **C-1** (claims & user-facing boundaries) — closed (no action; claims review passed).
- **C-2** (per-row fork buttons) — closed in this rerun via the working-tree change to `app.py` (panel-level button removed; `_render_generate_job_fork_buttons()` iterates succeeded summaries).
- **C-3** (integrator-scoped `apply_form_to_json`) — closed (no action; traces to D-1; preserves canonical wire format).
- **C-4** (`forked_from` lineage field) — closed (no action; minimum informational schema addition; source-job semantics unchanged).
- **C-5** (docs-sync scope) — closed (no action; sync stayed inside authorised paths).

No must-fix items remain open. All findings have a recorded disposition.

## Docs & decision-log surface

Spot-checked the working-tree docs sync against the traceability review:

- `CHANGELOG.md` — stage 4 landing + daemon-run remediation entries present in the Unreleased section.
- `docs/DECISION_LOG.md` — D037 receipt records the 12 operator-affirmed decisions.
- `docs/ROADMAP.md` — Updated date moved to 2026-05-20; RFC 0057 landing reflected.
- `docs/USER_GUIDE.md` — Generate panel paragraph references form-builder, CFD ack, fork, log redaction, and the subprocess default.
- `docs/rfcs/0057-generative-search-jobs-and-web-workspace.md` — status `landed`, Open Questions section replaced with the six resolved rows + the additional stage-4 decisions; routes renamed to `/api/generative-jobs/*`; Stage 4 added to the Implementation Path.
- `docs/workflows/0054-rfc-0057-stage-4-ui-polish/OPERATOR_REPORT.md` — daemon-run remediation entry dated 2026-05-20 is present.

## Validation evidence

Run from `/home/halbritt/git/kayak-gen` on `striatum/0054-daemon-driven-rerun-5`:

- Focused stage-4 suite — `.venv/bin/python -m pytest tests/test_generative_jobs_manager.py tests/test_generative_jobs_subprocess.py tests/test_generative_jobs_web.py tests/test_generate_spec_form.py tests/test_generate_frontier_view.py tests/test_generate_state_listener.py tests/test_generative_jobs_fork.py tests/test_log_redaction.py`: **91 passed in 32.03 s**.
- Boundary scans — `.venv/bin/python -m pytest tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces tests/test_ui_theme.py::test_no_orphan_color_literals_under_kayakgen_ui tests/test_import_boundaries.py`: **83 passed in 1.05 s**.
- Full repo suite — `.venv/bin/python -m pytest`: **1047 passed, 4 skipped in 367.99 s**. The four skips are the documented opt-in OpenFOAM-v2512 smoke/stage tests gated on `KAYAKGEN_OPENFOAM_SMOKE=1`.
- Lint — `.venv/bin/ruff check kayakgen tests`: **All checks passed**.
- Whitespace — `git diff --check`: clean (no output).

## Verdict

`accept`.

Every line in `STAGE_4_DECISIONS.md` is reflected in shipped behavior on the
review branch; every must-fix ledger item is closed; the full repo suite, the
forbidden-claim scrub, the ui-theme orphan-color scan, and the import-boundary
scans are green; ruff is clean and `git diff --check` is quiet; no blocked
posture (real solver, calibrated fitting, hosted deployment, safety /
seaworthiness / design-fitness / final-prediction claims) was elevated.
