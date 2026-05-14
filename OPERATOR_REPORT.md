# Operator Report

Updated: 2026-05-14

## Current State

- Operator-only constraint reaffirmed: design, implementation, and review work
  must be performed by Striatum-assigned agents, with this session limited to
  orchestration, artifact handling, report updates, trunk hygiene, and branch
  cleanup.
- 2026-05-14T10:40Z checkpoint: scaffolded workflow 0049
  (`roadmap-reconciliation`) to have Codex author/integrate a contributor-facing
  `docs/ROADMAP.md`, three independent review lanes for backlog completeness,
  no-claims/domain boundaries, and ops/sequencing, plus Claude final review.
  The scaffold is documentation/workflow-only; no roadmap content or runtime
  behavior was operator-authored.
- 2026-05-14T13:06Z checkpoint: workflow 0049 run
  `run_3497e451ce5a401293549cd3c9238554` is running on branch
  `striatum/0049-roadmap-reconciliation`. The Codex roadmap-author lane is
  claimed under session `sess_8341316c7d4244eca8b187258fe86e5d`, supervised
  with byline `author: roadmap-author-codex-gpt-5.5-001`, and has been sent
  the authoring packet. The packet requires maximal useful sub-agent use and
  forbids runtime/test changes.
- 2026-05-14T13:24Z checkpoint: workflow 0049 roadmap-author job completed.
  The first supervised stdin attempt stalled, so the job was retried and
  adopted under attested Codex session `sess_536e15b2e4ac4dd0b3999ffa06a32594`
  with artifact `art_448f5cb138934ddab6e96a1f3c1c1aa9`. A publish override was
  recorded because the adopted artifact came from the direct Codex CLI fallback
  while a live supervisor supplied the Codex byline. Changed files are docs and
  workflow artifacts only; `git diff --check` and forbidden path status checks
  passed.
- 2026-05-14T13:52Z checkpoint: workflow 0049 completed. First-pass reviews
  accepted backlog completeness (`art_3a93b6c2aa884b97bf4eb5e1683e1f43`),
  no-claims/domain boundaries (`art_ca532557c4794d0d9d1eb9a2b918f499`), and
  ops/sequencing (`art_bb1690a581b84ad78b39273f5f480a88`). Integration
  published `art_ecfe8711acc94251bdc0ae6241c1f385`; Claude final review
  published `art_526881c4995942d2947c9e05b74d2156` and completed with
  `accept`. Striatum marks run `run_3497e451ce5a401293549cd3c9238554`
  completed with no open blockers. Changes remain documentation/workflow
  artifacts only; no runtime, test, `.striatum`, solver, calibration,
  watertight-readiness, final-prediction, hosted-operation, full-parity, or
  high-angle stability capability changed.
- 2026-05-14T14:10Z checkpoint: scaffolded workflow 0050
  (`decision-panel-research`) as a design-only research workflow for the eight
  open roadmap decisions. The workflow runs one research packet per decision,
  then Claude/Codex/Gemini panel votes for each question, then strict majority
  integration into decision-log/roadmap/changelog docs and final review. It
  explicitly blocks dependent implementation burn-down unless a decision has
  at least two matching panel votes. Scaffold validation and `git diff --check`
  passed; no runtime or test paths changed.
- 2026-05-14T14:18Z checkpoint: workflow 0050 run
  `run_dc0a506896094745b380fd3ad2535d59` is running on branch
  `striatum/0050-decision-panel-research`. All eight Codex research packets
  are claimed and running in parallel under live supervisors: browser hosting,
  calibrated resistance, desktop parity, high-angle stability, resistance
  sources, solver path, solver readiness, and sweep/optimization. Each packet
  is design/research-only and writes only its workflow-local research artifact.
- 2026-05-14T10:00Z checkpoint: corrected stale RFC status/index labels for
  landed safe slices RFC 0016, RFC 0022, RFC 0025, RFC 0027, and RFC 0031.
  This was operator bookkeeping only; no runtime behavior or product claims
  changed. Next step is to scaffold a Striatum workflow for the narrow UI
  cleanup/follow-up work and then resume backlog burn-down with parallel
  Striatum runs where dependencies permit.
- 2026-05-14T10:05Z checkpoint: scaffolded workflow 0047
  (`ui-follow-up-cleanup`) with a Codex RFC/scope lane, four first-pass review
  lanes including ergonomics/design, Codex ledger and implementation lanes, and
  Claude final review. `workflow validate`, `workflow plan`, and `git diff
  --check` passed before commit. No runtime behavior changed in the scaffold.
- 2026-05-14T10:18Z checkpoint: workflow 0047 run
  `run_489eb28aa3e0453b916113addacd02e3` is running on branch
  `striatum/0047-ui-follow-up-cleanup`. The Codex RFC/scope lane drafted
  proposed RFC 0035, updated the RFC index, changelog, and workflow-local
  report, and published synthesis artifact
  `art_d4d245a9812944b2871a52adb789badc`. Operator reran repo-venv workflow
  validation successfully after the lane's global Striatum validation hit an
  unavailable daemon socket. Next action is to complete `rfc_scope` and launch
  the four first-pass review lanes in parallel.
- 2026-05-14T10:22Z checkpoint: workflow 0047 `rfc_scope` completed. Four
  first-pass review lanes are running in parallel: traceability
  (`sess_67b861e6f1ed459c865ea208b3dc39ce`), no-claims
  (`sess_8750edcc7c8044e1860550819ca3679b`), ergonomics/design
  (`sess_55481239cca440b1bdb67a8c64e2710d`), and ops/test
  (`sess_c8b5fd59b70a48eba5a4c21c946eb8e8`). Each prompt forbids Striatum
  mutation, commit/push, product implementation, and false attribution, and
  writes only its workflow-local review artifact.
- 2026-05-14T08:24:35Z checkpoint: workflows 0034 and 0035 first-pass review
  ledgers are complete and published. Workflow 0034 ledger artifact
  `art_b4dcf8d2ad3f4972a1b00b2b904a2c80` gates RFC 0023 implementation to an
  evidence-bound volume-mesh handoff slice; workflow 0035 ledger artifact
  `art_78b2248f646b4779bdd42ebe95eb303c` gates RFC 0024 implementation to a
  generated-body validation and structured-unavailable GZ handoff slice. Both
  workflow branches were committed, pushed, and fast-forwarded to `main`; trunk
  is current at `6a8d993`.
- 2026-05-14T08:24:35Z checkpoint: Striatum reports exactly two queued build
  jobs for the active backlog pair:
  `job_run_ef025ef630ec470e8d138821225783a2_implement_findings` and
  `job_run_cc879e1c30fa48d79fc1112669eb623c_implement_findings`. Final-review
  jobs are blocked behind those implementation jobs. Next action is to claim
  both Codex implementation lanes in parallel and require maximal useful
  sub-agent fanout within each lane.
- 2026-05-14T08:25:46Z checkpoint: both Codex implementation lanes were
  claimed and acknowledged. Workflow 0034 is running under Striatum session
  `sess_d3d234b140f4413c99fcd04d52c7357b`, lease
  `lease_1d861a16d3c5486288dc6c76e7cffd66`, local exec session `53660`.
  Workflow 0035 is running under Striatum session
  `sess_09f287c5596d475abba65afbf0826e4b`, lease
  `lease_bf0a58c35baa4cd18d360fa7a02f8445`, local exec session `87691`.
  Both prompts require maximal useful sub-agent fanout, forbid Striatum
  mutation/commit/push, forbid false bylines, and keep root `CHANGELOG.md`
  wording in patch summaries for operator application.
- 2026-05-14T08:47:31Z checkpoint: both implementation jobs completed and
  were published. Workflow 0035 implementation artifact
  `art_4a64e5d18e0d43a6b6f6590a6a7f1c27` adds the RFC 0024 structured
  unavailable/fixture-only GZ handoff and records `kayakgen/search/compare.py`
  hardening as deferred outside the packet write scope. Workflow 0034
  implementation artifact `art_8b5ac8bea9ea4b0f8f525fd1c7204022` adds the RFC
  0023 fixture-backed volume-mesh handoff, hash/path-bound dispatch gates, CLI
  blocker classes, and focused tests. Operator mechanical checks found no
  forbidden attribution metadata in changed files and clean `git diff --check`
  for both worktrees.
- 2026-05-14T08:47:31Z checkpoint: final reviews were claimed and launched in
  parallel. Workflow 0035 final review is running under Striatum session
  `sess_cd50d75bae894ae89a374df2dca1f638`, lease
  `lease_2a977cf4f629475d828865f9b34dcfc6`, local exec session `1610`.
  Workflow 0034 final review is running under Striatum session
  `sess_79f47bf1b31149b29522e8ad037dc400`, lease
  `lease_798233907a7e43159f269517c6786cfb`, local exec session `56948`.
- 2026-05-14T08:51:59Z checkpoint: workflow 0035 final review accepted the
  generated-body high-angle GZ handoff. Final review artifact
  `art_2bc46d81f5c84f0e8767658ded87663a` recorded no blocking findings;
  lingering low/medium items are a deferred compare negative test, legacy
  tuple validation cleanup, raw diagnostic exception text, and brittle
  fixture-only warning text. Operator `git diff --check` and forbidden
  attribution scans passed before commit.
- 2026-05-14T08:54:29Z checkpoint: workflow 0034 final review accepted the
  watertight volume-mesh handoff. Final review artifact
  `art_969aca7642fd4cfaadd2364f1fa6f578` recorded one low-severity
  follow-up for missing direct negative tests on several existing rejection
  codes, plus two low-risk contract/documentation observations. The accepted
  implementation commit was rebased onto current `main` after workflow 0035
  landed, preserving fast-forward trunk hygiene.
- 2026-05-14T08:58Z checkpoint: RFC 0023/RFC 0024 status drift was corrected
  in the RFC files, sequential RFC index, PRD, user guide, and changelog. The
  docs now describe workflow 0034/0035 as landed conservative handoff slices
  while keeping production solver readiness and real high-angle GZ claims
  deferred.
- 2026-05-14T09:03Z checkpoint: merged workflow branches 0034, 0035, and 0045
  were pruned locally and remotely after their changes landed on `main`.
  Workflow 0046 (`slider-label-visibility`) was scaffolded as a narrow
  follow-up for the user-reported hidden slider-label issue, with traceability,
  ergonomics/design, and ops/test first-pass review lanes and a Codex
  implementation lane that requires maximal useful sub-agent fanout.
- 2026-05-14T09:06Z checkpoint: workflow 0046 run
  `run_cec0311f06dd4484a8743c329f4dca61` was prepared, branch-confirmed on
  `striatum/0046-slider-label-visibility`, and started. Three first-pass
  review jobs were claimed, acknowledged, and launched concurrently:
  traceability (`sess_291f53a848b148bbb396ffe5eee44221`), ergonomics/design
  (`sess_88c321b49c8f413e8ffb19a62a6f4e9c`), and ops/test
  (`sess_6b85d7c949cd406c823a2c0111b8f191`).
- 2026-05-14T09:15Z checkpoint: workflow 0046 first-pass reviews were
  published. Traceability accepted the workflow as covered by existing UI RFCs
  (`art_2f2a661522de4d749ae564a8df82a99a`). Ergonomics/design accepted with
  focused findings around desktop label placement/font/value text and web
  slider thumb-label/typography behavior
  (`art_31b4ea64b1e54d4084cbd4c2f90b61d5`). Ops/test accepted with findings
  and validation guidance after a Codex sandbox-bypass retry
  (`art_5a7259782f6644688f255b6b2be5db58`).
- 2026-05-14T09:22:41Z checkpoint: workflow 0046 findings ledger was
  published as `art_502be1cdc477464893ebdc8f2e8e37a0` and completed. The
  ledger gates implementation to narrow desktop/web slider-label visibility
  fixes plus rendered/DOM geometry proof, with no new RFC required.
- 2026-05-14T09:22:41Z checkpoint: workflow 0046 Codex implementation lane was
  claimed and acknowledged under session
  `sess_8646f5f047fd4044ab43931ca400fdc8`, job
  `job_run_cec0311f06dd4484a8743c329f4dca61_implement_findings`, lease
  `lease_28502700cee142e48c100629fa609881`. The prompt requires maximal useful
  sub-agent fanout, forbids Striatum mutation/commit/push and forbidden byline
  metadata, and asks for a workflow-local patch summary.
- 2026-05-14T09:45:03Z checkpoint: workflow 0046 implementation completed and
  was published as `art_f2914d2dcfd94aecbab7dac7a570f848`. Codex reported
  focused desktop bbox, web static/theme, browser acceptance, and full-suite
  validation passing, with full-suite result `328 passed in 84.93s`. Operator
  checks found clean `git diff --check`, no forbidden attribution metadata, and
  no trailing whitespace in new workflow/test artifacts.
- 2026-05-14T09:50:29Z checkpoint: workflow 0046 final review completed with
  verdict `accept_with_findings`; artifact
  `art_7d18e35fb80c48ea8bd2b8061165c855`; verdict
  `verdict_c1f65bb287bd484f850f96d7b351e8b4`. Striatum reports run
  `run_cec0311f06dd4484a8743c329f4dca61` complete. Non-blocking findings:
  Matplotlib fallback keeps a tested manual bottom offset until
  `label_location` is available, web rows intentionally use a wrapper
  `role="group"` for canonical aria labels, and `PARAMETER_RAIL_CSS`
  duplicates the `:root` token block harmlessly.
- 2026-05-14T06:48:42Z checkpoint: workflow 0045 review remediation completed
  on branch `striatum/0045-workspace-ui-follow-up`; artifact
  `art_27fb1b0083f84d3a879c6e4c35f249b8` was published. The packet changes
  only clarified review verdict routing, added `CHANGELOG.md` to the
  implementation write scope, expanded sources, and documented the harness-safe
  validation command. Workflow validation and `git diff --check` passed; four
  first-pass review lanes are queued for parallel launch.
- 2026-05-14T06:52:05Z checkpoint: workflow 0045 first-pass reviews were
  claimed, acknowledged, and launched in parallel across traceability
  (`claude`), domain/no-claims (`gemini`), ergonomics/design (`claude`), and
  ops/test (`codex`). Each prompt preserves review-only scope, forbids
  Striatum mutation and falsified bylines, and requests maximal useful
  sub-agent or parallel-helper use.
- 2026-05-14T06:59:03Z checkpoint: workflow 0045 first-pass reviews were
  published with `accept_with_findings` verdicts: traceability
  `art_d260c5db42464b60b8764e544d2ab438`, domain/no-claims
  `art_242397acaf984873ab2e2c0de9ff2670`, ergonomics/design
  `art_fbe7c080d8f4499888b0117ff00d1654`, and ops/test
  `art_5c88ea0bcee540a1b54a521e8eed60a1`. The Gemini domain lane used a
  `gemini-2.5-flash` fallback after `gemini-3.1-pro-preview` quota exhaustion.
  No review requested a remediation cycle; Striatum now has one queued job for
  workflow 0045, the findings ledger.
- 2026-05-14T07:00:23Z checkpoint: workflow 0045 findings ledger was claimed,
  acknowledged, and launched under Codex session
  `sess_951648fa34e54963add9fbc04df14e47`. The prompt asks for maximal useful
  sub-agent extraction across the four review lanes and only the workflow-local
  `FINDINGS.md` artifact plus optional workflow-local report notes.
- 2026-05-14T07:08:15Z checkpoint: workflow 0045 findings ledger completed and
  published as `art_6a1511c0c59b4a7cab13f8a0951f31d2`. Gate verdict is
  `accept_with_findings`; no review remediation cycle is needed. The ledger
  defines the safe implementation scope as web preset binding, dynamic validity
  badge, Resistance and Mesh read-model wiring, honest Export menu rows,
  forbidden-copy expansion, browser/layout/read-model tests, and factual docs
  and changelog updates. Striatum now has one queued workflow 0045 job:
  `implement_findings`.
- 2026-05-14T07:09:37Z checkpoint: workflow 0045 implementation was claimed,
  acknowledged, and launched under Codex session
  `sess_990d8f1faba94666990e0d75cfb613c7`. The live run snapshot write scope
  excludes root `CHANGELOG.md`, so the implementer was instructed to propose
  exact changelog wording in `PATCH_SUMMARY.md` and leave root changelog edits
  to the operator after the job.
- 2026-05-13T20:56:04Z checkpoint: workflow 0044 scaffold was amended to add
  a dedicated ergonomics/design first-pass review lane before findings ledger
  and implementation. The workflow validates with the repo venv Striatum CLI.
- 2026-05-13T21:33:24Z checkpoint: starting workflow 0044 execution. The
  workflow plan exposes review_remediation first, then four parallel review
  lanes (traceability, domain, ergonomics/design, ops), then ledger,
  implementation, and final review. `run prepare` exposed an interrupted
  local Striatum SQLite v16 migration (`runs_new` temp table present with
  schema version 15); a backup was written to
  `.striatum/scratch/operator-db-repair-20260513T/state.sqlite3.before-v16-repair`
  before local state repair. No Striatum source changes are being made.
- 2026-05-13T21:49:27Z checkpoint: workflow 0044 run
  `run_4966ab190f8840d9b2f9c82b4044edad` is running on branch
  `striatum/0044-workspace-ui-rework`. The review_remediation job completed
  with artifact `art_3d85bc3387e6463fa1ac272cd9230323`, after a direct
  headless Codex retry bypassed the local bubblewrap failure. The remediation
  made RFC 0033 canonical for scope/copy/acceptance criteria and removed
  review-scaffold dependence on an unstored handoff bundle. Four first-pass
  review lanes are now queued for parallel launch.
- 2026-05-13T21:53:32Z checkpoint: workflow 0044 first-pass reviews were
  launched in parallel across traceability (`claude`), domain (`gemini`),
  ergonomics/design (`claude`), and ops (`codex`). The lane prompts preserve
  review-only boundaries, forbid Striatum mutation, and request maximal useful
  sub-agent/parallel assistance from each assigned reviewer.
- 2026-05-13T21:58:52Z checkpoint: workflow 0044 first-pass reviews are
  published. Verdicts: traceability `accept_with_findings`
  (`art_2b53fc2405ac4a8dac1a13e8a824d345`), domain `accept`
  (`art_784a311d19a842ec9020b17bfae648f8`), ergonomics/design
  `accept_with_findings` (`art_2c2743081cd84ffeb5e82ea58cf77da5`), and ops
  `accept_with_findings` (`art_91ef98eb947d4004896205f1e511fded`). Striatum
  queued the findings ledger for workflow 0044.
- 2026-05-13T22:00:29Z checkpoint: workflow 0044 findings ledger is claimed
  and running under Codex session `sess_1fae22524c5c4ca9a8cdff5ec37ee4b5`.
  The prompt asks for disjoint parallel/sub-agent ledger extraction and only
  the workflow-local `FINDINGS.md` artifact.
- 2026-05-13T22:05:24Z checkpoint: workflow 0044 findings ledger completed
  and published as `art_bc49d7fb6c40487d819e344324de6543`. The ledger gates
  implementation as `accept_with_findings`, with 12 safe-now implementation
  findings, 3 test/docs/scaffold findings, explicit deferrals, and a required
  validation matrix. Striatum queued workflow 0044 `implement_findings`.
- 2026-05-13T22:06:40Z checkpoint: workflow 0044 implementation is claimed
  and running under Codex session `sess_b58bda9e3d5e4169ba20d467387ad8ae`.
  The implementer prompt asks for maximal useful sub-agent fanout, disjoint
  scopes, in-scope docs/user-guide updates, tests, and a patch summary with a
  proposed root changelog entry because root `CHANGELOG.md` is outside the
  Striatum write scope.
- 2026-05-13T22:27:26Z checkpoint: workflow 0044 implementation completed.
  Patch summary published as `art_b53ca8a898094522a27385f865712abf`; Striatum
  job `job_run_4966ab190f8840d9b2f9c82b4044edad_implement_findings` is
  complete. Implementer validation: `git diff --check` passed,
  `.venv/bin/python -m pytest -q` -> 291 passed,
  `.venv/bin/python -m pytest tests/test_web.py tests/test_web_layout.py tests/test_ui_theme.py -q`
  -> 43 passed, and
  `.venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance -q`
  -> 1 passed. Next step is the Striatum final review lane before commit,
  trunk fast-forward, or backlog resumption.
- 2026-05-13T22:35:58Z checkpoint: workflow 0044 final review published as
  `art_7c61bfc9fa494d2f95e28bdae5a86acc`; verdict
  `accept_with_findings`. Striatum marks run
  `run_4966ab190f8840d9b2f9c82b4044edad` complete. Follow-up findings to
  carry into backlog/successor RFCs: web class presets do not reseed/narrow
  sliders, validity badge is static, resistance table/read model is not wired
  into the card, mesh diagnostics/package read models are not wired into the
  tab, toolbar export menu lacks Hydro JSON/Stability JSON/Mesh package items,
  forbidden-string grep tests should cover all RFC 0033 no-go strings, patch
  summary changelog wording is cosmetic-stale after the operator changelog
  entry, and full desktop region/test-id parity remains an explicit deferral.
- 2026-05-13T22:41:20Z checkpoint: after landing 0044, backlog inspection found
  only stale open predecessor runs 0040 and 0041. They are superseded by
  completed successor workflows 0042 and 0043 respectively; their queued
  downstream jobs should not be claimed. Operator disposition is to record the
  supersession, cancel the stale runs, and prune their obsolete branches.
- 2026-05-13T22:41:20Z checkpoint: recorded supersession decisions
  `dec_dc5ce467f37b48f295b73ed29477efa6` (0040 -> 0042) and
  `dec_8195ead3a4d741a493848da2be1086aa` (0041 -> 0043), resolved both
  checkpoints with cancel action, and canceled runs
  `run_48d834656e604d66aa430eb5f60ea643` and
  `run_4c920dd1311f42a5b0bbac4126af0cbd`. Striatum now reports no human
  checkpoints or open blockers.
- 2026-05-13T22:41:44Z checkpoint: deleted obsolete local and remote branches
  `striatum/0040-design-constraint-surfacing` and
  `striatum/0041-web-hosted-browser-acceptance`. `striatum doctor --json`
  reports no problems, `git ls-remote --heads origin 'refs/heads/striatum/*'`
  returns zero striatum branches, and explicit queued-job checks for the two
  canceled runs return zero queued items. The aggregate `status --json`
  `claimable_jobs` field still shows stale claimable summaries for the canceled
  runs, but `list jobs --state queued` and the jobs summary show only completed
  or canceled work.
- 2026-05-14 checkpoint: repaired the repo venv Striatum install without
  editing the dirty `/home/halbritt/git/striatum` source tree. Reinstalled the
  existing source into `.venv`, yielding `striatum 1.47.0`; refreshed
  `claude_code` and `codex` skill bundles plus the Codex plugin bundle; and
  confirmed `striatum doctor --json` is clean.
- 2026-05-14 checkpoint: corrected RFC 0033 from `proposed` to
  `partial landed safe-slice`, added RFC 0034 as the accepted implementation
  target for workflow 0044 follow-up findings, and scaffolded validated
  workflow `0045-workspace-ui-follow-up` with traceability, domain/no-claims,
  ergonomics/design, ops/test, ledger, Codex implementation, and final-review
  lanes.
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
- 2026-05-13T19:29:24Z checkpoint: successor runs 0042 and 0043 are active on
  current `main` to resolve the blocked 0040 and 0041 findings. Six review
  jobs were registered, claimed, and acknowledged in parallel: 0042
  traceability/domain/ops and 0043 traceability/browser/ops. The launch prompts
  preserve lane ownership, require maximal useful sub-agent use, forbid Striatum
  mutation commands, and require exactly one `Verdict intent:` line before the
  operator will publish a review.
- 2026-05-13T19:40:55Z checkpoint: all six successor first-pass reviews were
  published. Gemini Pro 3.1 quota was exhausted for the two Gemini lanes, so
  they were retried within the Gemini lane before publication rather than
  switching vendors. Published artifacts: 0042
  `art_2c4df4a9d92b45fab5c0fca3761dc54b` (traceability),
  `art_2e46e0743dbc4f559dd8f31356880188` (domain), and
  `art_e4ec60b3655e4e27a150e3dfdfaaccec` (ops); 0043
  `art_3634834d5d4b4df09ec6ae67acff6f03` (traceability),
  `art_6534da9ce1be4854920ee2073361c160` (browser), and
  `art_aa0b01556a34496bb4a010c9961f36c1` (ops). Both successor runs now have
  `findings_ledger` queued.
- 2026-05-13T19:47:20Z checkpoint: both successor findings ledgers were
  published and completed. 0042 ledger `art_bb02949c3574467ab24cbdc35ee264f4`
  defines the safe RFC 0031 implementation slice; 0043 ledger
  `art_0a3aa38ff90840a49db6c3eb48bcdd43` defines the safe RFC 0032
  implementation slice. Both successor runs now have `implement_findings`
  queued.
- 2026-05-13T19:48:45Z checkpoint: both successor implementation jobs were
  registered, claimed, and acknowledged. They are being launched in separate
  branch worktrees to preserve parallelism while avoiding shared-worktree
  conflicts: `/tmp/kayak-gen-successor-worktrees/0042` and
  `/tmp/kayak-gen-successor-worktrees/0043`.
- 2026-05-13T20:11:43Z checkpoint: both successor implementation jobs landed
  on `main`. 0042 landed as `78f14d0` with patch-summary artifact
  `art_f1d914a34a6d4f0e86e5499f8dc553a5`; 0043 rebased cleanly over 0042 and
  landed as `2798591` with patch-summary artifact
  `art_78d4e0a284c440558b439edfeaaed57c`. 0042 reported `.venv/bin/python -m
  pytest` -> 263 passed; 0043 reported `pytest -q` -> 252 passed plus
  browser-acceptance and focused web/CFD suites. Final-review jobs for 0042 and
  0043 are now running in parallel on the Claude lane.
- 2026-05-13T20:14:22Z checkpoint: integrated `main` verification passed:
  `.venv/bin/python -m pytest -q` -> 264 passed, and `.venv/bin/python -m
  pytest tests/test_web_browser.py -m browser_acceptance --browser-acceptance
  -q` -> 1 passed. 0042 final review published as
  `art_a699f8a3625047b084808222ad01a4ed` with `accept_with_findings`; the
  residual finding is the expected changelog gap because workflow build scopes
  excluded root `CHANGELOG.md`. 0042 run is complete. 0043 final review is
  still running.
- 2026-05-13T20:17:05Z checkpoint: 0043 final review published as
  `art_ec2468a675bb4d179510e2f7d229dea2` with `accept`; 0043 run is complete.
  The final review also noted a non-blocking root `CHANGELOG.md` gap.
- 2026-05-13T20:18:12Z checkpoint: root `CHANGELOG.md` was updated as
  operator release hygiene using the two implementation patch summaries, closing
  the non-blocking changelog gap noted by both final reviews.
- 2026-05-13T20:19:30Z checkpoint: temporary successor worktrees were removed
  and merged 0042/0043 local and remote branches were deleted. Older 0040/0041
  branches were preserved because their remote tips are not ancestors of
  `main`.
- 2026-05-13T17:46:07Z checkpoint: the four unblocked ledger jobs completed
  and were published without `author:` bylines: 0033
  `art_b263fcf6154e4503b62f8ad2a142813a`, 0037
  `art_d7b74a57a6984e678e34511eab735118`, 0038
  `art_cc417ec1fc31408b978f6053f4a16e23`, and 0039
  `art_4d5f25501f044275858079e7803403e0`. Ledger branch commits were pushed:
  0033 `d5b43bd`, 0037 `7b94cbd`, 0038 `461a286`, and 0039 `6d487c8`.
- 2026-05-13T17:47:42Z checkpoint: the 0033, 0037, 0038, and 0039 workflow
  branches were rebased onto current `main` and implementation jobs were
  claimed, acknowledged, and launched as four parallel Codex GPT-5.5 agents in
  isolated worktrees. Sessions: 0033
  `sess_a64d5c82bc03491dbfa20e56ba24d540`, 0037
  `sess_c8f2b3b0775d412795bf6a55927b8b8b`, 0038
  `sess_d7ea156f2f0941c8ac889fe6e1a8deeb`, and 0039
  `sess_d1dc968d00b64cf79f733be46fa53ac9`.
- 2026-05-13T17:54:48Z checkpoint: all four implementation agents remain
  active. Branch-local edits have started: 0033 is in workflow metadata and
  closed-volume evaluation; 0037 is in CFD fixture adapter/CLI/tests/changelog;
  0038 is in calibration/claims/contract/tests/RFC traceability; 0039 is in
  hull geometry, mesh diagnostics/package, desktop UI parameter plumbing, and a
  generated closed-body helper. No implementation artifacts have been published
  yet.
- 2026-05-13T18:03:34Z checkpoint: 0037 and 0038 implementation agents
  finished. Their patch summaries were published as
  `art_bb2eb3dd0b134244b3059be2d49b329b` and
  `art_1c9954c1883945198156a5b318635865`, implementation jobs were completed,
  and branch commits were pushed as 0037 `0b3cb9c` and 0038 `8bdd535`.
  Final-review jobs for 0037 and 0038 are now running in parallel Claude Opus
  lanes. 0033 and 0039 implementation agents remain active.
- 2026-05-13T18:07:33Z checkpoint: 0033 implementation finished. Its patch
  summary was published as `art_9e936226c92a49448bf22b0078cfe719`, the
  implementation job was completed, and branch commit `6903857` was pushed
  after rebasing onto current `main`. The 0033 final-review job is now running
  in a Claude Opus lane. 0039 remains the only active implementation job.
- 2026-05-13T18:14:59Z checkpoint: root prompt
  `CLAUDE_DESIGN_UI_REWORK_PROMPT.md` was added and pushed on `main` as
  `212d250` for a future Claude Design UI handoff. 0039 implementation
  finished; its patch summary was published as
  `art_fc269f6e6d67403ea97b9008b67b1d1a`, the implementation job completed,
  and branch commit `8367b65` was pushed after rebasing onto current `main`.
  The 0039 final-review job is now running. Striatum 1.37.0 no longer honors
  bare `STRIATUM_DAEMON_REQUIRED=0`; SQLite fallback now requires the paired
  `STRIATUM_TEST_HARNESS=1` compatibility env for this unmigrated repo state.
- 2026-05-13T18:21:53Z checkpoint: 0037 and 0038 final reviews were accepted
  and their workflow branches were fast-forwarded into `main`. `main` is pushed
  at `8461d73`. The 0037 final verdict was `accept`; the 0038 final verdict was
  `accept_with_findings`. The initial 0033 final-review output was a status
  message rather than an artifact, so 0033 final review is being retried with a
  stricter artifact-only prompt. 0039 final review is still running.
- 2026-05-13T18:27:41Z checkpoint: 0039 final review was accepted with findings
  and the workflow branch was fast-forwarded into `main`; `main` is pushed at
  `9a56257`. 0033 final review retry was accepted and published, but rebasing
  the 0033 branch onto current `main` hit conflicts in `CHANGELOG.md` and
  `tests/test_generated_closed_body.py` after 0039 landed overlapping generated
  closed-body tests. A separate Codex integration agent is resolving the rebase
  conflict in `/tmp/kayak-gen-ledger-worktrees/0033`; the operator is not
  resolving implementation content directly.
- 2026-05-13T18:38:13Z checkpoint: the separate Codex integration agent
  resolved the 0033 rebase conflict, preserved 0039 generated-body behavior and
  0033 generated closed-volume behavior, and reported `pytest -q` as 226 passed
  and 2 skipped. The rebased 0033 branch was fast-forwarded into `main`; `main`
  is pushed at `378798c`. Unblocked workflows 0033, 0037, 0038, and 0039 are
  landed. Remaining active Striatum blockers are the 0040 domain review and
  0041 browser review human checkpoints.
- 2026-05-13T18:40:01Z checkpoint: completed workflow branches 0033, 0037,
  0038, and 0039 were pruned locally and remotely after landing. Current `main`
  is pushed at `950b4a1`. Verification on trunk: `git diff --check` passed,
  `striatum doctor` reported 0 problems using the SQLite compatibility env, and
  `.venv/bin/python -m pytest -q` passed with 251 tests.
- 2026-05-13T18:52:48Z checkpoint: owner instruction received to create
  successor workflows for the 0040 and 0041 human-checkpoint blockers and
  proceed without further intervention. Two isolated scaffold worktrees were
  created from current `main`: `/tmp/kayak-gen-successor-worktrees/0042` on
  `striatum/0042-design-constraint-surfacing-revision` and
  `/tmp/kayak-gen-successor-worktrees/0043` on
  `striatum/0043-web-hosted-browser-acceptance-revision`. External agents will
  draft RFC 0031/workflow 0042 and RFC 0032/workflow 0043; the operator will
  not perform the design/scaffold content directly.
- 2026-05-13T19:10:22Z checkpoint: external scaffold agents completed RFC
  0031/workflow 0042 and RFC 0032/workflow 0043. Both workflows validated and
  include first-pass review revision cycles to avoid the 0040/0041 blocker
  shape. 0042 landed on `main` as `8cdc4a0`; 0043 required an external
  integration agent for the RFC index conflict and then landed on `main` as
  `bc7da82`. Both successor workflows are ready to prepare/start.
- 2026-05-13T19:18:33Z checkpoint: successor scaffolds and this report were
  pushed to `main` as `94ec9f0`. The old scaffold branches were detached from
  their temporary worktrees, reset to current `main`, and pushed as active run
  branches. Striatum successor runs are started: 0042
  `run_de90d1b197c640fd93ace51cfa37471b` on
  `striatum/0042-design-constraint-surfacing-revision`, and 0043
  `run_355c9ef7756449ce869550a3323e51c8` on
  `striatum/0043-web-hosted-browser-acceptance-revision`. The next claimable
  jobs are the two Codex revision-anchor/remediation roots, which can run in
  parallel because their write scopes are separate.
- 2026-05-13T19:26:24Z checkpoint: the first Codex root-agent launch hit a
  nested sandbox `bwrap` failure and produced no publishable files. The same
  acknowledged jobs were relaunched with Codex shell sandboxing disabled while
  preserving Striatum write scopes. 0042 published
  `art_d700c5ca05b14f29964d1e8cdcb2dac1` and completed
  `review_remediation`; the external remediator fixed RFC 0031/index status,
  0042 workflow `OPERATOR_REPORT.md` forbid ambiguity, and changelog wording.
  0043 published `art_0e6bf8daa4c54aa684082c7fa844a391` and completed
  `review_revision_anchor`, carrying forward the 0041 browser blocker context
  into the review handoff. Both artifacts have no `author:` byline, `git diff
  --check` is clean, and both successor workflow files validate.
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

## Workflow 0045 Implementation Checkpoint

- 2026-05-14T07:33:13Z: implementation lane
  `job_run_e185c1837e3c4000acd92b0339374577_implement_findings` exited
  successfully. Codex wrote
  `striatum/0045-workspace-ui-follow-up/implementation/PATCH_SUMMARY.md` and
  reported `git diff --check`, `58 passed` focused web/layout/read-model/mesh
  tests, `1 passed` browser acceptance, and `299 passed` full suite.
- Operator scope check found changed paths under docs, web UI, tests,
  workflow-local implementation artifact, root changelog, and this operator
  report. Touched-file byline scan was clean; broader byline hits were
  pre-existing workflow prompt/reference docs outside this change.
- Published patch-summary artifact
  `art_5d1cf66d36ea4a47898d8b9ac1ed9f7c` and completed the implementation
  job in Striatum.
- Implementation commit `1e2d6e5` was pushed on
  `striatum/0045-workspace-ui-follow-up` and fast-forwarded to `main`.
- 2026-05-14T07:41:53Z: final review completed with verdict
  `accept_with_findings`; artifact
  `art_9780e6e309074501b4bab99f563bbbb8`; run
  `run_e185c1837e3c4000acd92b0339374577` is complete in Striatum.
- Non-blocking final-review findings recorded for successor work:
  selected-preset-only validity badge semantics, a likely dead
  `_state_matches_preset_seed` listener branch, global bounds for
  non-canonical sliders under active presets, duplicated export-menu row data,
  and ad-hoc web `_state_snapshot` keys. No remediation was required for
  workflow 0045.
- RFC 0034 and the RFC index were corrected from accepted-target language to
  landed safe-slice after the final review/run completion.
- 2026-05-14T07:45Z: remaining real backlog identified in the deferred queue:
  workflows 0034 and 0035 were held until workflow 0033 landed, and 0033 is
  now complete. Stale aggregate Striatum claimable counts come from canceled
  workflows 0040/0041 and are not real work. Review/ledger/final prompts for
  workflows 0034 and 0035 were amended to request maximal useful sub-agent or
  parallel-helper use, keep helpers read-only, and forbid byline metadata.
- 2026-05-14T07:47Z: prepared and started workflow 0034
  (`run_ef025ef630ec470e8d138821225783a2`) on
  `striatum/0034-watertight-volume-mesh-handoff` and workflow 0035
  (`run_cc879e1c30fa48d79fc1112669eb623c`) on
  `striatum/0035-high-angle-gz-generated-body-handoff`.
- 2026-05-14T07:56Z: all six first-pass review lanes for 0034 and 0035 were
  launched in parallel. The Gemini Pro lanes exhausted quota; fallback attempts
  on `gemini-2.5-flash` also exhausted quota. Claude/Codex traceability and
  ops artifacts were produced, but several reviewers used `needs_revision`
  solely because the queued RFC slice was not yet implemented. Operator
  disposition: treat that as a scaffold/prompt defect, clarify review verdict
  semantics, and ask the assigned reviewers to revise under the clarified
  pre-implementation contract rather than editing their findings manually.
- 2026-05-14T08:02Z: RFC status headers were aligned with the RFC index for
  the landed/partial slices that had drifted, including RFC 0021's landed
  synthetic-diagnostic status. Workflow 0034/0035 first-pass review prompts now
  say to use `accept_with_findings` for implementable gaps and reserve
  `needs_revision` for RFC/workflow scaffold contradictions, missing context,
  or impossible/unsafe scope.
- Next operator actions: commit/push/fast-forward `main`, rebase/update the
  0034 and 0035 worktrees with the scaffold clarification, rerun affected
  review artifacts, publish valid first-pass reviews, then continue to the
  ledgers and implementation lanes with maximum parallelism.

## Workflow 0047 UI Follow-Up Cleanup

- 2026-05-14T09:20Z: scaffolded workflow 0047 from workflow 0045 and 0046
  final-review findings, drafted proposed RFC 0035, corrected RFC status/index
  drift, and pushed the scaffold to `main` as commit `5289866`.
- 2026-05-14T09:31Z: first-pass reviews were completed and published:
  traceability `accept_with_findings`, no-claims `accept` using Gemini Flash
  after Gemini Pro quota exhaustion, ergonomics/design `accept_with_findings`,
  and ops/test `accept_with_findings`.
- 2026-05-14T10:29Z: Codex findings ledger published
  (`art_969b235b3f90429c8bffc0398df00a61`) and completed with
  `accept_with_findings`. The ledger deduplicates the review set to six
  safe-now UI cleanup findings and keeps backend/solver/calibration/stability/
  watertight-readiness/desktop-parity work deferred.
- 2026-05-14T11:12Z: Codex implementation lane completed the six
  ledger-approved cleanup findings. Patch summary artifact
  `art_d52d985faa104cc2919fac590fca90f5` was published and the
  implementation job was completed in Striatum.
- Implementation validation reported: `git diff --check` passed; focused
  web/static/theme tests `39 passed`; browser acceptance `1 passed`;
  desktop bbox/gui tests `4 passed`; full non-browser suite `333 passed`.
- 2026-05-14T11:17Z: Claude final review published artifact
  `art_9c3ef4165cb64c0a98b6b8452f565823` and completed with
  `accept_with_findings`; Striatum marks run
  `run_489eb28aa3e0453b916113addacd02e3` completed.
- Non-blocking successor findings recorded by final review: stronger Trame
  browser proof or removal for the retained preset seed-listener branch,
  export-row `subtitle`/`description` schema consolidation, optional
  `Mesh package...` ellipsis polish, and future snapshot-schema unification.
- 2026-05-14T11:20Z: landed workflow 0047 to `main` as commit `78b14e5`,
  pushed `main`, and deleted merged branch
  `striatum/0047-ui-follow-up-cleanup` locally and remotely.
- 2026-05-14T11:23Z: corrected RFC 0035 and the RFC index from `proposed`
  to `landed safe-slice` after the completed workflow was fast-forwarded.

## Workflow 0048 Successor RFC Backlog

- 2026-05-14T11:38Z: started operator scaffolding for successor RFC workflow
  0048. Scope requested: RFCs for workflow 0047 successor findings plus the
  named deferred backlog items around closed-volume/solver readiness, real CFD
  adapter work, resistance calibration fixtures, and high-angle `GZ`.
- 2026-05-14T11:39Z: completed the three parallel Codex RFC-scoping lanes for
  workflow 0048. Draft RFCs now exist for 0036-0043; no runtime code was
  changed. Review lanes are claimable next: traceability, no-claims,
  ergonomics/design, and ops/test.
- 2026-05-14T11:55Z: ops review completed with `accept_with_findings`.
  No-claims completed with `accept`, but the direct Gemini Flash fallback
  artifact carried an operator byline; traceability and ergonomics/design
  Claude supervisors also died and reverted byline lookup to operator. Operator
  disposition: do not submit stale/misattributed artifacts; recover by
  requeueing those review lanes and rerunning with truthful bylines before
  integration.
- 2026-05-14T11:57Z: corrected the repo copy of the no-claims review author
  line to `reviewer-no-claims-gemini-2.5-flash-001`; Striatum had already
  accepted the stale artifact and cannot retry a completed job, so the mismatch
  remains recorded here for auditability.
- 2026-05-14T12:05Z: recovered and submitted Claude traceability and
  ergonomics/design reviews with truthful Claude bylines. Both completed with
  `accept_with_findings`; the RFC integration job is now queued.
- 2026-05-14T12:18Z: integration completed and published
  `striatum/0048-successor-rfc-backlog/integration/PATCH_SUMMARY.md`.
  Claude final review completed with `accept`; Striatum marks
  `run_c1de081e76f14cd1a81194e306338ac2` completed. Workflow 0048 is ready
  to commit and fast-forward to `main`.

## Workflow 0050 Decision Panel Research

- 2026-05-14T14:48Z: scaffold was already landed to `main` as commit
  `248b8f4`. The active run
  `run_dc0a506896094745b380fd3ad2535d59` has completed all eight research
  packets and all 24 panel votes. Eight adapter-output blockers from direct
  Claude/Gemini fallbacks were recovered by publishing the existing vote files
  with truthful model bylines and override rationale. No design decisions have
  been integrated yet; `integrate_decisions` is now claimable.
- 2026-05-14T15:09Z: Codex decision integration completed; Claude final review
  accepted the workflow. Striatum marks
  `run_dc0a506896094745b380fd3ad2535d59` completed with no open blockers and
  no non-accepting review verdicts. The accepted decisions are recorded in
  `docs/DECISION_LOG.md`, `docs/ROADMAP.md`, `CHANGELOG.md`, and
  `striatum/0050-decision-panel-research/integration/DECISION_RESULTS.md`.
  Next operator action after landing this commit: scaffold/run the unblocked
  implementation burn-down from the integration queue.
