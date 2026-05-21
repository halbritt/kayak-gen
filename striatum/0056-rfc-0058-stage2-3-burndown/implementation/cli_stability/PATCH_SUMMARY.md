author: implementer-codex-gpt-5.5-003

# RFC 0058 Stage 3 Stability CLI Patch Summary

## Changes

- Added `kayakgen/cli/stability_cli.py` with the `stability_app` sub-app and four schema-only subcommands:
  - `ingest-rig-run`
  - `promote-fixture`
  - `accept-fit`
  - `residual-plot`
- Registered the sub-app from `kayakgen/cli/main.py`.
- Preserved the pre-existing `kayakgen stability <hull>` evaluator shape through a hidden legacy command route.
- Added `tests/test_cli_stability.py` covering happy paths, validation failures, overwrite refusal, no-op candidate promotion, accepted-fit packet gating, and SVG stub output.
- Added `data/stability/` to `.gitignore`.

## Verification

- `.venv/bin/python -m pytest tests/test_stability_cli_high_angle.py tests/test_cli_stability.py -q`
  - `12 passed`
- `.venv/bin/python -m ruff check kayakgen/cli/stability_cli.py kayakgen/cli/main.py tests/test_cli_stability.py`
  - `All checks passed`
