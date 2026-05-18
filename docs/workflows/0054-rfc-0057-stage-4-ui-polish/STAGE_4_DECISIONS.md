# RFC 0057 Stage 4 — Operator Decisions

Captured 2026-05-18 from a 12-question operator interview against the RFC 0057
Open Questions section and the deferred UX items from stage 2. Implementers
must treat this as the authoritative resolution; reopening a row requires a
new RFC.

| # | Decision | Implementing track |
| --- | --- | --- |
| D-1 | **Spec input**: form-builder primary with a collapsible raw-JSON escape hatch. The CLI spec shape is the canonical wire format; the form serializes to it. | `implement_form_builder_module` |
| D-2 | **Spec validation timing**: live filtering of the objective picklist by claim-admissibility; inline errors next to the offending row; Submit disabled while errors exist. | `implement_form_builder_module` |
| D-3 | **Form defaults**: pre-fill `base_hull` from the current single-hull view; algorithm defaults to NSGA-II with `population_size=12`, `generations=4`; budget defaults to `max_evaluations=64`. Operator can clear or override every field. | `implement_form_builder_module` |
| D-4 | **CFD-in-loop**: per-job evaluator-block opt-in row with an explicit acknowledgement checkbox ("I accept evaluation may take orders of magnitude longer"). RFC 0046 opt-in mechanisms still apply at the runner. | `implement_form_builder_module` |
| D-5 | **Concurrency**: soft warning banner once 4 jobs are in-flight; no hard cap. Subprocess manager handles isolation; the parent never blocks. | `implement_form_builder_module` |
| D-6 | **Pareto-frontier viz**: 2D scatter synced with a sortable table; color points by `claim_state`, shape by `ConvergenceFlag` (RFC 0052). | `implement_frontier_view_module` |
| D-7 | **3-objective EHVI viz**: 2D scatter with an objective-pair selector; the third objective surfaces as a colour-mapped axis on the points and a column in the synced table. | `implement_frontier_view_module` |
| D-8 | **Candidate handoff**: clicking a Pareto-frontier row fully loads the candidate into the single-hull view (parameter rail + 3D scene rebuild) with a one-click undo toast that restores the prior state. | `implement_frontier_view_module` |
| D-9 | **Auto-refresh cadence**: poll every 1 s while any job state is in {queued, running}; every 10 s otherwise. Cancellable listener; no SSE/WebSocket. | `implement_auto_poll_module` |
| D-10 | **`kayakgen serve` default**: subprocess manager. `--jobs-in-process` becomes the explicit in-process opt-in. Print the chosen manager kind on startup. | `implement_subprocess_default` |
| D-11 | **Log redaction**: strip `$HOME` (replace with `~`) and rewrite paths under the resolved `jobs_root` to start with `<jobs_root>`. No-op for redaction-free payloads. | `implement_log_redaction` |
| D-12 | **Fork with new seed**: one-click "Fork with new seed" button on succeeded Pareto rows. New `POST /api/generative-jobs/{job_id}/fork` route; new `kayakgen.services.generative_jobs_fork` module. Source job's claim state and read-model semantics are unchanged. | `implement_fork_with_seed` |

## Out of scope (deferred)

- 3D scatter rendering for 4+ objective runs (EHVI v1 max is 3).
- "Rerun N forks at once" / seed-sweep affordance — single-fork only in this
  stage.
- Server-Sent Events / WebSocket push for job progress; polling is enough
  for the single-operator local-tool posture.
- Hosted demo, real-solver in-loop validation, calibrated prediction, or
  any change to the `result_semantics: "raw_unvalidated"` envelope.

## Blocked items (must remain blocked)

- Real solver execution: gated by the existing RFC 0041/0046 opt-ins; no
  stage-4 surface elevates that posture.
- Calibrated fitting: RFC 0027 / 0054 own those gates.
- Hosted/public deployment: D023 in `docs/DECISION_LOG.md` defers it.
- Safety, seaworthiness, design-fitness, final-prediction claims: the
  forbidden-copy scrub in `tests/test_web_layout.py` is authoritative.
