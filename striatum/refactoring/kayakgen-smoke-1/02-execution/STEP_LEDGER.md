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

(appended one per slice, before the next slice starts)
