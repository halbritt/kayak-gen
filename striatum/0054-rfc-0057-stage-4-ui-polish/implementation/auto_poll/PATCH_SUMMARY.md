author: implementer-codex-gpt-5.5-003

# Generate Auto-Poll Patch Summary

Implemented `kayakgen.ui.web.generate_state_listener.install_generate_state_listener(app)` for RFC 0057 stage 4 D-9.

## Changes

- Added cancellable Generate-panel auto polling with 1 second cadence when any job is `queued` or `running`, and 10 second cadence otherwise.
- Poll cadence reads the existing generative-job manager via `manager.list()`.
- Added terminal-transition tracking so `succeeded`, `failed`, and `resumable` transitions trigger one best-effort refresh of selected job detail panels.
- Added refresh coalescing for plain callback controllers so auto-poll does not immediately duplicate nearby manual Refresh Jobs presses.
- Preserved Trame controller safety by avoiding direct wrapping of Trame dispatcher objects.

## Tests

- `.venv/bin/pytest -q tests/test_generate_state_listener.py`
- `.venv/bin/pytest -q tests/test_generate_state_listener.py tests/test_generative_jobs_web.py tests/test_generative_jobs_manager.py tests/test_generative_jobs_subprocess.py`
