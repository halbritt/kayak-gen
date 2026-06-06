author: preservation-reviewer-codex-001

# Preservation Review

Verdict: `accept_with_findings`

## Findings

1. **Non-blocking commit-shape caveat: the executed branch has six code
   slice commits plus interleaved ledger commits, not only six commits.**

   The preservation-critical discipline is satisfied: each planned code
   slice has exactly one code commit, and each code commit stays inside the
   declared blast radius:

   - S0 `24be568`
   - S1(+S1t) `cf3c8bc`
   - S2 `47804a7`
   - S3 `c1414c6`
   - S4(+S4t) `f9b2ad0`
   - S5(+S5t) `170b01f`

   The additional commits (`5653d75`, `320917a`, `b00c8c2`, `faff2e9`,
   `ecb4e45`, `9b4578f`, `9967a70`, `88f9801`, `0448b78`) touch only
   `striatum/refactoring/kayakgen-smoke-1/02-execution/STEP_LEDGER.md`.
   This is not a preservation failure, but the final report should describe
   the history as "six code slice commits plus ledger bookkeeping commits"
   rather than "six total commits."

2. **Non-blocking operational note: attempt 2 fixed a detached-worktree
   publication issue by fast-forwarding the run branch to the already
   executed slice stack.**

   The ledger's attempt-2 explanation is consistent with the current
   branch: the current HEAD is `0448b78`, and
   `git log --oneline --reverse a31773e..0448b78` contains the recorded
   slice stack followed by ledger-only commits. I found no evidence that
   the code slice commits were replayed or rewritten during this branch
   repair.

## Preservation Checks

- Target shape landed: `presentation.py`, `scene.py`, `generate_panel.py`,
  `layout.py`, and `handlers.py` are present under `kayakgen/ui/web/`.
  `kayakgen/ui/web/app.py` is 355 lines, under the plan's approximate
  600-line cap.
- Frozen witness files stayed untouched across the code slice stack:
  `tests/test_web_browser.py`, `tests/test_import_boundaries.py`,
  `tests/test_services_boundaries.py`, `pyproject.toml`, docs, model
  code, and root shims had no diff in `a31773e..170b01f`.
- Public entrypoints remain importable with the same signatures:
  `create_app(initial_hull=None, server=None, initial_query=None,
  generative_manager=None)` and `KayakgenApp(server=None,
  initial_hull=None, initial_query=None, generative_manager=None)`.
  `_default_generative_jobs_root_for_app` remains callable through
  `kayakgen.ui.web.app`.
- Sibling modules do not import `kayakgen.ui.web.app`; `rg` found only
  docstring/comment references.

## Replay Results

- `.venv/bin/python -m pytest -q`:
  `1 failed, 1307 passed, 4 skipped in 487.96s`. The failure is exactly
  the documented baseline singleton:
  `tests/test_services_boundaries.py::test_services_does_not_import_ui_or_cli[path2]`.
- `.venv/bin/python -m ruff check kayakgen tests`: passed.
- `KAYAKGEN_BROWSER_ACCEPTANCE=1 .venv/bin/python -m pytest tests/test_web_browser.py -m browser_acceptance -q`:
  `4 passed, 2 deselected in 36.55s`.
- `.venv/bin/python -m pytest -q tests/test_web.py tests/test_web_layout.py tests/test_web_inline_help.py tests/test_generative_jobs_web.py tests/test_cli_serve.py`:
  `93 passed in 56.23s`.
- `.venv/bin/python -m pytest -q tests/test_web_layout.py tests/test_web_inline_help.py tests/test_hydro_tab_descriptions.py tests/test_generative_jobs_web.py`:
  `65 passed in 42.71s`.
- `PYTHONPATH=$PWD ~/.cache/kayakgen-noweb-venv/bin/python -c "import kayakgen, kayakgen.cli.main; print('import check: OK')"`:
  `import check: OK`.
- `PYTHONPATH=$PWD ~/.cache/kayakgen-noweb-venv/bin/python -m pytest -q -p no:cacheprovider --continue-on-collection-errors`:
  `20 failed, 1114 passed, 24 skipped, 4 errors in 345.76s`, matching the
  committed plan's named extras-less failure/error set.

## Conclusion

The attempt-3 branch now contains the planned refactor, the replayed test
evidence matches the committed plan's preservation bars, and the frozen
surfaces I checked were untouched. No slice needs rework for preservation.
