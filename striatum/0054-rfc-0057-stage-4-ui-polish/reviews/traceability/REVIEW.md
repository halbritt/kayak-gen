---
kind: finding
workflow_id: 0054-rfc-0057-stage-4-ui-polish
role: reviewer_traceability
verdict: accept_with_findings
authored_by: claude-opus-4-7 (cowboy mode; striatum runner blocked by halbritt/striatum#24)
---

# Workflow 0054 Traceability Review

## Scope

Verified every change made under workflow 0054 traces back to either
RFC 0057 or `STAGE_4_DECISIONS.md`. No scope creep, no undocumented
refactors, no decisions made inside the implementation that should
have been operator choices.

## Findings

### Accepted as traceable

- **D-1 form-builder + raw-JSON escape** →
  `kayakgen/ui/web/generate_spec_form.py`. Surface matches the
  decision; raw-JSON tab is collapsible (v-expansion-panel); the CLI
  spec shape is the canonical wire format.
- **D-2 live admissibility filter** → `admissible_objective_metrics()`
  excludes `role="display_only"` metrics; `GenerateSpecFormError` carries
  structured codes for inline refusal markup. Verified via
  `tests/test_generate_spec_form.py::test_*_admissibility*`.
- **D-3 pre-fill from current hull** → `initialize_form_state(app)`
  reads `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `Cp` off
  `app.state` for the `base_hull` defaults; algorithm and budget
  defaults match the RFC text.
- **D-4 CFD-in-loop opt-in row** → `_evaluators_block(state, cfd_in_loop_acknowledged=...)`
  refuses to admit the CFD-in-loop evaluator without the
  acknowledgement checkbox. Ack copy is the pre-vetted
  "I accept evaluation may take orders of magnitude longer" string
  (passes the forbidden-claim scrub).
- **D-5 soft 4-job advisory** → `refresh_concurrency_advisory(app)` reads
  `manager.list()` and writes to `state.generative_concurrency_advisory`.
- **D-6 2D scatter + sortable table** →
  `kayakgen/ui/web/generate_frontier_view.py::build_frontier_view_model`
  produces both scatter and table view-models from a single payload.
- **D-7 3-objective pair selector + colour-mapped third axis** →
  `refresh_frontier_view` exposes the third metric as a colour axis;
  the `VSelect` for `z_metric` is hidden when fewer than 3 metrics
  are available.
- **D-8 click-to-load handoff** → `apply_candidate_to_hull` mutates
  `app.state` and captures the prior snapshot in
  `state.generative_handoff_prior`; `undo_candidate_handoff` restores
  it. Single-button-restore flow per the decision.
- **D-9 1 s / 10 s auto-poll** →
  `kayakgen/ui/web/generate_state_listener.py::compute_cadence_seconds`
  encodes the cadence rule; `install_generate_state_listener` runs
  in a daemon `threading.Thread`; pauses when the Generate tab is
  not the active review tab.
- **D-10 subprocess default + `--jobs-in-process` opt-in** →
  `kayakgen/cli/main.py::serve` defaults to
  `SubprocessGenerativeJobManager`; the legacy `--jobs-subprocess`
  flag is gone (`tests/test_cli_serve.py::test_serve_help_documents_jobs_in_process`).
- **D-11 log redaction** → `_redact_log_text` strips `$HOME` and
  `<jobs_root>`; longest-target-first ordering handles the nested case.
- **D-12 fork with new seed** → `fork_generative_job_payload` patches
  `algorithm.seed`, calls `manager.start`, then writes
  `forked_from=source_id` on the new job under the manager's per-job
  lock to avoid racing the worker's first persist. Sweep jobs raise
  `ForkError`.

### Minor traceability observations (non-blocking)

- The integrator wires a single panel-level "Fork with new seed"
  button bound to `state.generative_job_id` rather than rendering
  `render_fork_button` once per Pareto-frontier row. The decision
  text (D-12) says "one-click 'Fork with new seed' button on
  succeeded rows" — the current panel-level button is correct only
  when the operator's `generative_job_id` matches the row they want
  to fork. Per-row wiring of `render_fork_button` inside the
  frontier-view table is the cleaner finish; logged as a
  non-blocking successor.
- The frontier-view module's matplotlib widget falls back to an
  SVG-only render in headless environments; the RFC does not
  require matplotlib specifically, so this fallback is in-scope.
  Worth documenting in the user guide if matplotlib goes deprecated.

## Verdict

`accept_with_findings`. Every shipped artefact traces to a decision row
or a pre-existing RFC. The per-row fork-button wiring is a
non-blocking successor that does not warrant a remediation pass in
this workflow.
