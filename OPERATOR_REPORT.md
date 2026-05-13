# Operator Report

Updated: 2026-05-13

## Current State

- `main` is clean and even with `origin/main` at `2ae4037`.
- Active implementation batch:
  `striatum/0032-closed-volume-self-intersection-diagnostics`,
  `striatum/0036-cfd-calibration-claim-gates`, and
  `striatum/0029-web-cfd-job-routes`.
- Active run IDs:
  `run_04735e0767704843a93cb507c202231f` (0032),
  `run_38b1b70956eb48eabbf39449375579ed` (0036), and
  `run_9126a2d7dd7a4fa3b9cbf6815a8e0c98` (0029).
- Workflows 0021, 0022, 0023, 0024, and 0025 have landed and were pushed to
  `origin/main`.
- Striatum skill/plugin bundle refresh landed on `main` after workflow 0025.
- Workflow 0026, docs roadmap and user guide, has landed and was pushed to
  `origin/main`.
- Workflow roadmap scaffolding for queued items 0027-0031 has landed on
  `main`.
- Residual roadmap RFC/workflow scaffolding for RFCs 0021-0030 and workflows
  0032-0041 landed on `main` as `83b9b56`.
- `CHANGELOG.md` has landed from git/RFC/workflow history, and `AGENTS.md`
  tells future agents to update it for RFC/workflow/user-facing changes.
- After workflow 0027 landed, the target repo Striatum Claude/Codex skill
  bundles were refreshed to match the running 1.36.0 install; `striatum doctor`
  is clean.
- Old merged local and remote topic branches were pruned before the current
  implementation batch; the only local topic branches now are the three active
  Striatum run branches listed above.
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

## Residual Roadmap Drafting

- Requested scope: RFC gaps, major implementation deferrals, and older partial
  RFC cleanup. RFCs may revise or supersede earlier RFCs where that improves
  progress.
- Scaffold fanout:
  - Worker A completed RFCs 0021-0022 and workflows 0032-0033 for
    closed-volume self-intersection diagnostics and generated closed-body
    construction. Both workflow definitions validated.
  - Worker B completed RFCs 0023-0024 and workflows 0034-0035 for watertight
    volume-mesh handoff and high-angle `GZ` generated-body handoff. Both
    workflow definitions validated.
  - Worker C completed RFCs 0025-0027 and workflows 0036-0038 for
    CFD/calibration claim gates, fixture-first CFD adapter, and resistance
    calibration acceptance. All three workflow definitions validated.
  - Worker D completed RFCs 0028-0030 and workflows 0039-0041 for older
    partials: plumb-stem closure semantics, design constraint surfacing, and
    web hosted browser acceptance. All three workflow definitions validated.
  - Worker E completed read-only dependency analysis.
- Proposed first simultaneous implementation batch after scaffolds land:
  workflows 0032, 0036, and existing workflow 0029. Scope limits:
  self-intersection diagnostics; CFD/calibration claim gates; and web CFD job
  routes limited to existing local-dispatch/unavailable states, not real solver
  success.
- Blocked dependency chain: 0033 waits on 0032; 0034 and 0035 wait on 0033;
  0037 and 0038 wait on 0036; real 0031 output waits on generated closed-body
  evidence; watertight real-solver work waits on generated body plus
  volume-mesh evidence.
- Branch hygiene rule for this phase: land scaffold batches to `main`
  frequently, push `main`, then delete merged local and remote topic branches.
- Scaffold batch landed on `main` as `83b9b56`; the
  `striatum/residual-roadmap-rfcs` branch was pushed, fast-forwarded into
  `main`, pushed to `origin/main`, then deleted locally and remotely.
- Verification completed for the scaffold batch: JSON syntax valid for
  workflows 0032-0041, Striatum workflow validation passed for all 10,
  `git diff --check` is clean, ASCII check is clean, and
  `striatum --repo . doctor` is clean.

## Active Batch 0032 / 0036 / 0029

- Dependency-safe first batch started with workflows 0032, 0036, and existing
  0029 because they do not depend on generated closed-body construction.
- All nine first-pass review jobs are complete with
  `accept_with_findings` verdicts. Review artifact branches were pushed:
  0029 as `99e840d`, 0032 as `2fb822d`, and 0036 as `0285633`.
  Artifact work is isolated by branch worktree: the root checkout remains on
  0029, `/home/halbritt/git/kayak-gen.worktrees/0032` is on 0032, and
  `/home/halbritt/git/kayak-gen.worktrees/0036` is on 0036.
- Review artifact sessions:
  `operator-0032-traceability`, `operator-0032-domain`, `operator-0032-ops`,
  `operator-0036-traceability`, `operator-0036-domain-source`,
  `operator-0036-ops`, `operator-0029-traceability`,
  `operator-0029-browser-domain`, and `operator-0029-ops`.
- Current gate: three Codex ledger jobs are claimed and acknowledged:
  `operator-0032-ledger`, `operator-0036-ledger`, and
  `operator-0029-ledger`. Their outputs will define the accepted implementation
  slices before any code changes.
- Focused verification after review artifacts:
  `.venv/bin/python -m pytest tests/test_closed_volume.py
  tests/test_cfd_jobs.py tests/test_resistance.py tests/test_compare.py
  tests/test_web.py -q` -> 56 passed.
- Next local gate: publish the three findings ledgers through Striatum, then
  run Codex implementation jobs with maximal useful sub-agent fanout.

## Completed Workflow 0027

- Roadmap scaffold/changelog batch landed on `main` as `76c33e6`.
- Workflow 0027 run `run_6a701b70b294436ba529dce7bb705b9b` ran on
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
- Workflow 0027 landed on `main` as `97efa00`.

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
