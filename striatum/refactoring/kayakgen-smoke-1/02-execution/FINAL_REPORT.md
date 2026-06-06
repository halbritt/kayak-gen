---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
inputs:
  - "striatum/refactoring/kayakgen-smoke-1/00-goal/GOAL_DECISION.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/COMMITTED_PLAN.md"
  - "striatum/refactoring/kayakgen-smoke-1/01-plan/GATE_SUMMARY.md"
  - "striatum/refactoring/kayakgen-smoke-1/02-execution/STEP_LEDGER.md"
  - "striatum/refactoring/kayakgen-smoke-1/02-execution/PRESERVATION_REVIEW.md"
---

author: operator-self-declared-finalize-report-author

# Final Report — kayakgen-smoke-1: split `kayakgen/ui/web/app.py` along the Generate-panel seam

Date: 2026-06-06
Run: `run_f2fbd2ab9adefda44b5e72b6bfefafdf`, stage 2 (finalize_report)
Branch: `striatum/refactoring-campaign-kayakgen-smoke-1` (head `0448b78` at
report time). Integration to `main` is the operator's serialized step; this
report does not push or merge.

A maintainer who reads only this artifact should be able to review the
change confidently. Each section names the evidence it rests on.

## 1. Goal and provenance

- **Stage 0 (goal selection):** Goal B accepted —
  *decompose `kayakgen/ui/web/app.py` (2,550 lines) into focused sibling
  modules along the Generate-panel seam*, decision
  `dec_e526052a732d40b385a892b3e78680be`
  (`00-goal/GOAL_DECISION.md`, run `run_08d0beb1f0959b071475ff4400dc1d97`,
  owner: human, outcome: accepted).
- **Stage 1 (falsified plan gate):** verdict **`accept_with_findings`** over
  seven binding constraints C1–C7, all discharged in the committed plan;
  refusal branch checked and not taken; no revision cycle needed
  (`01-plan/GATE_SUMMARY.md`, run `run_28c3e3f04b2faa6dbe285358c5ea530e`).
  The stage-2 input contract is `01-plan/COMMITTED_PLAN.md`.
- **Binding constraints discharged (gate → execution):**
  - **C1** — `render_fork_button` monkeypatch patch-target redirect, landed
    in the S4 commit (`tests/test_generative_jobs_web.py` now patches
    `kayakgen.ui.web.layout`; fake and assertions unchanged).
  - **C2** — declared test-migration recipes: split reads (S1t/S4t), union
    expansion of the forbidden-claim scan (S1t/S4t/S5t), and the eight
    negative source assertions widened to `app.py ∪ layout.py` at S4t.
  - **C3** — rollback restated LIFO-only; honored (see §8).
  - **C4** — operator re-scoped `execute_slices.allowed_paths` to the exact
    files-touched envelope before dispatch (verified in the step ledger
    against `workflow.json`).
  - **C5** — strict-mode browser acceptance (`KAYAKGEN_BROWSER_ACCEPTANCE=1`)
    run as a mandatory gate after S4 and S5; green both times.
  - **C6** — `generate_panel.py` is trame-bearing by design (module-level
    `generate_spec_form` imports); extras-less safety rests on the
    `cli/main.py:648` try/except gate, re-verified extras-less.
  - **C7** — ledger-anchored execution discipline: one ledger entry per
    slice with commit hash and verification transcript
    (`02-execution/STEP_LEDGER.md`).
- **Stage 2 preservation review:** verdict **`accept_with_findings`**
  (`02-execution/PRESERVATION_REVIEW.md`, attempt 3): "the replayed test
  evidence matches the committed plan's preservation bars … No slice needs
  rework for preservation." Two non-blocking findings, incorporated here
  (§6, §7).

## 2. Baseline (recorded, then reproduced twice)

Recorded at plan time (§1.2 of the committed plan), reproduced by the
executor on the unmodified starting tree `a31773e` before any write, and
independently reproduced by the preservation reviewer:

| Command | Result |
|---|---|
| `.venv/bin/python -m pytest -q` | RED: **1 failed, 1307 passed, 4 skipped** |
| `.venv/bin/python -m ruff check kayakgen tests` | PASS, exit 0 |
| Strict browser acceptance | GREEN: 4 passed, 2 deselected |
| Extras-less import check | PASS |
| Extras-less full suite (§1.3 method) | 20 failed, 1114 passed, 24 skipped, 4 errors — all pre-existing, named |

**Named pre-existing failure (the "F3 singleton"):**
`tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`
— `kayakgen/services/evaluation.py` imports from `kayakgen.ui`. Red on
unmodified `main`; the per-slice bar was "failure set stays exactly this
one id", and it did, in every gate run.

**Named pre-existing extras-less set (the "F4 set"):** 2 collection errors
(`test_generate_spec_form.py`, `test_hull_parameter_metadata.py`), 2 runtime
errors (the two `test_cli_serve.py` manager tests), 20 failures (4 in
`test_generative_jobs_fork.py`, 15 in `test_generative_jobs_web.py`, plus
the F3 singleton). The bar was "set must not grow", and it did not.

## 3. Frozen surfaces — inventory and evidence

`git log --name-only a31773e..170b01f` (the code slice stack) touches **no**
frozen file. The preservation reviewer independently confirmed: "frozen
witness files stayed untouched across the code slice stack."

| Surface | Evidence |
|---|---|
| `tests/test_web_browser.py` (browser witness) | untouched; strict gate green at S4, S5, and review replay |
| `tests/test_import_boundaries.py`, `tests/test_services_boundaries.py` | untouched; F3 failure set unchanged |
| `pyproject.toml` | untouched (also a forbidden path in the job's write scope) |
| `kayakgen serve` CLI behavior | `tests/test_cli_serve.py` green every slice; S0 strengthened the jobs-root pin |
| `create_app` / `KayakgenApp` import paths + signatures | reviewer-verified identical signatures; 12 import sites unchanged |
| Generative-job state-transition order | `tests/test_generative_jobs_web.py` green every slice (runtime pins untouched; only the declared C1 redirect landed) |
| `LAYOUT_TEST_IDS` / `REGION_CLASSES` values, DOM ids, widget order | `tests/test_web_layout.py` + strict browser gate |
| `[web]` extras gating | per-slice extras-less import check + post-S5 extras-less full suite, F4 set identical |
| Claim-vocabulary guard | C2(ii) union expansion: the forbidden-claim test now scans every render-feeding module (app, presentation, layout, handlers, generate_panel, controllers, spec form, frontier hook) |

## 4. Step ledger summary

Full per-slice transcripts: `02-execution/STEP_LEDGER.md`. History shape
(per the reviewer's finding 1): **six code slice commits plus interleaved
ledger bookkeeping commits** that touch only the ledger file.

| Slice | Change | Preservation claim | Verification | Commit |
|---|---|---|---|---|
| S0 | `tests/test_cli_serve.py`: assert echoed `jobs_root` equals `KAYAKGEN_GENERATIVE_JOBS_ROOT` in both manager tests (+5 lines, cap 10) | characterization only; no source change | targeted 3 passed; full suite F3-only; ruff 0 | `24be568` |
| S1+S1t | constants/CSS/copy + 5 pure helpers → `presentation.py` (byte-identical); 46 by-name re-exports in `app.py`; declared pointer redirects + C2(i) step 1 + C2(ii) adds presentation.py (net ≈70/cap 80; tests ≈16/cap 20) | byte-identical values/bodies; every name still importable from `kayakgen.ui.web.app` (46-name identity check) | targeted 81 passed; full suite F3-only; ruff 0; import check OK | `cf3c8bc` |
| S2 | `_build_polydata`, `_make_actor`, `_rebuild_scene` → `scene.py` (`SceneMixin`) (net ≈26/cap 40) | byte-identical actor/mesh construction | full suite F3-only; ruff 0; import check OK | `47804a7` |
| S3 | panel region + `_default_generative_jobs_root_for_app` → `generate_panel.py` (`GeneratePanelMixin`); `cli/main.py:657` redirect (1 line); alias kept (net ≈56/cap 60) | payloads + transition order unchanged; jobs-root value-pinned by S0 | targeted 18 passed; full suite F3-only; ruff 0; import check OK; browser insurance 4/2 | `c1414c6` |
| S4+S4t | layout region → `layout.py` (`LayoutMixin`); C1 patch-target redirect; bulk redirects; C2(i) step 2; C2(iii) union negatives; C2(ii) adds layout.py (net ≈51/cap 80; tests 40/cap 40) | `LAYOUT_TEST_IDS`/`REGION_CLASSES` values, DOM ids, widget order unchanged | targeted 65 passed; full suite F3-only; ruff 0; import check OK; **strict browser gate 4/2** | `f9b2ad0` |
| S5+S5t | handlers region → `handlers.py` (`HandlersMixin`); app.py settles at **355 lines**; C2(ii) adds handlers.py + generate_panel.py (net ≈71/cap 100; tests 11/cap 20) | `create_app`/`KayakgenApp` paths + signatures unchanged; bindings identical | targeted 93 passed; full suite F3-only; ruff 0; import check OK; **strict browser gate 4/2**; **extras-less full suite: F4 set identical** | `170b01f` |

Final composition: `class KayakgenApp(HandlersMixin, GeneratePanelMixin,
LayoutMixin, SceneMixin)` — methods disjoint, MRO inert, exactly the plan §6
shape. `app.py` is a 355-line integrator (imports/re-exports, `__init__` +
parameter-rail state, mixin composition, `create_app`) — under the goal's
~600 cap and the plan's ≈400–450 projection.

## 5. Characterization tests added (preserving current behavior)

- **S0 (`24be568`):** two assertions in `tests/test_cli_serve.py` pinning
  the echoed `jobs_root` to the `KAYAKGEN_GENERATIVE_JOBS_ROOT` value in
  both manager paths. This documents the resolver's current behavior (env
  override, then home fallback); it does not change it. All other test
  edits in the campaign are declared string-preserving pointer
  redirects/read restructurings, not new characterization.

## 6. Deviations from plan (no stop condition fired)

No stop condition (plan §9) fired; no slice exceeded its net-diff cap. The
deviations below are recorded for honesty; none changed behavior:

1. **Slice-attribution corrections in the declared test-edit inventory.**
   The plan's S5t row expected the `"Shareable URL copied"` redirect at S5;
   the literal's definition (`SHARE_TOAST_COPY`) is displaced at **S1**, so
   the redirect landed in the S1 commit per the F2 same-commit rule.
   `test_hydro_tab_descriptions.py` was listed in S1t's files but nothing
   it asserts is displaced before S4; its edits landed at S4t. Several
   S1-displaced strings in `test_web_layout.py` (resistance-table markup,
   export row classes, the `"region-params"` ordering anchor) were not
   itemized line-by-line at the gate; each received the plan's declared
   default edit (mechanical pointer redirect / structural read edit,
   assertion strings unchanged), recorded per-slice in the ledger.
2. **Union-read implementation of C2(i)/C2(iii) at S4t.** Positives whose
   targets moved and the eight declared negatives are evaluated against
   app+layout concatenated reads — for negatives this is literally the
   discharged `app.py ∪ layout.py` scope; for positives it is the pre-split
   single-file semantics. Chosen over per-assertion repoints to stay inside
   the S4t net cap.
3. **Ledger bookkeeping commits interleave the slice stack** (reviewer
   finding 1, non-blocking): each slice is one code commit; its ledger
   entry follows as a separate commit so the entry can record the code
   commit's hash. Ledger commits touch only `STEP_LEDGER.md`.
4. **Harness repair between review attempts (reviewer finding 2,
   non-blocking):** `striatum worktree create` produced a detached-HEAD
   worktree, so the slice stack initially never advanced the run branch and
   the first two review attempts audited the unmodified baseline
   (spurious `needs_revision`). Repair: ancestry-verified fast-forward of
   `striatum/refactoring-campaign-kayakgen-smoke-1` to the existing stack,
   then checking the branch out at repo_root. The reviewer verified "no
   evidence that the code slice commits were replayed or rewritten."
   This was striatum-harness recovery, not a change to the campaign's code.

## 7. Deferred findings (noticed, correctly left alone; suitable as issues)

1. **Services→UI boundary violation (the F3 singleton):**
   `kayakgen/services/evaluation.py` imports `HYDROSTATICS_ROW_METADATA`
   from `kayakgen.ui.hydrostatics_metadata`, failing
   `test_services_does_not_import_ui_or_cli[path2]`. Pre-existing,
   deterministic, outside this campaign's blast radius. File as: move the
   metadata registry out of `ui` (or invert the dependency).
2. **Extras-less test-file leaks (the F4 set):** several web test files
   exercise web code without an `importorskip` guard, producing 20F+4E
   without `[web]` extras (named set in §2). File as: add guards or mark
   the files web-only.
3. **Invalid `# noqa` directives** at
   `kayakgen/ui/web/generate_frontier_view.py:60–65` (ruff warns
   "expected a comma-separated list of codes"). Pre-existing; cosmetic.
4. **Vacuous ordering anchor (pre-existing test weakness):**
   `test_validity_badge_visible_in_parameter_rail`'s `"region-params"`
   anchor matched the `LAYOUT_TEST_IDS` constant definition, not the
   layout's region open, so its params-before-badge claim was always
   trivially true. The campaign preserved the original semantics via a
   concatenated read; a follow-up could re-anchor it on
   `self._region_attrs("params")` to make the ordering claim real.
5. **Striatum harness findings** (kayak-gen is the striatum test workload;
   these belong upstream): per-job worktrees are detached-HEAD so
   `repo_write` author commits don't advance the run branch reviewers
   audit; `branch confirm` is records-only while reviewer lanes audit the
   live repo_root checkout; re-registered sessions mutate
   `expected_artifacts[].author_line` to an operator byline; idle
   unattested sessions are swept closed between packets. All recorded with
   recovery recipes in the step ledger (attempt-2 section).

## 8. Rollback map (LIFO-only, per C3)

A clean single `git revert` exists only at the head of the landed stack. A
full unwind reverts in this order, resolving `app.py`'s import block at
each step:

| Order | Revert commit | Undoes |
|---|---|---|
| 1 | `170b01f` | S5 (+S5t) handlers.py |
| 2 | `f9b2ad0` | S4 (+S4t) layout.py |
| 3 | `c1414c6` | S3 generate_panel.py + cli redirect |
| 4 | `47804a7` | S2 scene.py |
| 5 | `cf3c8bc` | S1 (+S1t) presentation.py |
| 6 | `24be568` | S0 characterization assertions |

Ledger bookkeeping commits (`5653d75`, `320917a`, `b00c8c2`, `faff2e9`,
`ecb4e45`, `9b4578f`, `9967a70`, `88f9801`, `0448b78`) touch only
`STEP_LEDGER.md` and need no revert for a code unwind.

## 9. Residual risk

- **Mixin name collisions are silent.** The composition is safe because
  method sets are disjoint today; a future method added to two mixins would
  shadow by MRO without an error. Mitigation candidate: a small test
  asserting pairwise disjointness of the four mixins' method names.
- **Broad re-export surface in `app.py`.** 46+ names re-exported
  (`# noqa: F401`) to keep `kayakgen.ui.web.app.<name>` paths alive. Tests
  that monkeypatch *moved* module globals must target the defining module
  (the C1 lesson); future moves need the same audit.
- **Union source-reads in tests are coupled to the module split.** The
  redirected `read_text()` targets in the four edited test files name the
  new modules; a further split would need the same mechanical re-derivation.
- **Integration is pending.** The campaign branch
  (`striatum/refactoring-campaign-kayakgen-smoke-1`, head `0448b78` plus
  this report's commit) is verified but not merged; `main` still holds the
  pre-campaign tree. Until the operator integrates, the two diverge and
  any hotfix to `kayakgen/ui/web/` on `main` would need replaying onto the
  branch (or vice versa).
- **The F3/F4 reds remain red by design.** They are named, pinned, and
  unchanged — but they stay a standing trap for anyone reading raw suite
  output without this report's framing.
