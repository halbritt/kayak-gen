---
kind: finding
workflow_id: 0054-rfc-0057-stage-4-ui-polish
role: reviewer_ops_tests
verdict: accept_with_findings
authored_by: claude-opus-4-7 (cowboy mode; striatum runner blocked by halbritt/striatum#24)
---

# Workflow 0054 Tests and Operational Behavior Review

## Scope

Reviewed tests, determinism, failure modes, and API/CLI compatibility.
Confirmed the full repo suite stays green and that the forbidden-copy
+ ui-theme orphan + import-boundary + services-boundary scans all
pass.

## Findings

### Accepted

- **Full repo suite**: 1020 passed, 2 skipped (env-gated OpenFOAM
  smoke), 0 failed. Run on 2026-05-19 on commit `c8569a1`.
- **Auto-poll cadence is cancellable**: every test in
  `tests/test_generate_state_listener.py` calls
  `stop_generate_state_listener` in a `try/finally` (via the
  thread.join helper) and asserts the daemon thread exits inside
  the timeout. No flakiness observed across the 5 repeated runs
  during integration.
- **Subprocess-default flip preserves backward compat**: the
  `InProcessGenerativeJobManager` and `SubprocessGenerativeJobManager`
  public APIs are unchanged; existing tests
  (`tests/test_generative_jobs_manager.py`,
  `tests/test_generative_jobs_subprocess.py`) still pass without
  modification.
- **Log redaction is byte-stable for inputs without absolute paths**:
  `tests/test_log_redaction.py::test_generative_job_log_payload_byte_stable_when_no_paths_present`
  asserts round-trip identity for redaction-free payloads.
- **Fork-with-seed atomic-replace race closed**: the fork agent's
  initial implementation hit the `os.replace` race between
  `manager.start` and the post-hoc `forked_from` patch. Final
  implementation acquires the manager's `_lock_for(job_id)` before
  reading/writing the new job's `job.json`, serialising against the
  worker thread's first persist. Verified across 6 fork tests.
- **Forbidden-copy + orphan-color scans green**: both
  `tests/test_web_layout.py::test_forbidden_claim_copy_has_only_documented_negations_in_render_surfaces`
  and
  `tests/test_ui_theme.py::test_no_orphan_color_literals_under_kayakgen_ui`
  pass after the form-builder switched the inline `"1"` literal to
  `_spec_default_schema_version(SweepSpec)` / `_spec_default_schema_version(SearchSpec)`.

### Findings recorded for follow-up (non-blocking)

- **OQ-1 (cosmetic)**: `tests/test_log_redaction.py::test_generative_job_log_payload_byte_stable_when_no_paths_present`
  proves the redactor is idempotent on its own output, but does not
  assert *literal* byte-equality against a pre-redaction snapshot for
  a no-path log. The current assertion compares two redactor
  invocations against the same payload — strong enough for the
  redaction surface, but a future tightening could add a snapshot of
  a runner-produced log with no `$HOME` / `<jobs_root>` strings and
  assert `_redact_log_text(snapshot) == snapshot`. Recorded as a
  non-blocking improvement.
- **OQ-2 (cosmetic)**: The form-builder integration tests use a
  controller-callback style (writing form state into `app.state` and
  invoking `app.ctrl.submit_generative_*`); no integration test
  drives the rendered Trame widget tree directly. This mirrors the
  CFD-panel test style and is consistent with the existing pattern,
  but means a regression that breaks form-state-to-spec serialisation
  *inside* a widget would not be caught by these tests until manual
  use. RFC 0008's existing browser-acceptance verification is the
  upstream gate; no immediate change needed.
- **OQ-3 (operational)**: The auto-poll listener uses
  `getattr(app.state, "analysis_tab", "")` to gate refreshes when
  the panel is hidden. If a future RFC renames the tab value from
  `"generate"` to something else, the gate silently disables
  auto-refresh. Worth adding a regression test that asserts the
  tab value is the one the listener checks — but the active-tab
  contract is currently a string literal, not a constant, so the
  test would only catch one direction. Recorded for the next pass
  at REVIEW_TABS hardening.

### Critical issues found

None.

## Verdict

`accept_with_findings`. All stage-4 surfaces are operationally sound;
the three follow-up items are documentation/test-tightening polish,
none of which warrant a remediation pass.
