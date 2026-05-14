author: implementer-codex-gpt-5.5-004
date: 2026-05-14
job: job_run_c6989300a86c4c6cb66e44555bb19067_implement_sweep_objectives

# Patch Summary - Sweep Objective Metadata

## Scope

Implemented the workflow 0050 sweep/search prerequisite for explicit objective
metadata. The change is limited to `kayakgen/search/`, `tests/test_compare.py`,
and this workflow-local implementation artifact.

## Changes

- Added `kayakgen.search.objectives` with an `ObjectiveMetadata` read model and
  registry fields for metric label, unit, direction, source evaluator,
  availability rule, claim-state requirement, accepted-use requirement, and
  role.
- Kept conservative default objective candidates to `GM0_m`,
  `displacement_error_kg`, and `mesh_problem_count`, sourced from the metadata
  registry in the existing order.
- Added `objective_metadata` to `ComparisonReport` so generated reports carry
  the selected objective metadata beside the selected objective list.
- Preserved raw resistance behavior as explicit exploratory comparison only:
  `Rt_N_last` remains excluded from defaults, carries
  `role="explicit_exploratory"`, requires `claim_state_required="calibrated_model"`
  and `accepted_use_required="final_prediction"` metadata, and still triggers
  accepted-use provenance warnings unless the full calibrated-prediction gate
  is satisfied.
- Added explicit metadata for the reserved `design_fitness` objective so
  calibrated resistance still does not become final design fitness.
- Added an unsupported-objective metadata fallback for explicit unknown metrics.

## Files Changed

- `kayakgen/search/objectives.py`
- `kayakgen/search/compare.py`
- `kayakgen/search/__init__.py`
- `tests/test_compare.py`
- `striatum/0051-implementation-burndown-stage1/implementation/sweep_objectives/PATCH_SUMMARY.md`

## Verification

- `pytest tests/test_compare.py tests/test_pareto.py tests/test_sweep.py tests/test_cli.py`
  - Result: 57 passed.
- `git diff --check -- kayakgen/search/__init__.py kayakgen/search/compare.py kayakgen/search/objectives.py tests/test_compare.py`
  - Result: clean.
- `python -m compileall kayakgen/search`
  - Result: clean.

## Notes

The worktree already contained unrelated modifications outside this packet's
write scope when the implementation pass completed, including docs, web, CFD,
calibration, volume-mesh, and operator-report paths. Those were left untouched.
