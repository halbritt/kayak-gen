---
schema_version: "striatum.support_ledger.v1"
artifact_kind: "support_ledger"
audited_artifact: "striatum/refactoring/kayakgen-smoke-1/01-plan/COMMITTED_PLAN.md"
---

author: refactoring-author-claude-001

# Step Ledger — kayakgen-smoke-1 execution (stage 2, execute_slices)

Date: 2026-06-05
Run: `run_f2fbd2ab9adefda44b5e72b6bfefafdf`, stage 2 (execute_slices), attempt 1
Plan under execution: `striatum/refactoring/kayakgen-smoke-1/01-plan/COMMITTED_PLAN.md`
Worktree: `.striatum/worktrees/wt_786ba8ec8412ad048f8c6e4eccc281cb`, branch
`striatum/refactoring-campaign-kayakgen-smoke-1`, starting commit `a31773e`.

One preservation claim per slice; each entry records slice id, what changed,
verification command, observed result, commit hash, and the rollback unit.
Rollback guarantees are LIFO-only per plan §7 (revert head of stack first).

Ledger-keeping note (declared, per plan §12): each slice lands as one code
commit; its ledger entry is committed immediately after in a separate
bookkeeping commit so the entry can record the slice commit's hash. Ledger
commits are outside every slice's net-diff accounting and do not affect the
LIFO revert path of the code commits.

## Stage-2 entry preconditions (plan §11)

**C4 re-scope: verified.** `workflow.json` `execute_slices.write_scope.allowed_paths`
equals the exact files-touched envelope of plan §11 (`kayakgen/ui/web/`,
`kayakgen/cli/main.py`, the four declared test files, plus this ledger path);
`tests/test_web_browser.py`, `tests/test_import_boundaries.py`,
`tests/test_services_boundaries.py`, and `pyproject.toml` are forbidden paths.

**Worktree note:** the run's confirmed branch
`striatum/refactoring-campaign-kayakgen-smoke-1` did not yet exist in git;
`striatum worktree create` failed with `invalid reference`. Created the branch
at `main` (= `a31773e`, the run's recorded starting tree) and re-ran worktree
create, which succeeded. No repo file was touched by this.

## Baseline reproduction (plan §11, before any write)

Tree: `a31773e` (unmodified), worktree clean at start.

| Command | Bar (plan §1.2/§8) | Observed |
|---|---|---|
| `.venv/bin/python -m pytest -q` | failure set == {`tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`} (F3 singleton), 1307 passed, 4 skipped | **PASS** — `1 failed, 1307 passed, 4 skipped in 495.17s (0:08:15)`; sole failure id is exactly the F3 singleton |
| `.venv/bin/python -m ruff check kayakgen tests` | exit 0 | **PASS** — "All checks passed!", exit 0 (pre-existing invalid-`# noqa` warnings in `generate_frontier_view.py`, not errors) |
| `KAYAKGEN_BROWSER_ACCEPTANCE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q` (strict) | 4 passed, 2 deselected | **PASS** — `4 passed, 2 deselected in 36.56s` |
| `noweb-venv python -c "import kayakgen, kayakgen.cli.main"` | succeeds | **PASS** — "import check: OK" (fresh venv: numpy, numpy-stl, pydantic, typer, click, pytest, pytest-benchmark; PYTHONPATH=worktree) |

**Baseline verdict: reproduced.** All four bars match plan §1.2 exactly.
Execution proceeds to S0.

## Slice entries

(one per slice, written before the next slice starts)

### S0 — characterization: jobs_root value pin in serve manager tests

- **Pre-slice dirty check (stop condition 8):** `git status --short` clean.
- **What changed:** `tests/test_cli_serve.py` only. Added one equality
  assertion (plus comment) to each of the two manager tests:
  `assert f"jobs_root={tmp_path / 'jobs'}" in result.output`. No source change.
- **Net diff:** +5 lines (cap 10). Gross == net (no relocation).
- **Preservation claim:** documents current `KAYAKGEN_GENERATIVE_JOBS_ROOT`
  resolution; behavior untouched.
- **Verification:**
  - `pytest -q tests/test_cli_serve.py` → `3 passed in 0.71s`
  - `.venv/bin/python -m ruff check kayakgen tests` → exit 0
  - Full suite → `1 failed, 1307 passed, 4 skipped in 510.64s (0:08:30)`;
    failure set exactly the F3 singleton. **Bar met.**
- **Commit:** `24be568`
- **Rollback unit:** revert commit `24be568`.

### S1 (+S1t) — presentation.py extraction

- **Pre-slice dirty check (stop condition 8):** clean.
- **What changed:** `kayakgen/ui/web/presentation.py` (new),
  `kayakgen/ui/web/app.py`, plus S1t test edits in `tests/test_web_layout.py`
  and `tests/test_web_inline_help.py`. app.py lines 98–710 (constants/CSS/copy,
  `validity_badge_title_for`, `_param_row_raw_attrs`) and 766–803 (`_pre_html`,
  `_resistance_table_html`, `_generative_job_state_flags`) relocated
  **byte-identically** (verified by substring comparison against
  `HEAD:app.py`); app.py re-exports all 46 names by name (`# noqa: F401`);
  now-unused `class_preset_options` dropped from app.py's controllers import.
- **Net diff:** app.py +48 (re-export block) / 1 import-name deletion;
  presentation.py ~21 non-relocation lines (docstring + imports). S1 net ≈ 70
  (cap 80). S1t: layout +16/−5, inline_help +4/−3 ≈ 16 edited lines (cap 20).
- **Preservation claim:** byte-identical constant values and helper bodies;
  every F1 name importable from `kayakgen.ui.web.app` — verified by an
  identity check (`getattr(app, n) is getattr(presentation, n)` for all 46).
- **S1t detail (all assertion strings unchanged):**
  - C2(i) step 1: `presentation_source` read added in
    `test_parameter_slider_labels...`; aria-label assertion repointed.
  - C2(ii): union test scans `presentation.py` via the `with_name` idiom.
  - Mechanical pointer redirects for S1-displaced strings the plan's
    inventory did not itemize line-by-line but declares as the default edit:
    `test_web_layout.py` resistance/export contract (single-file read became
    app+presentation concatenation — equivalent for its all-positive
    assertions), share-URL positive (`"Shareable URL copied"`, displaced at
    S1, not S5 as the plan's S5t row guessed; redirected here per the F2
    same-commit rule), badge-ordering anchor (`"region-params"` now in
    presentation.py; read prepends presentation.py preserving the original
    constants-before-layout order), and `test_web_inline_help.py`
    comparison-toggle copy constants.
  - `test_hydro_tab_descriptions.py`: **no S1 edit needed** (plan listed it
    in S1t's files; its assertions target layout-region text that moves at
    S4) — null finding, recorded.
- **Verification:**
  - Targeted (decision §4 row 1): `pytest -q tests/test_web.py
    tests/test_web_layout.py tests/test_web_inline_help.py
    tests/test_generate_panel_label_rendering.py
    tests/test_hydro_tab_descriptions.py` → `81 passed in 50.52s`
  - Full suite → `1 failed, 1307 passed, 4 skipped in 491.57s (0:08:11)`;
    failure set exactly the F3 singleton. **Bar met.**
  - ruff → exit 0. Extras-less import check → OK.
- **Commit:** `cf3c8bc`
- **Rollback unit:** revert commit `cf3c8bc` (LIFO: unwound last once
  successors land).

### S2 — scene.py (SceneMixin)

- **Pre-slice dirty check (stop condition 8):** clean.
- **What changed:** `kayakgen/ui/web/scene.py` (new), `kayakgen/ui/web/app.py`.
  `_build_polydata` + `_make_actor` (module functions) and `_rebuild_scene`
  relocated **byte-identically** (verified against `HEAD:app.py`);
  `class KayakgenApp(SceneMixin)`; app.py re-exports `_build_polydata` /
  `_make_actor` (`# noqa: F401`, defensive — no test imports them; the only
  external reference is `test_ui_theme.py`'s AST walk, which rglobs all of
  `kayakgen/ui/` and so scans scene.py automatically); now-unused
  `import numpy as np` removed from app.py.
- **Net diff:** app.py +6/−66; scene.py ~20 non-relocation lines (docstring,
  imports, mixin declaration). Net ≈ 26 (cap 40).
- **Preservation claim:** byte-identical actor/mesh construction; no
  state-key changes (mixin methods read the same instance attributes).
- **Verification:**
  - Full suite → `1 failed, 1307 passed, 4 skipped in 503.00s (0:08:22)`;
    failure set exactly the F3 singleton. **Bar met.**
  - ruff → exit 0. Extras-less import check → OK.
- **Commit:** `47804a7`
- **Rollback unit:** revert commit `47804a7`.

### S3 — generate_panel.py (GeneratePanelMixin) + cli redirect

- **Pre-slice dirty check (stop condition 8):** clean.
- **What changed:** `kayakgen/ui/web/generate_panel.py` (new),
  `kayakgen/ui/web/app.py`, `kayakgen/cli/main.py` (1 import line).
  Panel region (the plan's 1473–1751 range, which includes
  `load_from_query`) and `_default_generative_jobs_root_for_app` relocated
  **byte-identically** (verified against `HEAD:app.py`);
  `class KayakgenApp(GeneratePanelMixin, SceneMixin)`; app.py re-imports the
  jobs-root resolver (used in `__init__`, so the
  `kayakgen.ui.web.app._default_generative_jobs_root_for_app` alias holds);
  `cli/main.py:657` now imports from `generate_panel` (within the declared
  ≤2-line budget); 16 now-unused app.py imports pruned via ruff --fix.
  Per C6, generate_panel.py imports `generate_spec_form` names at module
  level (trame-bearing licensed by the §1.3 precedent).
- **Net diff:** app.py +5/−312 (panel import block + class line);
  cli/main.py 1 modified line; generate_panel.py ~50 non-relocation lines
  (docstring + imports + mixin declaration). Net ≈ 56 (cap 60).
- **Preservation claim:** submit/cancel/fork/resume payloads and transition
  order unchanged (byte-identical method bodies; runtime-asserting tests
  green); jobs-root resolution value-pinned by S0 stays green.
- **Verification:**
  - `pytest -q tests/test_generative_jobs_web.py tests/test_cli_serve.py`
    → `18 passed in 8.22s`
  - Full suite → `1 failed, 1307 passed, 4 skipped in 496.40s (0:08:16)`;
    failure set exactly the F3 singleton. **Bar met.**
  - ruff → exit 0. Extras-less import check → OK.
  - Browser insurance (non-gating, non-strict) → `4 passed, 2 deselected
    in 35.84s`.
- **Commit:** `c1414c6`
- **Rollback unit:** revert commit `c1414c6`.

### S4 (+S4t) — layout.py (LayoutMixin)

- **Pre-slice dirty check (stop condition 8):** clean.
- **What changed:** `kayakgen/ui/web/layout.py` (new), `kayakgen/ui/web/app.py`,
  plus S4t edits in `tests/test_web_layout.py`, `tests/test_web_inline_help.py`,
  `tests/test_hydro_tab_descriptions.py`, `tests/test_generative_jobs_web.py`.
  Layout region (`_region_attrs`, `_build_layout`, `_render_export_menu`,
  `_export_menu_action`, all `_render_*_tab`, `_render_generate_job_fork_buttons`,
  `_render_status_bar`) relocated **byte-identically** (verified against
  `HEAD:app.py`); `class KayakgenApp(GeneratePanelMixin, LayoutMixin,
  SceneMixin)`; 8 now-unused app.py imports pruned (html, trame widget/layout
  imports, render hooks).
- **Net diff:** app.py +2/−791; layout.py ~49 non-relocation lines (docstring +
  imports + mixin declaration) → S4 code net ≈ 51 (cap 80). S4t: layout
  +30/−18, inline_help +5/−5, hydro +3/−2, generative_jobs_web +2/−2 → raw
  insertions 40 (== cap 40); by per-redirect edit-unit counting ≈ 32,
  matching the plan's estimate.
- **Preservation claim:** `LAYOUT_TEST_IDS`/`REGION_CLASSES` values, DOM ids,
  widget construction order unchanged (byte-identical bodies; strict browser
  gate is the end-to-end witness and is green).
- **S4t detail (all assertion strings unchanged):**
  - **C1 discharged:** monkeypatch at `test_generative_jobs_web.py:547` now
    targets `kayakgen.ui.web.layout`; the fake and `calls == ["done-job"]`
    untouched; the fork-button test passes post-S4.
  - **C2(i) step 2 / C2(iii):** slider-construction positives and the eight
    negative assertions now evaluate against an app.py+layout.py union read —
    for negatives this is exactly the declared `app.py ∪ layout.py` scope; for
    positives the union is the pre-split single-file semantics.
  - **C2(ii) step 2:** forbidden-claim union test scans layout.py.
  - Bulk pointer redirects to layout.py for functions whose every target
    moved; split reads where mixed (css-tokens test keeps the
    `workspace_style_html` init count on app.py and redirects the
    `html_widgets.Div(v_html=…)` count to layout.py).
  - Ordering tests (badge-in-rail, comparison-tab-order) keep their find
    anchors in one concatenated read preserving pre-split source order.
- **Verification:**
  - Targeted: `pytest -q tests/test_web_layout.py tests/test_web_inline_help.py
    tests/test_hydro_tab_descriptions.py tests/test_generative_jobs_web.py`
    → `65 passed in 40.58s`
  - Full suite → `1 failed, 1307 passed, 4 skipped in 491.55s (0:08:11)`;
    failure set exactly the F3 singleton. **Bar met.**
  - **Strict browser acceptance (C5, mandatory gate):**
    `KAYAKGEN_BROWSER_ACCEPTANCE=1 .venv/bin/python -m pytest
    tests/test_web_browser.py -m browser_acceptance -q` →
    `4 passed, 2 deselected in 35.67s`. **Gate green.**
  - ruff → exit 0. Extras-less import check → OK.
- **Commit:** `f9b2ad0`
- **Rollback unit:** revert commit `f9b2ad0`.

### S5 (+S5t) — handlers.py (HandlersMixin); final shape

- **Pre-slice dirty check (stop condition 8):** clean.
- **What changed:** `kayakgen/ui/web/handlers.py` (new),
  `kayakgen/ui/web/app.py`, plus the S5t union expansion in
  `tests/test_web_layout.py`. Handlers region (`_current_hull` …
  `_load_cfd_raw_result`) relocated **byte-identically** (verified against
  `HEAD:app.py`); `class KayakgenApp(HandlersMixin, GeneratePanelMixin,
  LayoutMixin, SceneMixin)` — the plan §6 composition order, methods
  disjoint, MRO inert; 30 now-unused app.py imports pruned;
  `STATE_SNAPSHOT_KEYS` re-export retained (`# noqa: F401`) because
  `test_web_layout.py` reads it via `web_app.` (invariant 2).
  **app.py settles at 355 lines** (≤ the goal's ~600 cap; plan projected
  ≈400–450): import/re-export block, `__init__` + parameter-rail state,
  mixin composition, `create_app`.
- **Net diff:** app.py +3/−434; handlers.py ~68 non-relocation lines
  (docstring + imports + mixin declaration) → S5 net ≈ 71 (cap 100).
  S5t: test_web_layout.py +11/−1 (cap 20).
- **Preservation claim:** `create_app`/`KayakgenApp` import paths +
  signatures unchanged; trame ctrl/state bindings identical
  (byte-identical bodies; strict browser gate green).
- **S5t detail:** C2(ii) final union expansion — the forbidden-claim test
  now scans app.py + presentation.py + layout.py + handlers.py +
  generate_panel.py + controllers + spec form (+ frontier render hook):
  the claim-vocabulary guard covers every render-feeding module, as
  discharged. No other test strings were displaced at S5 — the plan's S5t
  expectation of share-toast pointer redirects had already been satisfied
  at S1 (the literal's definition moved then; recorded in the S1 entry).
- **Verification:**
  - Targeted: `pytest -q tests/test_web.py tests/test_web_layout.py
    tests/test_web_inline_help.py tests/test_generative_jobs_web.py
    tests/test_cli_serve.py` → `93 passed in 54.36s`
  - Full suite → `1 failed, 1307 passed, 4 skipped in 497.90s (0:08:17)`;
    failure set exactly the F3 singleton. **Bar met.**
  - **Strict browser acceptance (C5, mandatory gate):**
    `KAYAKGEN_BROWSER_ACCEPTANCE=1 .venv/bin/python -m pytest
    tests/test_web_browser.py -m browser_acceptance -q` →
    `4 passed, 2 deselected in 36.64s`. **Gate green.**
  - **Extras-less full suite (§1.3 method, once after S5):**
    `20 failed, 1114 passed, 24 skipped, 4 errors in 356.59s` — the
    failure/error id set is **identical** to §1.3's named set
    (collection errors: `test_generate_spec_form.py`,
    `test_hull_parameter_metadata.py`; runtime errors: the two
    `test_cli_serve.py` manager tests; failures: 4 ×
    `test_generative_jobs_fork.py` + 15 × `test_generative_jobs_web.py` +
    the F3 singleton). The set did not grow. **Bar met.**
  - ruff → exit 0. Extras-less import check → OK.
- **Commit:** `170b01f`
- **Rollback unit:** revert commit `170b01f` (head of stack at campaign end).

## Campaign close-out

All slices S0 → S5(+S5t) landed in order with per-slice verification; no
stop condition fired. Final landed stack (oldest → newest code commits):
`24be568` (S0), `cf3c8bc` (S1+S1t), `47804a7` (S2), `c1414c6` (S3),
`f9b2ad0` (S4+S4t), `170b01f` (S5+S5t). Rollback remains LIFO-only per
plan §7: revert from `170b01f` backwards.

Final post-S5 verification (the repository's full verification suite, §8):

| Command | Bar | Observed |
|---|---|---|
| Full suite | failure set == F3 singleton | **PASS** — 1 failed / 1307 passed / 4 skipped |
| ruff | exit 0 | **PASS** |
| Strict browser acceptance | 4 passed, 2 deselected | **PASS** |
| Extras-less full suite | §1.3 failure/error id set, no growth | **PASS** — exact set |
| Import check | clean | **PASS** |

Target shape delivered: `kayakgen/ui/web/` now holds `presentation.py`,
`scene.py`, `generate_panel.py`, `layout.py`, `handlers.py` as siblings
imported by `app.py` (dependency direction sibling → imported-by-app,
invariant 7 held; no sibling imports `app.py`), and `app.py` is a
355-line integrator. Frozen surfaces untouched: `tests/test_web_browser.py`,
`tests/test_import_boundaries.py`, `tests/test_services_boundaries.py`,
`pyproject.toml` (verified: no commit in the stack touches them).

## Attempt-2 revision (response to PRESERVATION_REVIEW.md `needs_revision`)

Reviewer findings 1–3 (no slice commits in the reviewed tree; refactor
absent; ledger unauditable) share one root cause, now fixed:

- **Root cause (harness, not execution):** `striatum worktree create` gave
  this job a **detached-HEAD** worktree based at `a31773e`. All six slice
  commits plus ledger commits landed on that detached HEAD (through
  `9967a70`) and never advanced the run's confirmed branch
  `striatum/refactoring-campaign-kayakgen-smoke-1`, which still pointed at
  `a31773e` — so the reviewer's own worktree, cut from the branch, contained
  none of the executed work. (Striatum harness finding, worth upstreaming:
  a per-job worktree for a `repo_write` job should attach to the run
  branch, or job completion should advance it.)
- **Fix (no replay, per plan §12 discipline 2):** verified
  `a31773e` is an ancestor of `9967a70`, then fast-forwarded
  `striatum/refactoring-campaign-kayakgen-smoke-1` to `9967a70` and
  re-attached the execution worktree to the branch. The slice stack is
  unchanged — same commits, same hashes as recorded above; nothing was
  re-executed or rewritten.
- **Reviewer replay note (extras-less import check):** `noweb-venv` is not
  a PATH binary; it is the plan §1.3 shorthand for a fresh venv with only
  core deps. Recipe used here:
  `python3 -m venv ~/.cache/kayakgen-noweb-venv && ~/.cache/kayakgen-noweb-venv/bin/pip
  install numpy numpy-stl pydantic typer click pytest pytest-benchmark`,
  then from the worktree:
  `PYTHONPATH=$PWD ~/.cache/kayakgen-noweb-venv/bin/python -c "import kayakgen, kayakgen.cli.main"`
  (per-slice check) and
  `PYTHONPATH=$PWD ~/.cache/kayakgen-noweb-venv/bin/python -m pytest -q -p
  no:cacheprovider --continue-on-collection-errors` (post-S5 full run).
- The reviewer's own replay on unmodified `a31773e` (full suite F3
  singleton, ruff pass, strict browser 4 passed/2 deselected) independently
  re-confirms the recorded baseline of §1.2.
