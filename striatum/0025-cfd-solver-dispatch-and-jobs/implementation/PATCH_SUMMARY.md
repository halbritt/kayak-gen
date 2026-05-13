author: operator [self-declared: operator-implementer]

# Patch summary - workflow 0025

## Files changed

- `.claude/skills/striatum-*.md` and `.codex/agents/striatum-*.md`: refreshed
  Striatum skill bundles to match the installed runtime after doctor reported
  bundle drift.
- `docs/rfcs/0015-cfd-solver-dispatch-and-jobs.md`: marked RFC 0015 as
  `partial local-dispatch`, documented landed local state handling, and listed
  real-solver/web/validation deferrals.
- `docs/rfcs/README.md`: updated the RFC 0015 status and roadmap summary.
- `kayakgen/eval/cfd.py`: replaced by the `kayakgen.eval.cfd` package while
  preserving `evaluate_cfd` and `CfdNotImplementedError`.
- `kayakgen/eval/cfd/__init__.py`: exported the CFD boundary and local
  dispatch helpers.
- `kayakgen/eval/cfd/jobs.py`: added local job/run/profile models, deterministic
  job directories, mesh readiness gating, unavailable adapter behavior, and
  mock failed-command handling.
- `kayakgen/cli/main.py`: added `kayakgen cfd prepare/status/run/profiles`.
- `tests/test_cfd_jobs.py`: added core model, readiness, unavailable, and
  failed-command tests.
- `tests/test_cli.py`: added CLI prepare/status/unavailable and watertight
  readiness rejection tests.
- `OPERATOR_REPORT.md` and
  `docs/workflows/0025-cfd-solver-dispatch-and-jobs/OPERATOR_REPORT.md`:
  updated workflow progress and verification state.

## Findings addressed

- F-001: landed only the local CFD dispatch contract; no real solver
  integration.
- F-002: `cfd prepare` loads mesh manifests, enforces required mesh profile, and
  rejects readiness below the selected solver profile requirement.
- F-003: job/run records use `result_semantics: raw_unvalidated`, and CLI status
  prints that CFD results are raw and unvalidated.
- F-004: job records persist mesh manifest reference, solver profile, speed,
  seawater density, kinematic viscosity, schema version, warnings, and positive
  value validation.
- F-005: local job IDs are derived from stable mesh/profile/fluid inputs and
  write inspectable `job.json`, `profile.json`, and `run.json` artifacts.
- F-006: unavailable profiles write `status: unavailable`; the mock local-command
  profile writes `status: failed`, `error_kind: command_failed`, error text, and
  stdout/stderr logs.
- F-007: RFC/status docs and focused tests now match the landed local-dispatch
  boundary.

## Verification

- `.venv/bin/python -m pytest tests/test_cfd_jobs.py tests/test_cli.py -q` ->
  21 passed.
- `.venv/bin/python -m pytest -q` -> 160 passed.
- `git diff --check` -> clean.
- `striatum --repo . doctor` -> clean after refreshing Striatum skill/plugin
  bundles.
- `.venv/bin/ruff --version` -> not available (`.venv/bin/ruff` is missing).
