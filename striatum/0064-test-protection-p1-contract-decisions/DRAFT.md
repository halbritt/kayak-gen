# Draft — Workflow 0064: test-protection P1 contract decisions (D048 + D049)

author: author-claude-001
date: 2026-06-06
run: run_f090c84339d75237140b6b6f9a681260
branch: striatum/0064-test-protection-p1-contract-decisions (worktree wt_5beff36f7c2d6e0675a6c2f2b20bc154)

The two operator-decided contract fixes from `docs/DECISION_LOG.md` rows
D048 and D049 (remediation plan P1-COMPARE-GATE / P1-FIT-KIND, audit rows
R2 / R1, BUG-026 / BUG-001), landed in order, one commit per decision.

## Slice 1 — D048 compare admissibility refusal (`565a8cb494d352ed375f096dd23eb039d9f54b02`)

```
 docs/ARCHITECTURE_MAP.md   |  2 ++
 docs/USER_GUIDE.md         | 23 +++++++++++++-----
 docs/bug-hunt/LEDGER.md    |  2 +-
 kayakgen/cli/main.py       | 14 ++++++++++-
 kayakgen/search/compare.py | 28 ++++++++++++++++++----
 tests/test_compare.py      | 60 ++++++++++++++++++++++++++++++++++++++++++++++
 6 files changed, 117 insertions(+), 12 deletions(-)
```

- `build_comparison_report` now calls
  `ensure_objectives_claim_admissible_for_search` (the forbidden-path gate in
  `kayakgen/search/pareto.py` is **called, not modified**) on the selected
  objectives, after the existing early high-angle-GZ refusal. The gate
  re-runs the RFC 0043 display-only refusal first, so that token still wins
  for high-angle keys in both modes (`test_compare_refuses_high_angle_objective`
  unchanged and green).
- New keyword-only `explicit_exploratory: bool = False` threaded through
  `build_comparison_report` / `write_comparison_report`, exposed as
  `--explicit-exploratory` on `kayakgen compare` (`kayakgen/cli/main.py`).
- Default behavior unchanged: defaults (`GM0_m`, `displacement_error_kg`,
  `mesh_problem_count`) are `default_conservative` and pass the gate without
  the flag; `test_default_comparison_report_is_deterministic` and the rest of
  the default-path suite are untouched and green. The only call sites of
  `build_comparison_report` outside the CLI (`services/design_report.py`,
  web read models) use default objectives and need no change.
- **Refusal is not removal**: every assertion of the prior auto-downgrade
  tests survives behind the opt-in —
  `test_raw_resistance_objective_is_exploratory_and_requires_provenance`,
  the forged/accepted/rejected/validation-only claim-contract tests, and
  `test_calibrated_resistance_is_not_final_design_fitness` now pass
  `explicit_exploratory=True` with all existing assertions intact
  (exploratory_frontier kind, accepted-use provenance warnings, objective
  metadata pins).
- The two `not_a_metric` unsupported-objective tests also moved to the
  opt-in path: the gate (whose semantics are frozen) refuses *unregistered*
  metrics without the opt-in, so the unsupported-warning behavior is pinned
  behind the flag with a comment explaining why.
- Docs: USER_GUIDE compare section documents the refusal + flag with an
  example; ARCHITECTURE_MAP gets a CLI-table row for the flag (precedent:
  the cfd `--allow-real-solver-execution` row) and a `compare.py` annotation;
  LEDGER BUG-026 → fixed citing D048 + this workflow.

### Refusal-token test evidence

```
tests/test_compare.py::test_raw_resistance_objective_without_opt_in_is_refused PASSED [ 50%]
tests/test_compare.py::test_design_fitness_objective_without_opt_in_is_refused PASSED [100%]
======================= 2 passed, 32 deselected in 0.63s =======================
```

The new regressions pin the full payload: `SearchObjectiveRefusedError`,
`reason["code"] == "search_objective_claim_not_admissible"`,
`reason["token"] == RFC_0044_SEARCH_OBJECTIVE_CLAIM_ADMISSIBILITY`,
`claim_state == "raw_unvalidated"` (Rt_N_last) and
`"uncalibrated_comparative"` (design_fitness), token present in `str(exc)`.

## Slice 2 — D049 StabilityFitRecord.kind (`5a2278851705aeede21ffddf1e4bdcf49c287537`)

```
 CHANGELOG.md                               |  23 ++++++
 docs/USER_GUIDE.md                         |   6 +-
 docs/bug-hunt/LEDGER.md                    |   2 +-
 kayakgen/eval/stability/accepted_fit.py    |   6 ++
 kayakgen/services/generative_jobs.py       |   5 +-
 tests/conftest.py                          |   3 +
 tests/test_cfd_in_loop_evaluator_status.py | 118 +++++++++++++++++++++--------
 7 files changed, 130 insertions(+), 33 deletions(-)
```

- `StabilityFitRecord` gains
  `kind: Literal["analytical", "cfd_in_loop"] = "analytical"` — additive
  with default. A new regression
  (`test_kind_is_additive_legacy_fit_json_parses_as_analytical`) dumps a
  fit, deletes `kind`, and re-validates: legacy JSONs parse as
  `"analytical"`.
- The forbidden 0063 digest pin is untouched and green:
  `tests/test_stability_fit_registry.py` (incl. the
  `fixture_canonical_sha256` pin, which hashes the FIXTURE manifest, not the
  fit record) passes unmodified — verified explicitly before and inside the
  full gate.
- `tests/conftest.py make_stability_acceptance_triple` gains a `kind`
  passthrough kwarg (default `"analytical"`, so all existing factory users
  are byte-identical).
- `tests/test_cfd_in_loop_evaluator_status.py` rewritten around REAL records
  from the factory; the rejected-verdict case re-validates a mutated dump
  through the production model (a genuinely valid rejected record, not a
  `model_copy` that skips validators). Exactly one SimpleNamespace test
  remains, labeled `SHAPE-TOLERANCE` with a docstring stating it is
  intentionally the only fake left.
- `cfd_in_loop_evaluator_status` docstring updated (the discriminator is no
  longer "deferred"); logic untouched.
- Docs: USER_GUIDE stage-4 fit-record bullet documents `kind` + the
  two-kind graduation rule; LEDGER BUG-001 → fixed citing D049; CHANGELOG
  carries one Unreleased→Changed entry covering both slices.
- Null finding: ARCHITECTURE_MAP does not enumerate `StabilityFitRecord`
  schema fields anywhere (checked: only the `accept-fit` CLI row mentions
  the record), so per the packet's conditional ("if it lists schema
  fields") no D049 ARCHITECTURE_MAP change was needed.

### Real-record graduation evidence

```
tests/test_cfd_in_loop_evaluator_status.py::test_kind_is_additive_legacy_fit_json_parses_as_analytical PASSED [ 10%]
tests/test_cfd_in_loop_evaluator_status.py::test_empty_registry_defaults_to_opt_in_only PASSED [ 20%]
tests/test_cfd_in_loop_evaluator_status.py::test_analytical_only_registry_stays_opt_in_only PASSED [ 30%]
tests/test_cfd_in_loop_evaluator_status.py::test_cfd_in_loop_only_registry_stays_opt_in_only PASSED [ 40%]
tests/test_cfd_in_loop_evaluator_status.py::test_both_accepted_covering_fits_promote_to_first_class PASSED [ 50%]
tests/test_cfd_in_loop_evaluator_status.py::test_non_covering_fit_does_not_promote PASSED [ 60%]
tests/test_cfd_in_loop_evaluator_status.py::test_rejected_fit_does_not_promote PASSED [ 70%]
tests/test_cfd_in_loop_evaluator_status.py::test_persistent_opt_out_wins_over_graduation PASSED [ 80%]
tests/test_cfd_in_loop_evaluator_status.py::test_persistent_opt_in_does_not_block_graduation PASSED [ 90%]
tests/test_cfd_in_loop_evaluator_status.py::test_structural_registry_tolerates_duck_typed_records PASSED [100%]
============================== 10 passed in 0.04s ==============================
```

`test_both_accepted_covering_fits_promote_to_first_class` is the BUG-001
kill shot: two real `StabilityFitRecord` instances (factory-built, one per
kind, covering scope) graduate to `first_class` — unreachable with
production records before this slice.

## Full gate

`.venv/bin/python -m pytest -q` (worktree, 8:35):

```
=========================== short test summary info ============================
SKIPPED [1] tests/test_cfd_run_stages.py:212: OpenFOAM-v2512 succeeded stage test is opt-in; set KAYAKGEN_OPENFOAM_SMOKE=1 and KAYAKGEN_OPENFOAM_LOCAL_RUN=1 and ensure /usr/lib/openfoam/openfoam2512/etc/bashrc is sourceable (override via KAYAKGEN_OPENFOAM_BASHRC).
SKIPPED [1] tests/test_cfd_run_stages.py:255: OpenFOAM-v2512 succeeded stage test is opt-in; set KAYAKGEN_OPENFOAM_SMOKE=1 and KAYAKGEN_OPENFOAM_LOCAL_RUN=1 and ensure /usr/lib/openfoam/openfoam2512/etc/bashrc is sourceable (override via KAYAKGEN_OPENFOAM_BASHRC).
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:109: OpenFOAM-v2512 smoke test is opt-in; set KAYAKGEN_OPENFOAM_SMOKE=1 and ensure /usr/lib/openfoam/openfoam2512/etc/bashrc is sourceable with interFoam on PATH (override via KAYAKGEN_OPENFOAM_BASHRC).
SKIPPED [1] tests/test_openfoam_v2512_smoke.py:213: OpenFOAM-v2512 smoke test is opt-in; set KAYAKGEN_OPENFOAM_SMOKE=1 and ensure /usr/lib/openfoam/openfoam2512/etc/bashrc is sourceable with interFoam on PATH (override via KAYAKGEN_OPENFOAM_BASHRC).
1319 passed, 4 skipped, 1 warning in 515.69s (0:08:35)
```

0 failed; exactly the 4 documented OpenFOAM opt-in skips. The single
warning is the *intended* corrupt-store-repair UserWarning emitted by the
workflow-0063 P1-STORE-ATOMIC repair path inside its own test
(`test_openfoam_rerun_ignores_stale_force_dat_and_raw_result`), pre-existing
on the base branch.

`ruff check .` → `All checks passed!` (one pre-existing invalid-`# noqa`
*warning* in `kayakgen/ui/web/generate_frontier_view.py:65`, untouched by
this workflow and present on the base branch).

## Notes for the reviewer

- Forbidden paths untouched: `kayakgen/search/pareto.py`,
  `kayakgen/eval/stability/registry.py`,
  `tests/test_stability_fit_registry.py`, `tests/test_services_boundaries.py`,
  `tests/test_import_boundaries.py` (verify with
  `git diff ed651a8..5a22788 --stat`: 11 files, none of these).
- `kayakgen/services/generative_jobs.py` changes are docstring-only
  (graduation logic byte-identical).
- The unknown-metric ("not_a_metric") tests moving behind the opt-in is a
  consequence of the frozen gate's semantics (unregistered metrics refuse
  by default), not a new decision; flagged here for explicit review since
  D048's text names only the two claim states.
