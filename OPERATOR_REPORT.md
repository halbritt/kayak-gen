# Operator Report

Updated: 2026-05-13

## Current State

- `main` is clean and tracking `origin/main`.
- Workflows 0021, 0022, 0023, and 0024 have landed and were pushed to
  `origin/main`.
- Next queued workflow is 0025, CFD solver dispatch and jobs.
- Root report was created after compaction because only per-workflow reports
  were present in `docs/workflows/*/OPERATOR_REPORT.md`.

## Completed Since Backlog Queue

- 0021 web plots and comparison UI: landed compact web analysis/comparison
  views, tests, and RFC/status updates.
- 0022 generalized trim and GZ stability: landed explicit longitudinal load
  components, fixed-body upright trim equilibrium, CLI/sweep summaries, tests,
  and truthful high-angle GZ deferral.
- 0023 resistance calibration dataset vetting: added the University of
  Edinburgh Pacific-canoe dataset as validation-only source metadata, kept
  RFC 0012 proposed, and left resistance uncalibrated.
- 0024 watertight solid mesh profile: added
  `watertight_solid_resistance_v1` as a blocked readiness profile, exposed
  profile selection in `mesh-package`, and kept current packages below
  `cfd_ready`.

## Active Workflow

- 0025 CFD solver dispatch and jobs has been scaffolded and validated.
- Gate rule: implement local dispatch contracts and unavailable/mock behavior
  before any real solver integration. No fake solver success and no calibrated
  CFD claims.

## Verification Baseline

- Latest full suite after workflow 0023: `.venv/bin/python -m pytest -q` ->
  147 passed.
- `striatum --repo . workflow validate
  docs/workflows/0023-resistance-calibration-dataset-vetting/workflow.json` ->
  valid.
- `striatum --repo . workflow validate
  docs/workflows/0024-watertight-solid-mesh-profile/workflow.json` -> valid.
- `striatum --repo . workflow validate
  docs/workflows/0025-cfd-solver-dispatch-and-jobs/workflow.json` -> valid.
- `git diff --check` -> clean.
- `striatum --repo . doctor` was clean after the skill refresh in workflow
  0022.
- Ruff is not installed in the current virtualenv, so ruff checks are
  unavailable unless dependencies are added.
