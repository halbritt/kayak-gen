author: reviewer-codex-001
verdict: accept
date: 2026-06-06

# Review — Workflow 0065 P2 Top-ups

No findings.

## Checks

- Scope: `git diff main...HEAD --name-only` touches only `CHANGELOG.md`,
  `pyproject.toml`, `tests/test_hydrostatics.py`,
  `tests/test_generative_jobs_subprocess.py`,
  `tests/test_stability_fit_registry.py`, and
  `striatum/0065-test-protection-p2-topups/DRAFT.md`. No `kayakgen/` or
  `scripts/` edits are present.
- P2-HYDRO-ANCHOR: accepted. The closed-form derivation in
  `tests/test_hydrostatics.py::test_analytic_anchor_parabolic_body_volume_and_lcb`
  matches the V2 `round` section sampler: mirrored section area is
  `(4/3) * b * T`; with `b(xi) = b0 * (1 - xi^2) * (1 + c * xi)`,
  `V = (8/9) * b0 * T * L` and `LCB = 0.5 + c/10`. The `rtol=1e-2`
  tolerance is coarse relative to the stated observed drift and would fail
  an integration drift above the tolerance.
- P2-CANCEL-DETERMINISTIC: accepted. The new manager-level test runs the
  real runner entry point in-process with a controlled sweep runner and
  creates the cancel flag before the runner body executes, so the
  `cancelled_by_operator` contract is asserted without wall-clock races.
  The real-subprocess cancel/resume variants are explicitly labeled smoke.
- P2-REGISTRY-MICROGAPS: accepted. The three new tests pin the intended
  ANY-pass semantics, the hysteresis branch of gate 3a, and the touching
  heel-range pass boundary of gate 9. The workflow-0063 digest pin remains
  byte-identical to `main`.
- P2-REASON-ENUM: accepted. `test_every_reason_has_a_next_action` derives
  from the registry module namespace; a new `REASON_X` constant without
  remediation copy would be included in `missing` and fail the test.
- P2-MYPY-DECIDE: accepted. `mypy` was removed from `[project.optional-dependencies].dev`
  only; no `[tool.mypy]` config was added, and `CHANGELOG.md` records the
  rationale.

## Verification

- Focused review run: `.venv/bin/python -m pytest
  tests/test_hydrostatics.py::test_analytic_anchor_parabolic_body_volume_and_lcb
  tests/test_generative_jobs_subprocess.py::test_subprocess_manager_cancel_deterministic_with_controlled_runner
  tests/test_generative_jobs_subprocess.py::test_subprocess_manager_cancel_via_flag
  tests/test_generative_jobs_subprocess.py::test_subprocess_manager_resume_after_cancel
  tests/test_stability_fit_registry.py::test_multi_fixture_fit_loads_when_only_second_fixture_clears_chain
  tests/test_stability_fit_registry.py::test_gate_loose_hysteresis_bound
  tests/test_stability_fit_registry.py::test_gate_touching_heel_range_is_intended_pass
  tests/test_stability_fit_registry.py::test_every_reason_has_a_next_action
  tests/test_stability_fit_registry.py::test_fixture_canonical_sha256_pinned_to_literal_digest
  -q` -> 9 passed.
- Full gate: `.venv/bin/python -m pytest -q` -> 1324 passed, 4 skipped in
  522.81s. The 4 skips are exactly the documented OpenFOAM opt-in gates in
  `tests/test_cfd_run_stages.py` and `tests/test_openfoam_v2512_smoke.py`.
- Ruff: `.venv/bin/python -m ruff check kayakgen tests` -> All checks
  passed.
