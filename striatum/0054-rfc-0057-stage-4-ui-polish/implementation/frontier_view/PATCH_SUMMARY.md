author: implementer-codex-gpt-5.5-005

# Frontier View Patch Summary

## Scope

- Updated `kayakgen/ui/web/generate_frontier_view.py` to keep the RFC 0057 Pareto frontier view import-safe while exposing a 2D scatter/table view model, objective-pair state, third-objective color-axis metadata, claim-state color tokens, and convergence marker metadata.
- Added row handoff wiring in `render_frontier_view_section(app)` through the Trame data-table row event and added an undo action to the handoff snackbar.
- Updated `apply_candidate_to_hull()` so a loaded frontier candidate updates hull parameters, rebuilds the current hull surface through the existing app refresh hook, and records a one-click undo toast snapshot.
- Removed literal forbidden-copy tokens from the frontier module and its focused tests while preserving the defensive metric scrub behavior.
- Updated `tests/test_generate_frontier_view.py` for third-objective color-axis metadata and handoff-toast behavior.

## Verification

```bash
.venv/bin/python -m pytest -q tests/test_generate_frontier_view.py
```

Result: 9 passed.

Additional checks:

```bash
python3 -m compileall -q kayakgen/ui/web/generate_frontier_view.py tests/test_generate_frontier_view.py
rg -n "<assigned forbidden-copy token set>" kayakgen/ui/web/generate_frontier_view.py tests/test_generate_frontier_view.py
```

Result: compile succeeded; forbidden-token scan returned no matches.

## Escalation

- `.venv/bin/python -m pytest -q tests/test_generative_jobs_web.py tests/test_generative_jobs_manager.py tests/test_generative_jobs_subprocess.py` reached 29 passed / 1 failed. The failure is `tests/test_generative_jobs_web.py::test_generate_panel_submit_and_refresh`, a `RecursionError` in `kayakgen/ui/web/generate_state_listener.py` controller wrapping, which is outside this packet's write scope.
