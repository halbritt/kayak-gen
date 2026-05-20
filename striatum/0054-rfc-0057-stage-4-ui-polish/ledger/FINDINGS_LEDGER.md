---
schema_version: striatum.findings_ledger.v1
artifact_kind: findings_ledger
summary_count: 2
---

author: findings-ledger-codex-gpt-5.5-001
schema_version: striatum.findings_ledger.v1
kind: findings_ledger
logical_name: findings_ledger
workflow_id: 0054-rfc-0057-stage-4-ui-polish
role: findings_ledger

# Workflow 0054 Findings Ledger

## Source Reviews

- `reviews/claims/REVIEW.md` — passed; no claim-boundary remediation.
- `reviews/ops_tests/REVIEW.md` — accepted with one medium operational test finding.
- `reviews/traceability/REVIEW.md` — accepted with non-blocking traceability notes; one prior fork-button note is already closed in this rerun.
- `final/FINAL_REVIEW.md` — historical cowboy-mode final review retained for context, but this daemon-run ledger is based on the current review artifacts above.

## Must-fix Remediation Items

### MF-1: Cancellation tests can pass when cancellation is ignored

**Origin:** `reviews/ops_tests/REVIEW.md`

**Decision / contract:** RFC 0057 stage 4 D-10 makes subprocess execution the default for `kayakgen serve`, and RFC 0057 defines cancellation as a durable job-manager route/manager operation that should leave a resumable checkpoint when observed between candidate emissions.

**Finding:** Current cancellation coverage accepts successful completion as a passing outcome after cancellation is requested. In `tests/test_generative_jobs_manager.py`, `test_manager_cancel_transitions_to_resumable` permits `state in ("resumable", "succeeded")`, and `test_manager_resume_after_cancel` returns early if the job finishes before reaching `resumable`. The same pattern appears in `tests/test_generative_jobs_subprocess.py::test_subprocess_manager_cancel_via_flag`, `tests/test_generative_jobs_subprocess.py::test_subprocess_manager_resume_after_cancel`, and `tests/test_generative_jobs_web.py::test_post_cancel_and_resume_lifecycle`.

**Risk:** A regression where the in-process runner or subprocess runner stops polling `progress_sink.should_cancel()` / `cancel.flag` can still pass the fast-sweep tests because the job reaches `succeeded` before the assertion requires cancellation semantics. That leaves the stage-4 operational cancellation path under-tested.

**Required remediation scope:** Add at least one deterministic cancellation test that controls the candidate-emission seam or runner progress sink so cancellation is observed before terminal completion. The test should require:

- terminal `state == "resumable"`;
- `error.kind == "cancelled_by_operator"`;
- `resumable_from_checkpoint is True`;
- subprocess `cancel.flag` cleanup after the child writes terminal state, for the subprocess-manager path.

This is a test-strengthening item only. It does not authorize a new cancellation API, hard job cap, queue system, SSE/WebSocket progress channel, or any change to the existing RFC 0057 state vocabulary.

## Non-blocking Successor Items

### NB-1: Replace sleep-sensitive auto-poll assertions with a stepped clock or loop seam

**Origin:** `reviews/ops_tests/REVIEW.md` coverage note.

**Current state:** Auto-poll listener coverage passed locally, but it uses short wall-clock sleeps. That is acceptable for this workflow, but remains more scheduler-sensitive than a fake clock or directly stepped poll loop.

**Successor scope:** In a future UI-test hardening pass, add a fake-clock or stepped-poll seam for `kayakgen.ui.web.generate_state_listener` tests so cadence, terminal refresh, teardown, reinstall, and coalescing behavior can be asserted without relying on real sleeps.

**Why non-blocking:** The reviewer reported the full focused and full-suite test runs as passing. This is residual test robustness, not a functional defect in stage-4 behavior.

## Closed / No-action Findings

### C-1: Claims and user-facing boundaries

**Origin:** `reviews/claims/REVIEW.md`.

**Disposition:** No action. The review passed the Generate panel copy, objective admissibility filtering, frontier metric scrubbing, fork label, log redaction, and forbidden-claim verification. No remediation or successor item is needed.

### C-2: Per-row fork buttons

**Origin:** `reviews/traceability/REVIEW.md` NB-T1.

**Disposition:** Closed in this rerun. The traceability review records that the prior panel-level fork affordance was replaced with per-succeeded-job rendering via `_render_generate_job_fork_buttons()` and `render_fork_button(self, job_summary=payload)`.

### C-3: Integrator-scoped form serialization callback

**Origin:** `reviews/traceability/REVIEW.md` NB-T2.

**Disposition:** No action. `app.ctrl.apply_form_to_json` and the Submit Search / Submit Sweep callbacks are traced to D-1's form-builder primary path and preserve the existing CLI spec wire format.

### C-4: `forked_from` lineage field

**Origin:** `reviews/traceability/REVIEW.md` NB-T3.

**Disposition:** No action. The optional `GenerativeJob.forked_from` field is the minimum informational schema addition needed for fork lineage. It does not change source-job claim state or read-model semantics.

### C-5: Documentation sync scope

**Origin:** `reviews/traceability/REVIEW.md` NB-T4.

**Disposition:** No action. The docs-sync changes stayed within the authorized files and did not widen runtime behavior or design scope.
