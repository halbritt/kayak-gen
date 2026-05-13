# Operator Report

Updated: 2026-05-13

## Current State

- `main` is clean and tracking `origin/main`.
- Workflows 0021, 0022, and 0023 have landed and were pushed to
  `origin/main`.
- Next queued workflow is 0024, watertight solid mesh profile.
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

## Active Workflow

- 0024 watertight solid mesh profile has been scaffolded and validated.
- Gate rule: add a named watertight-solid readiness boundary only if the
  geometry contract is explicit. Otherwise, implement blocked/readiness
  diagnostics without relabeling current open wetted-surface packages as
  watertight or `cfd_ready`.

## Verification Baseline

- Latest full suite after workflow 0023: `.venv/bin/python -m pytest -q` ->
  147 passed.
- `striatum --repo . workflow validate
  docs/workflows/0023-resistance-calibration-dataset-vetting/workflow.json` ->
  valid.
- `striatum --repo . workflow validate
  docs/workflows/0024-watertight-solid-mesh-profile/workflow.json` -> valid.
- `git diff --check` -> clean.
- `striatum --repo . doctor` was clean after the skill refresh in workflow
  0022.
- Ruff is not installed in the current virtualenv, so ruff checks are
  unavailable unless dependencies are added.
