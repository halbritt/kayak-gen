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
