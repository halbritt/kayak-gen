author: reviewer-codex-001
date: 2026-06-06
run: run_f090c84339d75237140b6b6f9a681260
job: job_run_f090c84339d75237140b6b6f9a681260_review
verdict: accept

# Review — Workflow 0064 D048/D049

## Findings

No findings.

## Contract Checks

- Forbidden paths are untouched in `git diff main...HEAD`: `kayakgen/search/pareto.py`, `kayakgen/eval/stability/registry.py`, `tests/test_stability_fit_registry.py`, `tests/test_services_boundaries.py`, and `tests/test_import_boundaries.py` have no branch diff.
- D048 is implemented by calling `ensure_objectives_claim_admissible_for_search` from `build_comparison_report` with default `explicit_exploratory=False`. The refusal-token regressions pin `RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY` for `Rt_N_last` (`raw_unvalidated`) and `design_fitness` (`uncalibrated_comparative`).
- `--explicit-exploratory` is plumbed through `kayakgen compare` to `write_comparison_report` and `build_comparison_report`. The prior exploratory report assertions were moved behind the opt-in rather than removed: `exploratory_frontier`, accepted-use provenance, warnings, and metadata assertions remain in `tests/test_compare.py`.
- Default comparison behavior remains conservative: default-objective tests continue to cover `GM0_m`, `displacement_error_kg`, and `mesh_problem_count` with no flag.
- D049 is additive: `StabilityFitRecord.kind` is `Literal["analytical", "cfd_in_loop"]` with default `"analytical"`, and the legacy JSON parse regression deletes `kind` before validation and asserts the analytical default.
- CFD-in-loop graduation tests now use real `StabilityFitRecord` instances via `make_stability_acceptance_triple`; coverage includes analytical-only, CFD-only, both-kinds covering, non-covering, rejected, persistent opt-out, and persistent opt-in. The remaining `SimpleNamespace` test is explicitly shape-tolerance only.
- The 0063 fixture-digest pin file is untouched by the branch diff.
- BUG-001 and BUG-026 ledger rows are closed with D049/D048 and workflow citations. USER_GUIDE, CHANGELOG, and ARCHITECTURE_MAP updates are present for the public CLI/schema surface changes.
- I found no new claim/readiness/accepted-use literal beyond the `kind` discriminator and no new forbidden-copy wording. The refusal token remains the RFC 0044 token, not a new local phrase.

## Gate

- `.venv/bin/python -m pytest -q` passed: `1319 passed, 4 skipped, 1 warning in 524.62s (0:08:44)`.
- The four skips are exactly the documented OpenFOAM opt-in skips: two in `tests/test_cfd_run_stages.py` and two in `tests/test_openfoam_v2512_smoke.py`.
- The warning is the expected corrupt-artifact repair `UserWarning` exercised by `tests/test_cfd_jobs.py::test_openfoam_rerun_ignores_stale_force_dat_and_raw_result`.
- `.venv/bin/python -m ruff check kayakgen tests` passed: `All checks passed!`.
