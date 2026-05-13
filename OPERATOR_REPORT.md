# Operator Report

Updated: 2026-05-13

## Current State

- `main` and `origin/main` were even at `76c33e6` before workflow 0027 landing;
  the current accepted landing branch is
  `striatum/0027-closed-volume-geometry-contract`.
- Workflows 0021, 0022, 0023, 0024, and 0025 have landed and were pushed to
  `origin/main`.
- Striatum skill/plugin bundle refresh landed on `main` after workflow 0025.
- Workflow 0026, docs roadmap and user guide, has landed and was pushed to
  `origin/main`.
- Workflow roadmap scaffolding for queued items 0027-0031 has landed on
  `main`.
- `CHANGELOG.md` has landed from git/RFC/workflow history, and `AGENTS.md`
  tells future agents to update it for RFC/workflow/user-facing changes.
- After workflow 0027 landed, the target repo Striatum Claude/Codex skill
  bundles were refreshed to match the running 1.36.0 install; `striatum doctor`
  is clean.
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
- 0025 CFD solver dispatch and jobs: landed local dispatch job/run/profile
  records, mesh readiness gating, unavailable and mock failed-command states,
  and `kayakgen cfd prepare/status/run/profiles`. Real solvers, normalized
  physical outputs, web job routes, watertight geometry, and calibrated CFD
  claims remain deferred.
- Striatum bundle refresh: updated Striatum skill/plugin bundles on `main` after
  the 0025 landing.

## Previous Workflow 0026

- Workflow 0026 documentation-only reconciliation is complete: it added
  `docs/USER_GUIDE.md`, a root `README.md`, proposed RFCs 0016-0020, corrected
  PRD current-vs-roadmap claims, and updated the backlog queue/RFC index.
- Verification: `.venv/bin/python -m pytest -q` -> 160 passed;
  `git diff --check` -> clean; `striatum --repo . doctor` -> clean.
- Workflow 0026 final review accepted as
  `art_e8356a0cabe24fd7b806c78a5091d7a0`; Striatum run
  `run_b51d0f3bc0e3409b824f120a59676733` is complete.
- Workflow 0026 landed as `f2a3bb9` and `main` is fast-forwarded to
  `origin/main`.

## Roadmap Execution Queue

- 0027 closed-volume geometry contract: scaffold complete via parallel worker.
- 0028 real CFD solver adapter: scaffold complete via parallel worker.
- 0029 web CFD job routes: scaffold complete via parallel worker.
- 0030 resistance calibration fixture: scaffold complete locally after the
  agent thread limit was reached.
- 0031 high-angle GZ and secondary stability: scaffold complete locally after
  the agent thread limit was reached.
- Next queued implementation workflows after 0027 are 0028-0031.

## Active Workflow 0027

- Roadmap scaffold/changelog batch landed on `main` as `76c33e6`.
- Workflow 0027 run `run_6a701b70b294436ba529dce7bb705b9b` is active on
  branch `striatum/0027-closed-volume-geometry-contract`.
- Three review artifacts and the findings ledger are published. The ledger
  allows only a safe slice: explicit synthetic closed-volume diagnostics and
  evidence-based watertight dispatch rejection; generated hull-plus-deck closure
  and any `cfd_ready` handoff remain blocked.
- Implementation is complete locally across code, tests, docs, RFC 0016, and
  changelog updates. Targeted verification:
  `.venv/bin/python -m pytest tests/test_closed_volume.py tests/test_cfd_jobs.py tests/test_mesh_package.py -q`
  -> 21 passed.
- Full verification passed: `.venv/bin/python -m pytest -q` -> 167 passed;
  `git diff --check` -> clean.
- Final review accepted with findings as `art_3d03d49d6c814726aa9c59e7e99bde8f`;
  Striatum run `run_6a701b70b294436ba529dce7bb705b9b` is complete.
- Next gate: commit, push branch, fast-forward `main`, and push `main`.

## Verification Baseline

- Latest full suite after workflow 0025: `.venv/bin/python -m pytest -q` ->
  160 passed.
- `striatum --repo . workflow validate
  docs/workflows/0023-resistance-calibration-dataset-vetting/workflow.json` ->
  valid.
- `striatum --repo . workflow validate
  docs/workflows/0024-watertight-solid-mesh-profile/workflow.json` -> valid.
- `striatum --repo . workflow validate
  docs/workflows/0025-cfd-solver-dispatch-and-jobs/workflow.json` -> valid.
- `striatum --repo . workflow validate
  docs/workflows/0026-docs-roadmap-user-guide/workflow.json` -> valid.
- `git diff --check` -> clean.
- `striatum --repo . doctor` was clean after the Striatum bundle refresh that
  landed after workflow 0025.
- Ruff is not installed in the current virtualenv, so ruff checks are
  unavailable unless dependencies are added.
