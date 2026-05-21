author: remediator-codex-gpt-5.5-001
schema_version: striatum.patch_summary.v1
kind: patch_summary
logical_name: patch_summary
workflow_id: 0056-rfc-0058-stage2-3-burndown
role: remediator

# Remediation Patch Summary

## Scope

- Fixed MF-1 from `ledger/FINDINGS_LEDGER.md`: the Generate-panel
  serializer now treats the CFD-in-loop acknowledgement as implicit when
  `generative_cfd_in_loop_status == "first_class"`, matching the render path
  that hides the acknowledgement control in that state.
- Preserved the default `opt_in_only` behavior: unacknowledged CFD-in-loop
  requests are still refused unless the evaluator has graduated to
  `first_class`.
- Updated `CHANGELOG.md` and the workflow `OPERATOR_REPORT.md` with the
  remediation note.

## Tests

- `.venv/bin/python -m pytest tests/test_generate_spec_form.py -q`
- `.venv/bin/python -m pytest tests/test_generative_jobs_manager.py tests/test_generative_jobs_subprocess.py tests/test_generative_jobs_web.py -q`

## Notes

- No new evaluator status, claim-state literal, RFC 0046 persistent opt-in
  API, or real CFD-in-loop graduation evidence was introduced.
