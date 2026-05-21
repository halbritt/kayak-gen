author: implementer-codex-gpt-5.5-002
schema_version: striatum.patch_summary.v1
kind: patch_summary
logical_name: patch_summary
workflow_id: 0056-rfc-0058-stage2-3-burndown
job_id: implement_cfd_in_loop_status

# Patch Summary

## Changes

- Added `cfd_in_loop_evaluator_status(registry, hull_scope, persistent_opt_in)`
  to `kayakgen/services/generative_jobs.py`.
- Kept the helper additive and structural: accepted records with
  `kind="analytical"` and `kind="cfd_in_loop"` must both cover the requested
  `HullFamilyScope` before status becomes `first_class`.
- Preserved the default and opt-out posture: empty or incomplete registries
  return `opt_in_only`, and `persistent_opt_in=False` wins over graduation.
- Added focused tests in `tests/test_cfd_in_loop_evaluator_status.py` covering
  empty registry, analytical-only, CFD-in-loop-only, both-present,
  non-covering/rejected records, and persistent setting branches.

## Verification

- `.venv/bin/python -m pytest tests/test_cfd_in_loop_evaluator_status.py`
- `.venv/bin/python -m ruff check kayakgen/services/generative_jobs.py tests/test_cfd_in_loop_evaluator_status.py`
