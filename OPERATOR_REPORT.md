# Operator Report

Updated: 2026-05-13

## Current State

- Operator-only constraint reaffirmed: design, implementation, and review work
  must be performed by Striatum-assigned agents, with this session limited to
  orchestration, artifact handling, report updates, trunk hygiene, and branch
  cleanup.
- Next maximum-parallel batch queued from the ready backlog: workflows 0033,
  0037, 0038, 0039, 0040, and 0041. Workflows 0034 and 0035 remain queued until
  0033 lands because they depend on generated closed-body evidence.
- Active maximum-parallel batch run IDs:
  `run_f33e467413ba4ca2a4e5e794338d9580` (0033),
  `run_f0ce0eddffee4622a10d02a842cd84ea` (0037),
  `run_7d439091034943ec90848192c9f49136` (0038),
  `run_53f17f26285941c3a3992705772ce07d` (0039),
  `run_48d834656e604d66aa430eb5f60ea643` (0040), and
  `run_4c920dd1311f42a5b0bbac4126af0cbd` (0041).
- The 0033/0037/0038/0039/0040/0041 prompt files now include an operator
  parallelism instruction asking agents to use the maximal number of useful
  sub-agents or parallel workers while preserving their assigned Striatum role.
- Eighteen first-pass review sessions were registered, claimed, acknowledged,
  and launched through their configured process-adapter lanes: Claude for
  traceability, Gemini for domain/browser, and Codex for ops/ops-test.
- Current Striatum CLI state is SQLite-backed while Striatum 1.37.0 enforces
  daemon-required by default, so operator Striatum commands for this batch use
  `STRIATUM_DAEMON_REQUIRED=0`; no Striatum source changes were made.
- The first process-adapter pass did not produce publishable Striatum review
  results: some process parents were lost, several Codex/Gemini jobs exited
  without artifacts or verdicts, and the few generated files used unattested
  operator self-declared bylines. Those unsubmitted files were removed.
- The 18 first-pass review jobs were retried with fresh leases. A second pass
  is running through explicit headless Claude/Gemini/Codex invocations that
  generate markdown artifacts without `author:` bylines; the operator will only
  publish artifacts that include the agent's own `Verdict intent:` line.
- 2026-05-13T17:22:31Z checkpoint: mechanical artifact checks found no
  `author:` bylines. Several Codex ops artifacts were explicit repository
  read-failure artifacts, so they are not publishable. Those six ops/ops-test
  lanes are being retried in parallel with a direct repo working directory and
  sandbox bypass. The Gemini 0040 domain lane from the second pass is still
  running; downstream ledger/build/final jobs remain untouched.
- 2026-05-13T17:29:01Z checkpoint: the second-pass Claude/Gemini batch and the
  Codex ops retry batch finished. The Codex retry cleared the repository-read
  failure artifacts. Three traceability artifacts repeated `Verdict intent:`
  more than once, so those traceability lanes are being retried with a strict
  format override before any review artifact is submitted.
- 2026-05-13T17:34:14Z checkpoint: all 18 first-pass review artifacts were
  mechanically valid and published to Striatum without `author:` bylines. Review
  artifact IDs are:
  0033 `art_31c33028a7af4d48bac8feb5f0e167ab`,
  `art_ab155900ecda4c7ab605441ae6a0dd1b`,
  `art_ffe135063751468cb1cc225df4c684a6`; 0037
  `art_62044238cfb2488192cf48e2efe9ed10`,
  `art_7962a49951cf48d0a7afcb6a57bf1049`,
  `art_2b2b5cf6c2774530a01d45a616f512ad`; 0038
  `art_58223a360c3c4d4e857a8980f8066cf6`,
  `art_665137deaf264e79a7922d39da9063c8`,
  `art_b5b84e3d2c1b4719928fa0d4216fd9bf`; 0039
  `art_076598903e2b467ab53615e76a158ff3`,
  `art_598bb00706ae410cb8769ec64d35fe96`,
  `art_7de2bfd52c3b405ab800cd19983e94ac`; 0040
  `art_20c727dfc7844bfa962423f32cd2c977`,
  `art_5672dc677e554a53b86c7be26b7e5b77`,
  `art_be8c6766c64a41beb097a722a324c42f`; 0041
  `art_007666f675f44bea88b3f07c5b5b5e6a`,
  `art_268d41d46b2c4d268daa61abb4c7e5bc`,
  `art_f20703ca138449adb5a8258850481dd8`.
- Striatum opened human-checkpoint blockers for 0040 `review_domain` and 0041
  `review_browser` because those lanes returned `needs_revision` and the
  workflows have no matching revision cycle. The operator is not overriding
  those review verdicts. Ledger/implementation can proceed for 0033, 0037,
  0038, and 0039; 0040 and 0041 remain blocked pending an owner/workflow
  decision.
- 2026-05-13T17:38:13Z checkpoint: the 0033, 0037, 0038, and 0039 ledger jobs
  were registered, claimed, acknowledged, and launched as four parallel Codex
  GPT-5.5 agents in isolated branch worktrees under `/tmp`. Prompts require
  maximal useful sub-agent use, forbid `author:` bylines, and keep publishing
  and completion with the operator.
- 2026-05-13T17:46:07Z checkpoint: the four unblocked ledger jobs completed
  and were published without `author:` bylines: 0033
  `art_b263fcf6154e4503b62f8ad2a142813a`, 0037
  `art_d7b74a57a6984e678e34511eab735118`, 0038
  `art_cc417ec1fc31408b978f6053f4a16e23`, and 0039
  `art_4d5f25501f044275858079e7803403e0`. Ledger branch commits were pushed:
  0033 `d5b43bd`, 0037 `7b94cbd`, 0038 `461a286`, and 0039 `6d487c8`.
- The failed adapter recovery briefly requeued downstream ledger/build/final
  jobs while clearing stale leases. Those jobs must not be claimed until the
  first-pass review artifacts are published and accepted; operator control is
  preserving the intended gate order.
- `main` includes the completed 0032, 0036, and 0029 workflow landings; the
  workflow code landed through `d13d0ad` before this final report update.
- All temporary workflow branches and worktrees from the 0032/0036/0029 batch
  were pruned locally and remotely; only `main` remains locally.
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
- After the 0032/0036/0029 batch landed, the target repo Striatum Claude/Codex
  skill bundles were refreshed again to match the running 1.37.0 install;
  `striatum doctor` is clean.
- Old merged local and remote topic branches were pruned before and after the
  current implementation batch.
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

## Completed Batch 0032 / 0036 / 0029

- Dependency-safe first batch started with workflows 0032, 0036, and existing
  0029 because they do not depend on generated closed-body construction.
- All nine first-pass review jobs are complete with
  `accept_with_findings` verdicts. Review artifact branches were pushed, then
  rebased onto current `origin/main`.
- Review artifact sessions:
  `operator-0032-traceability`, `operator-0032-domain`, `operator-0032-ops`,
  `operator-0036-traceability`, `operator-0036-domain-source`,
  `operator-0036-ops`, `operator-0029-traceability`,
  `operator-0029-browser-domain`, and `operator-0029-ops`.
- The three findings ledgers are published and complete in Striatum:
  `art_bd9b12ea04dc45db8fff05be455e7031` (0032),
  `art_1887251ffab041479fe97d86e1e7e029` (0036), and
  `art_ee4d220fb5f14ede97b1bd660d25325c` (0029). Ledger commits are pushed on
  the rebased workflow branches: 0029 `2b7e2b6`, 0032 `c164fe1`, and 0036
  `2c23b1d`.
- The three Codex implementation jobs completed with accepted final reviews.
  Patch-summary artifacts:
  `art_96c0b07f08f94ce8b27d7e1da64abbbe` (0032),
  `art_62ff09c30d564368a8e8ec52407a839d` (0036), and
  `art_b0e58a678e764fdbbe91bd71d3ae2902` (0029). Final-review artifacts:
  `art_8a3c5971361749cba97b7b2ecd098e78` (0032),
  `art_c657118cad6c4fa6944ce801c7d4b3c2` (0036), and
  `art_0d917b84e0834ea197a620cd370a0f73` (0029).
- 0032 landed RFC 0021 explicit synthetic closed-volume self-intersection
  diagnostics with `not_checked`, `passed`, `failed`, and `inconclusive`
  status, bounded example pairs, and no `cfd_ready` promotion.
- 0036 landed RFC 0025 claim-state gates and visible warnings for current raw
  analytical resistance and raw local CFD dispatch, without adding real solver
  success, calibrated models, accepted fixtures, or final design-fitness
  claims.
- 0029 landed local `/api/cfd/*` web routes and a compact browser panel over
  existing server-local CFD job records, keeping outputs raw/unvalidated and
  leaving hosted workers, auth, cancellation, real solvers, and validation
  deferred.
- Focused verification after review artifacts:
  `.venv/bin/python -m pytest tests/test_closed_volume.py
  tests/test_cfd_jobs.py tests/test_resistance.py tests/test_compare.py
  tests/test_web.py -q` -> 56 passed.
- Integration verification:
  - After landing 0032: `.venv/bin/python -m pytest tests/test_closed_volume.py
    tests/test_cfd_jobs.py -q` -> 23 passed.
  - After rebasing/landing 0036:
    `.venv/bin/python -m pytest tests/test_cfd_jobs.py tests/test_resistance.py
    tests/test_compare.py tests/test_web.py tests/test_cli.py -q` -> 78 passed.
  - After rebasing/landing 0029:
    `.venv/bin/python -m pytest tests/test_cfd_jobs.py tests/test_web.py
    tests/test_resistance.py tests/test_compare.py tests/test_cli.py -q` ->
    82 passed; `tests/test_web_browser.py -q` -> 1 passed.
  - Final integrated trunk: `.venv/bin/python -m pytest -q` -> 192 passed;
    `git diff --check` -> clean.
- All three workflows are complete in Striatum and fast-forwarded into `main`.

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
