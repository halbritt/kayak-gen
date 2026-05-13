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
- Scaffold committed as `7039878` and pushed to `origin/main`.
- Striatum run `run_ac6771c05d58422da72797fa47edf967` is running on branch
  `striatum/0025-cfd-solver-dispatch-and-jobs`.
- Gate rule: implement local dispatch contracts and unavailable/mock behavior
  before any real solver integration. No fake solver success and no calibrated
  CFD claims.
- Three review lanes for workflow 0025 are complete with
  `accept_with_findings`:
  - traceability `art_40461f93bb8a4cf3a04fe94471a048b4`;
  - domain `art_ee4f71da2bb24dd0931e76dd6f5dc2a5`;
  - ops `art_1a7f17bbb7824ff9a94602e094732fee`.
- Next active step is the workflow 0025 findings ledger.
- The workflow 0025 findings ledger has been written at
  `striatum/0025-cfd-solver-dispatch-and-jobs/ledger/FINDINGS.md`.
  Gate result: proceed with the local dispatch slice only; defer real solvers,
  normalized physical outputs, web job routes, and watertight geometry.
- The ledger was published as `art_6f5c7d26bf5e4df98996d7bb37936282`; next
  active step is implementation.
- Workflow 0025 implementation is claimed as
  `sess_253976cf21164e3fbd921063575922cf`.
- Workflow 0025 implementation is complete locally:
  `kayakgen.eval.cfd` now provides local dispatch job/run/profile records,
  mesh readiness gating, unavailable and mock failed-command states, and
  `kayakgen cfd prepare/status/run/profiles`.
- Verification: focused CFD/CLI tests passed (21), full suite passed (160),
  `git diff --check` is clean, and `striatum --repo . doctor` is clean after
  refreshing Striatum skill/plugin bundles. Ruff remains unavailable in
  `.venv`.
- Workflow 0025 implementation artifact published as
  `art_1cb4d53b1459438a92e77be868636e93`; next active step is final review.
- Workflow 0025 final review accepted as
  `art_1090063be141486aa89dca66630b1424`; Striatum run
  `run_ac6771c05d58422da72797fa47edf967` is complete. Next active step is
  commit, push branch, and fast-forward `main`.

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
