author: operator [self-declared: operator-final-review]

# Final review - workflow 0025

Verdict: accept

## Coverage table

| Ledger finding | Evidence |
| --- | --- |
| F-001 - Local CFD dispatch only | `kayakgen.eval.cfd.jobs` adds job/run/profile records and local adapters only. No OpenFOAM, SU2, hosted worker, Docker, or remote execution was added. |
| F-002 - Mesh profile/readiness gating | `prepare_local_job` loads `manifest.json`, checks required mesh profile, compares readiness levels, and rejects current watertight-solid packages below `cfd_ready`. |
| F-003 - Raw/unvalidated semantics | Job/run records carry `result_semantics: raw_unvalidated`; CLI prepare/status/run print `CFD results are raw and unvalidated.` |
| F-004 - Reproducible inputs | `job.json` persists mesh manifest reference, hull reference, solver profile, speed, seawater density, kinematic viscosity, schema version, readiness, and warnings; non-positive values raise `CfdDispatchError`. |
| F-005 - Deterministic local directories | Job IDs are derived from hull hash, mesh profile, solver profile, speed, density, and viscosity; tests verify repeated prepares use the same directory. |
| F-006 - Unavailable and failed-command states | Unavailable profiles write `status: unavailable` and `error_kind: solver_unavailable`; the mock local command writes `status: failed`, `error_kind: command_failed`, error text, return code, and stdout/stderr logs. |
| F-007 - Docs and tests | RFC 0015 and the RFC index now say `partial local-dispatch`; tests cover model round-trip, prepare success, readiness rejection, profile mismatch, invalid inputs, unavailable run, failed command, and CLI paths. |

## Verification

- `.venv/bin/python -m pytest tests/test_cfd_jobs.py tests/test_cli.py -q` -> 21 passed.
- `.venv/bin/python -m pytest -q` -> 160 passed.
- `git diff --check` -> clean.
- `striatum --repo . doctor` -> clean after refreshing Striatum skill/plugin bundles.
- `.venv/bin/ruff --version` -> unavailable; `.venv/bin/ruff` is missing.

## Gate result

Accept. The workflow satisfies the local dispatch contract and keeps solver
output truthful: no fake solver success, no real solver integration, and no
calibrated or validated CFD claims.
