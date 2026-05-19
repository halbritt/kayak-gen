---
kind: finding
workflow_id: 0054-rfc-0057-stage-4-ui-polish
role: final_reviewer
verdict: accept
authored_by: claude-opus-4-7 (cowboy mode; striatum runner blocked by halbritt/striatum#24)
---

# Workflow 0054 Final Review

## Scope check against `STAGE_4_DECISIONS.md`

Each of the twelve operator-affirmed decisions is reflected in the
shipped behavior on `main` at commit `f27f181`:

| # | Decision | Shipped artefact | Verified |
| --- | --- | --- | --- |
| D-1 | Form-builder + raw-JSON escape | `generate_spec_form.py` | ✅ |
| D-2 | Live admissibility filter | `admissible_objective_metrics()` + `GenerateSpecFormError` | ✅ |
| D-3 | Pre-fill from current hull | `initialize_form_state(app)` | ✅ |
| D-4 | CFD-in-loop opt-in row with explicit ack | `_evaluators_block(state, cfd_in_loop_acknowledged=...)` | ✅ |
| D-5 | Soft 4-job advisory | `refresh_concurrency_advisory(app)` | ✅ |
| D-6 | 2D scatter + sortable table | `build_frontier_view_model` | ✅ |
| D-7 | 3-objective pair selector + colour-mapped third axis | `refresh_frontier_view` | ✅ |
| D-8 | Full handoff + undo toast | `apply_candidate_to_hull` + `undo_candidate_handoff` | ✅ |
| D-9 | 1 s / 10 s auto-poll | `compute_cadence_seconds` + `install_generate_state_listener` | ✅ |
| D-10 | Subprocess default + `--jobs-in-process` opt-in | `kayakgen/cli/main.py::serve` | ✅ |
| D-11 | Home + jobs_root log redaction | `_redact_log_text` + routed via `generative_job_log_payload` | ✅ |
| D-12 | One-click fork with new seed | `generative_jobs_fork.py` + `POST /api/generative-jobs/{job_id}/fork` + panel button | ✅ |

## Blocked items remain blocked

- Real solver execution — gated by RFC 0041/0046 opt-ins; no stage-4
  surface elevated that posture.
- Calibrated fitting — RFC 0027 / 0054 own those gates; untouched.
- Hosted/public deployment — D023 still defers it.
- Safety, seaworthiness, design-fitness, final-prediction claims —
  the forbidden-copy scrub in `tests/test_web_layout.py` stayed
  green.

## Review findings disposition

- Three reviewer artefacts produced (traceability/claims/ops+tests).
- Zero must-fix findings.
- Four non-blocking successor items recorded in the findings ledger
  (per-row Fork buttons; snapshot-assert literal byte-stability of
  the redactor; widget-tree integration tests; constant-ify
  `REVIEW_TABS` tab values).

## Validation evidence

- `git diff --check`: clean on `c8569a1`.
- Full repo suite: 1020 passed, 2 env-gated OpenFOAM skips.
- Forbidden-claim scrub: green.
- UI theme orphan-color scan: green.
- Import-boundary + services-boundary scans: green.
- Ruff: clean across `kayakgen/` and `tests/`.

## Verdict

`accept`.

## Workflow execution note

Workflow 0054 was scaffolded and prepared via striatum
(`run_971f9a5aa58786f53499eeca0969a7d2`) but the runner's
`supervise send --packet-id` flow rejected the IDs returned by
`claim-next` on the v1.55.0 CLI (filed at
<https://github.com/halbritt/striatum/issues/24>). The run was
cancelled and the workflow ran cowboy-mode under the operator's
existing kayak-gen authorisation. This final review and the upstream
reviews/ledger/remediation stand as the cowboy-mode equivalent of
the daemon-driven trail; the workflow scaffold remains re-runnable
on `main` once the upstream fix lands.
