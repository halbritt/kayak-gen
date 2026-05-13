# Operator Report

Updated: 2026-05-13

## Current State

- `main` is clean and tracking `origin/main` at `f2a3bb9`.
- Workflows 0021, 0022, 0023, 0024, and 0025 have landed and were pushed to
  `origin/main`.
- Striatum skill/plugin bundle refresh landed on `main` after workflow 0025.
- Workflow 0026, docs roadmap and user guide, has landed and was pushed to
  `origin/main`.
- Workflow roadmap scaffolding for queued items 0027-0031 is complete locally
  and awaiting validation/landing.
- `CHANGELOG.md` has been created locally from git/RFC/workflow history, and
  `AGENTS.md` now tells future agents to update it for RFC/workflow/user-facing
  changes.
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

## Active Workflow

- 0026 docs roadmap and user guide has been scaffolded and validated.
- Workflow 0025 implementation landed as `9c7d541` and pushed to
  `origin/main`.
- Striatum bundle refresh committed as `d443dbe` and pushed to `origin/main`.
- Workflow 0026 scaffold committed as `420112a` and pushed to `origin/main`.
- Striatum run `run_b51d0f3bc0e3409b824f120a59676733` is active on branch
  `striatum/0026-docs-roadmap-user-guide`.
- Gate rule: documentation-only reconciliation. Do not implement runtime code,
  real solver execution, web job routes, calibrated resistance, high-angle GZ,
  closed-volume geometry, or watertight solid generation.
- Three review lanes for workflow 0026 are complete with
  `accept_with_findings`: documentation accuracy, user guide, and roadmap.
- The workflow 0026 findings ledger has been written at
  `striatum/0026-docs-roadmap-user-guide/ledger/FINDINGS.md`.
  Gate result: proceed with documentation-only implementation.
- Active implementation scope is stale documentation reconciliation: PRD
  current-vs-roadmap wording, backlog queue history/next-work wording,
  operator report state, user guide, and proposed roadmap RFC/navigation work.
- Workflow 0026 implementation is complete locally: added `docs/USER_GUIDE.md`,
  a root `README.md`, proposed RFCs 0016-0020, corrected PRD current-vs-roadmap
  claims, and updated the backlog queue/RFC index.
- Verification: `.venv/bin/python -m pytest -q` -> 160 passed;
  `git diff --check` -> clean; `striatum --repo . doctor` -> clean.
- Workflow 0026 implementation artifact published as
  `art_b89cfa2056bc4766974dc7ecdbc995ac`; next active step is final review.
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
- Current landing plan: validate all five workflow definitions, create a
  Striatum branch, commit, push, fast-forward `main`, and push `main`.

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
