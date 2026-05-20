---
schema_version: striatum.finding.v1
artifact_kind: finding
verdict_intent: accept_with_findings
---

author: reviewer-traceability-claude-opus-4.7-001

# Workflow 0054 Traceability Review

## Scope

Verified every workflow 0054 change traces back to a row in
`docs/workflows/0054-rfc-0057-stage-4-ui-polish/STAGE_4_DECISIONS.md`
or to an existing surface in
`docs/rfcs/0057-generative-search-jobs-and-web-workspace.md`. Cross-
checked the workflow.json job scopes, the seven patch summaries under
`striatum/0054-rfc-0057-stage-4-ui-polish/implementation/`, the stage-4
commit `c8569a1` plus the working-tree polish on
`striatum/0054-daemon-driven-rerun-5`, and the
docs sync (CHANGELOG, RFC 0057, USER_GUIDE, ROADMAP, DECISION_LOG D037,
OPERATOR_REPORT). RFC 0057's `Open Questions` section was inspected
end-to-end to confirm every resolution lands in the implementation.

## Decision-by-decision traceability

| Decision | Implementing track | Concrete artefact | Status |
| --- | --- | --- | --- |
| D-1 form-builder + raw-JSON escape | `implement_form_builder_module` | `kayakgen/ui/web/generate_spec_form.py::render_spec_form_section` with `VExpansionPanels`-wrapped raw-JSON `VTextarea`; `build_spec_from_form_state` round-trips to `SweepSpec`/`SearchSpec` schema versions pulled from the Pydantic models. | ✓ |
| D-2 live admissibility filter | `implement_form_builder_module` | `admissible_objective_metrics()` drops `role="display_only"` and high-angle GZ names; `objective_refusal_reason()` exposes the RFC 0044 refusal structure; `_objectives_block()` raises `GenerateSpecFormError(code="objective_not_admissible", refusal=...)` for inline rendering. | ✓ |
| D-3 form defaults | `implement_form_builder_module` | `initialize_form_state()` pre-fills `BASE_HULL_KEYS = (length_m, beam_oa_m, beam_wl_m, draft_m, Cp)` from current state, seeds `DEFAULT_NSGA2_POPULATION_SIZE=12`, `DEFAULT_NSGA2_GENERATIONS=4`, `DEFAULT_MAX_EVALUATIONS=64`. Operator can clear or override every field. | ✓ |
| D-4 CFD-in-loop opt-in row | `implement_form_builder_module` | `_evaluators_block(state, cfd_in_loop_acknowledged=...)` plus the structured `GenerateSpecFormError(code="cfd_in_loop_ack_required")` refusal. `CFD_IN_LOOP_ACK_LABEL = "I accept evaluation may take orders of magnitude longer"` is wired as the checkbox label. | ✓ |
| D-5 soft 4-job advisory | `implement_form_builder_module` | `CONCURRENCY_ADVISORY_THRESHOLD = 4`, `refresh_concurrency_advisory(app)` reads `manager.list()` and writes `state.generative_concurrency_advisory`. No hard cap path exists. | ✓ |
| D-6 2D scatter + sortable table sync | `implement_frontier_view_module` | `kayakgen/ui/web/generate_frontier_view.py::build_frontier_view_model` returns aligned `rows` + `scatter_points`; color maps via `_CLAIM_STATE_COLOR_TOKENS`; marker shape via `_CONVERGENCE_MARKERS`. `render_frontier_view_section` emits `VDataTable` + matplotlib widget (SVG fallback). | ✓ |
| D-7 3-objective EHVI colour-axis | `implement_frontier_view_module` | `refresh_frontier_view` exposes `generative_frontier_z_metric` only when ≥3 metrics are available; `_z_color_ratio` normalises the third axis; `color_axis = {metric, min, max}` is part of the view-model. | ✓ |
| D-8 click-to-load handoff with undo | `implement_frontier_view_module` | `apply_candidate_to_hull(app, payload)` snapshots `HULL_STATE_FIELDS` into `state.generative_handoff_prior` and writes the toast message; `undo_candidate_handoff(app)` restores it. The `VDataTable.click_row=(ctrl.load_generative_candidate, ...)` wiring delivers the row payload. | ✓ |
| D-9 1 s / 10 s auto-poll | `implement_auto_poll_module` | `kayakgen/ui/web/generate_state_listener.py::compute_cadence_seconds` returns `running_seconds` (default 1.0) iff `has_in_flight_jobs(summaries)` else `idle_seconds` (default 10.0); `install_generate_state_listener` starts a daemon thread; `stop_generate_state_listener` sets the stop event and re-installs are idempotent. Coalescing in `_wrap_manual_refresh` prevents double-hits with manual refreshes. | ✓ |
| D-10 subprocess default + opt-in flag | `implement_subprocess_default` + integrator | `kayakgen/cli/main.py::serve` defaults to `SubprocessGenerativeJobManager` and prints the chosen manager kind; `--jobs-in-process` is the explicit opt-in (Typer flag at `kayakgen/cli/main.py:621`). `KayakgenApp.__init__` also defaults to `SubprocessGenerativeJobManager(jobs_root=_default_generative_jobs_root_for_app())` when no manager is supplied. | ✓ |
| D-11 log redaction | `implement_log_redaction` | `_redact_log_text(text, *, home_dir, jobs_root)` applies longest-prefix-first replacement (`<jobs_root>` then `~`) so a `jobs_root` nested under `$HOME` rewrites correctly. `generative_job_log_payload()` routes through it before returning the web payload. | ✓ |
| D-12 fork-with-new-seed | `implement_fork_with_seed` | `kayakgen/services/generative_jobs_fork.py::fork_generative_job_payload` reuses `manager.start` after `_patch_seed` (NSGA-II or EHVI `algorithm.seed`); sweep jobs raise `ForkError` → HTTP 400 `cannot_fork_sweep`. New `POST /api/generative-jobs/{job_id}/fork` route in `controllers.py`. `GenerativeJob.forked_from` is the only new field; reads of source-job claim state and read-models are unchanged. | ✓ |

## RFC 0057 Open Questions resolution

The working-tree RFC text moves RFC 0057 from `proposed` → `landed`, renames
the route family from `/api/jobs/*` to `/api/generative-jobs/*` everywhere
in the prose, replaces the in-process default narrative with the subprocess
default (and explicit `--jobs-in-process` opt-in), adds `Stage 4 — web
Generate polish` to the implementation path, and replaces the six Open
Questions with the resolutions from `STAGE_4_DECISIONS.md`. Spot-checked
the route names against `controllers.py` (`add_post`, `add_get` calls at
lines 472-494): all eight routes match the RFC text verbatim, plus the new
`/api/generative-jobs/{job_id}/fork` route from D-12.

## Out-of-scope items confirmed absent

- No 3D scatter rendering surface (EHVI v1 max is 3): `generate_frontier_view.py`
  only ever emits 2D scatter + colour axis.
- No "rerun N forks at once" affordance: `fork_generative_job_payload`
  accepts a single `new_seed: int`.
- No SSE/WebSocket push: `install_generate_state_listener` is a
  `threading.Thread` daemon, not an event-stream subscription.
- No new `claim_state`, `readiness_level`, or `accepted_uses` literal: the
  view-model preserves `raw_unvalidated` / `uncalibrated_comparative` and
  routes through the existing claim-admissibility gates.
- No hosted operation, real solver path, or calibrated promotion is enabled.

## Findings recorded (non-blocking)

### NB-T1 — Per-row Fork buttons (closed in this rerun)

The prior cowboy-mode traceability review (committed at `4d15730`) noted
that the integrator's panel-level "Fork with new seed" button bound to
`state.generative_job_id` was a single-row affordance even though D-12
called for the button to live on succeeded rows. The working-tree changes
on `striatum/0054-daemon-driven-rerun-5` resolve this: `app.py` removes
the panel-level button and adds `_render_generate_job_fork_buttons()`,
which iterates `self._generative_manager.list()` and calls
`render_fork_button(self, job_summary=payload)` for every `succeeded`
summary. This closes ledger item NB-1 inside this workflow rather than
deferring it. Mechanical change, no scope creep.

### NB-T2 — `apply_form_to_json` controller is integrator-scoped

The new `app.ctrl.apply_form_to_json` callback and the `Submit Search` /
`Submit Sweep` buttons inside the new generate tab trace to D-1's "form-
builder primary with a collapsible raw-JSON escape hatch": the buttons
serialise form state via `build_spec_from_form_state`, write it to
`state.generative_spec_json`, and submit. This is integrator surface;
the wire format is the existing canonical `SweepSpec` / `SearchSpec`.
No new design decision was made inside the implementation.

### NB-T3 — `forked_from` field is the only schema add

D-12 specifies a new manager primitive but is silent on whether the
forked job carries source-job lineage. `GenerativeJob.forked_from`
(optional) is the minimum addition required to satisfy "Source job's
claim state and read-model semantics are unchanged" while still letting
the operator see what was forked. The field is informational, ignored by
all existing start / cancel / resume / list code, and is explicitly
called out in the docs sync (USER_GUIDE Generate paragraph, RFC 0057
landed note, D037 receipt).

### NB-T4 — Doc-sync touches only authorised paths

The `synchronize_docs` track scope listed CHANGELOG, DECISION_LOG, ROADMAP,
USER_GUIDE, RFC index, RFC 0057 text, and OPERATOR_REPORT. The working-
tree diff confirms only those paths were touched in the docs sync (D037
already existed; the sync verified it). Date update on `docs/ROADMAP.md`
moves "Updated" from 2026-05-17 to 2026-05-20.

## Verdict

`accept_with_findings`. Every shipped artefact in this workflow traces to
either a row in `STAGE_4_DECISIONS.md` or to an established RFC 0057
surface. No decision was made inside the implementation that should have
been an operator choice; no track widened its write scope; no out-of-scope
item from the decisions doc surfaced in the working tree. The four
non-blocking observations above are recorded for the findings ledger but
do not warrant a remediation pass — NB-T1 already landed inside this
rerun, and NB-T2 / NB-T3 / NB-T4 are integrator-scoped mechanics that
the workflow's tracks were authorised to make.
