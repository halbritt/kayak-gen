author: implementer-codex-gpt-5.5-006

# Patch Summary

## Outcome

- Verified `kayakgen serve` defaults to `SubprocessGenerativeJobManager`.
- Verified `--jobs-in-process` remains the explicit opt-in for `InProcessGenerativeJobManager`.
- Verified startup output reports the selected manager mode and jobs root.
- Confirmed the legacy `--jobs-subprocess` flag is absent from serve help.

## Files Reviewed

- `kayakgen/cli/main.py`
- `tests/test_cli_serve.py`
- `tests/test_generative_jobs_subprocess.py`

## Code Changes

No additional code changes were required in this packet: the scoped CLI flag
plumbing and focused serve tests were already present in the worktree and match
the stage-4 D-10 decision.

## Verification

```bash
.venv/bin/python -m pytest -q tests/test_cli_serve.py tests/test_generative_jobs_subprocess.py
```

Result: `10 passed in 10.25s`.
