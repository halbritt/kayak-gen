# Interface and operations review - 0010

author: operator
Date: 2026-05-12
Reviewer: codex
Verdict intent: needs_revision

## Summary

Desktop 2D GUI and station-view behavior mostly matches RFCs 0002/0003, and
the test suite passes in the repo `.venv`. The remaining gaps are concentrated
in operations and web completion: Docker/readme packaging needs an explicit
check, RFC 0008 REST/share behavior is not wired, the PyVista desktop preview
drops newer hull parameters, and the CLI/workflow state overclaims completion.

## Commands run

```text
python3 -m pytest -q -> failed: No module named pytest.
.venv/bin/python -m pytest -q -> 59 passed.
.venv/bin/kayakgen --help -> commands: init, generate, evaluate, view, serve; no sweep.
rg "/api/(evaluate|stl|hulls|jobs)|add_route|aiohttp|FastAPI" kayakgen tests -> no mounted API routes found.
git status --short -- docs/workflows/0010-rfc-completion-review-remediation .codex -> both paths untracked.
```

## Findings

### F-OPS-001 - Docker build context omits declared project readme

- Severity: major
- RFC: 0008 deployment / acceptance criteria
- File(s): `pyproject.toml:9`, `Dockerfile:11`
- What you found: `pyproject.toml` declares `readme = "AGENTS.md"`, but the
  Dockerfile copies only `pyproject.toml`, `kayakgen/`, and the three shim
  files before running `pip install -e ".[web]"`. This creates an avoidable
  packaging risk in the container build context.
- Suggested remediation: Copy `AGENTS.md` before `pip install`, or change the
  project readme to a file included in the Docker context.
- Evidence: `Dockerfile` lacks `COPY AGENTS.md ./`; `pyproject.toml` names it
  as the readme. Operator note: an editable dry-run from a temp context did
  not fail, so this should be verified with an actual Docker build or demoted
  if setuptools keeps accepting it.

### F-OPS-002 - RFC 0008 REST API and job stubs are not implemented

- Severity: major
- RFC: 0008 REST API surface and Heavy-CFD tier
- File(s): `docs/rfcs/0008-web-frontend.md`, `kayakgen/ui/web/app.py`,
  `kayakgen/ui/web/controllers.py`
- What you found: RFC 0008 requires `/api/evaluate`, `/api/stl`,
  `/api/hulls`, and 501 job stubs. The code has pure helper functions such as
  `evaluation_for_state`, but no aiohttp/FastAPI/trame route mounting in the
  app factory.
- Suggested remediation: Mount the promised routes on the Trame server app
  and add REST contract tests comparing `/api/evaluate` to `kayakgen evaluate`.
- Evidence: Search found no route registration or `/api/jobs`; only docstrings
  and tests mention `/api/evaluate`.

### F-OPS-003 - URL sharing is helper-only, not page-load or clipboard behavior

- Severity: major
- RFC: 0008 URL state and acceptance criteria
- File(s): `docs/rfcs/0008-web-frontend.md`, `kayakgen/ui/web/app.py`,
  `tests/test_web.py`
- What you found: `[Share]` only sets `state.share_url` to a relative
  `?hull=...` string. `load_from_query()` exists, but it is not wired to
  initial browser query parsing; tests call it manually. There is also no
  clipboard action and no `/api/hulls` id fallback.
- Suggested remediation: Parse `hull` during app startup/session
  initialization, make Share copy or expose the full URL, and implement or
  explicitly defer the id-store fallback.
- Evidence: `rg load_from_query` returns only the method definition and the
  manual unit test.

### F-OPS-004 - PyVista desktop preview drops `beam_wl` and `bow_rake`

- Severity: major
- RFC: 0002 3D view tracks sliders; RFC 0007 UI consumes current Hull parameters
- File(s): `kayakgen/ui/desktop.py:36`, `kayakgen/ui/desktop.py:267`,
  `kayakgen/ui/pv_window.py:13`
- What you found: The desktop GUI includes `beam_wl` and `bow_rake` in its
  Hull translation, but `pv_window.py` has its own `_GUI_TO_HULL` map that
  omits both. Opening or updating the 3D window reconstructs a `Hull` without
  those values, so the 3D preview can disagree with the 2D plots, metrics,
  and STL export.
- Suggested remediation: Share one GUI-param-to-Hull adapter or add the
  missing fields to `pv_window.py`; add a focused test for the adapter so
  future hull parameters cannot silently disappear.
- Evidence: `beam_wl` and `bow_rake` are present in `desktop.py` but absent
  from `pv_window.py`.

### F-OPS-005 - `kayakgen sweep` promised by RFC 0007 is missing

- Severity: minor
- RFC: 0007 CLI
- File(s): `docs/rfcs/0007-architectural-revisit.md`, `kayakgen/cli/main.py`
- What you found: RFC 0007 lists `kayakgen sweep <sweep.yaml> --out <dir>`.
  The actual CLI exposes `init`, `generate`, `evaluate`, `view`, and `serve`,
  but no `sweep` command or explicit stub.
- Suggested remediation: Add a `sweep` command stub that exits with a clear
  not-implemented status, or implement the minimal YAML-to-output-dir sweep
  contract.
- Evidence: `.venv/bin/kayakgen --help` lists no `sweep`.

### F-OPS-006 - Workflow state is dirty despite `allow_dirty: false`

- Severity: minor
- RFC: workflow hygiene
- File(s): `docs/workflows/0010-rfc-completion-review-remediation/workflow.json`,
  `docs/workflows/0010-rfc-completion-review-remediation/OPERATOR_REPORT.md`
- What you found: The workflow declares `allow_dirty: false`, and the run was
  prepared/started while `.codex/` and the workflow directory were untracked.
- Suggested remediation: Commit the workflow artifacts or update the operator
  report to reflect the dirty/untracked state before remediation jobs rely on
  it.
- Evidence: `git status --short` shows `.codex/` and the workflow directory
  as untracked.
