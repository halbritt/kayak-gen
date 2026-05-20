author: integrator-codex-gpt-5.5-001

# Integration Patch Summary

## Scope

- Integrated the RFC 0057 stage-4 Generate tab modules into
  `kayakgen/ui/web/app.py`.
- Kept the Generate panel on the form-builder primary path with the raw JSON
  editor as an escape hatch.
- Wired `KayakgenApp` to use `SubprocessGenerativeJobManager` by default when
  no manager is supplied.

## App wiring

- `KayakgenApp.__init__` now installs the Generate auto-poll listener after
  controller callback wiring.
- Added `ctrl.apply_form_to_json`, and made Submit Search / Submit Sweep build
  a spec from form state when the raw JSON editor is empty.
- Replaced the legacy selected-job-only fork button with per-succeeded-job
  `render_fork_button(self, job_summary=...)` calls.
- The Generate tab now calls both `render_spec_form_section(self)` and
  `render_frontier_view_section(self)`.

## Tests

- Updated `tests/test_generative_jobs_web.py` panel-level coverage to exercise
  form serialization through controller callbacks.
- Added coverage that default `create_app()` uses the subprocess manager.
- Added coverage that the integrated Generate tab invokes the stage-4 fork
  renderer for succeeded rows.

## Verification

- `.venv/bin/pytest tests/test_generative_jobs_web.py -q`
- `.venv/bin/pytest tests/test_web_layout.py -q`
- `.venv/bin/pytest tests/test_generative_jobs_manager.py tests/test_generative_jobs_subprocess.py tests/test_cli_serve.py -q`
- `.venv/bin/ruff check kayakgen/ui/web/app.py tests/test_generative_jobs_web.py`
