---
schema_version: "striatum.patch_summary.v1"
artifact_kind: "patch_summary"
---

author: remediator-codex-gpt-5.5-001
date: 2026-05-14
run: run_c6989300a86c4c6cb66e44555bb19067
session: sess_210c9c921a1b4260b0dab022a0115621
job: job_run_c6989300a86c4c6cb66e44555bb19067_remediate_findings
lease: lease_c6bf7a34f8244feeadeb495affc2666b

# Patch Summary - Review Findings Remediation

## Scope

Remediated the two must-fix findings from the workflow 0051 findings ledger:
stale OpenFOAM raw output on rerun, and generated-body GZ metadata failing the
canonical stability contract round trip.

## Files Changed

- `CHANGELOG.md`
- `OPERATOR_REPORT.md`
- `docs/workflows/0051-implementation-burndown-stage1/OPERATOR_REPORT.md`
- `kayakgen/eval/cfd/jobs.py`
- `kayakgen/eval/contract.py`
- `kayakgen/eval/stability.py`
- `tests/test_cfd_jobs.py`
- `tests/test_stability.py`
- `striatum/0051-implementation-burndown-stage1/remediation/PATCH_SUMMARY.md`

## What Landed

- Added OpenFOAM per-run output cleanup before solver command execution. The
  adapter removes the stale `case/openfoam/postProcessing/forces/` tree and
  `openfoam-raw-result.json` before running the configured command, and records
  a stable `output_cleanup_failed` failure if cleanup itself fails.
- Added a regression test that first creates parser-readable OpenFOAM fake
  output, then reruns the same prepared job with a clean zero-exit/no-output
  command. The second run now records `missing_output` and does not reuse stale
  drag data or a stale raw-result manifest.
- Lifted generated-body GZ v1 metadata into the canonical contract by adding
  typed `GZHeelPointMetadata`, the `fixed_trim_generated_body_v1` method value,
  `heel_point_metadata`, `summary_semantics`, and `result_semantics` to
  `kayakgen.eval.contract.GZCurve` while keeping `extra="forbid"`.
- Updated `GeneratedBodyGZCurve` to use the canonical metadata type and replaced
  the rejection-pinning test with a round-trip test through `GZCurve` and
  `StabilityResult`.
- Updated changelog and workflow/operator reports with factual remediation
  status and no-claims boundaries.

## Boundaries Preserved

- No real OpenFOAM `succeeded` path is enabled. Parser-readable fake output
  still records `failed` with `solver_success_blocked`.
- OpenFOAM output remains `raw_unvalidated`; no calibrated CFD, final
  prediction, or design-fitness claim was added.
- Generated-body high-angle stability remains gated by the existing body
  diagnostics and is labeled as an unvalidated hydrostatic comparison, not a
  safety, seaworthiness, capsize, or final design-fitness result.
- Ordinary generated packages remain below production solver readiness unless
  the existing fixture-backed evidence path passes.

## Validation

- `python -m pytest tests/test_cfd_jobs.py::test_openfoam_parser_readable_force_dat_does_not_enable_succeeded_path tests/test_cfd_jobs.py::test_openfoam_rerun_ignores_stale_force_dat_and_raw_result -q` - 2 passed.
- `python -m pytest tests/test_stability.py::test_generated_body_v1_metadata_round_trips_through_canonical_contract tests/test_stability.py::test_generated_body_hull_hash_mismatch_returns_unavailable tests/test_stability.py::test_gz_curve_rejects_legacy_minimal_payload_without_provenance -q` - 3 passed.
- `python -m pytest tests/test_cfd_jobs.py -q` - 40 passed.
- `python -m pytest tests/test_stability.py -q` - 36 passed.
- `git diff --check` - passed.
- `python -m compileall -q kayakgen tests` - passed.
- `python -m pytest -q` - 383 passed in 118.87s.

## Artifact Publication Note

Publishing this artifact required `--allow-no-process-execution` because Codex
created and edited the file with the `apply_patch` tool, which does not emit a
Striatum `process_executions` row for the exact artifact path. The override is
limited to this workflow-local remediation artifact; git status, validation
commands, and file content confirm it remains inside the packet write scope.

## Worktree Note

The shared worktree already contained the seven workflow 0051 implementation
patches and review artifacts when this remediation started. This patch only
intentionally adds the remediation changes listed above and does not revert or
rewrite sibling-lane work.
