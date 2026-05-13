# Patch Summary: 0039 Plumb-Stem Closure Semantics

## Summary

Implemented the ledger-approved RFC 0028 safe slice. `Hull` now supports
independent `stern_rake` while preserving legacy `bow_rake`-only symmetric
input, the loft selects side-specific rake under the bow-negative/stern-positive
X convention, and generated closed bodies have exact plumb endpoint rings,
deterministic cap winding, positive signed volume, zero body-level boundary
edges, and required self-intersection diagnostics before reporting
`closed_volume`.

Open hull/deck STL generation and mesh packages remain inspection/open-surface
paths and are not promoted to watertight-solid or `cfd_ready`.

## Changed Files

- `CHANGELOG.md`
- `docs/PRD.md`
- `docs/USER_GUIDE.md`
- `docs/rfcs/0004-plumb-bow.md`
- `docs/rfcs/0028-plumb-stem-closure-semantics.md`
- `docs/rfcs/README.md`
- `docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md`
- `docs/workflows/0039-plumb-stem-closure-semantics/workflow.json`
- `kayakgen/eval/generated_closed_body.py`
- `kayakgen/eval/mesh_diagnostics.py`
- `kayakgen/eval/mesh_package.py`
- `kayakgen/model/geometry.py`
- `kayakgen/model/hull.py`
- `kayakgen/ui/desktop.py`
- `kayakgen/ui/gui_params.py`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/state.py`
- `tests/test_cli.py`
- `tests/test_generated_closed_body.py`
- `tests/test_golden.py`
- `tests/test_gui_params.py`
- `tests/test_hull_roundtrip.py`
- `tests/test_mesh_diagnostics.py`
- `tests/test_mesh_package.py`
- `tests/test_plumb_bow.py`
- `tests/test_web.py`

## Findings Addressed

- F-001: updated stale workflow source paths in `SOURCES.md` and
  `workflow.json`.
- F-002: added `Hull.stern_rake` validation and compatibility seeding for
  legacy `bow_rake`-only input.
- F-003: added side-specific rake selection in loft decay/deck scaling.
- F-004/F-005: added generated closed-body construction with exact plumb
  terminal rings, raked apex closure, deterministic bow/stern caps, positive
  signed volume, cap-normal tests, boundary-edge tests, and required
  self-intersection diagnostics.
- F-006/F-009: documented coordinate conventions, legacy `bow_rake` semantics,
  RFC 0028 status, and user-facing open-surface caveats.
- F-007: demoted finite degenerate and finite nonmanifold meshes below
  `stl_surface` and added focused tests.

## Deferred Findings

- F-008 remains deferred: CLI stdout still reports package path/readiness while
  detailed watertight-profile failure reasons live in the manifest.
- No `cfd_ready`, watertight-solid solver handoff, volume mesh generation,
  manufacturing stem thickness, reverse rake, or broader hull-form controls
  were added.

## Sub-Agent Usage

Used five read-only sub-agents with disjoint scopes:

- Bernoulli inspected `Hull` serialization and compatibility surfaces.
- Kuhn inspected geometry/closed-body placement, winding, and test strategy.
- Boyle inspected docs, RFC traceability, source-list, and changelog updates.
- Dewey inspected existing tests and recommended focused verification.
- Nietzsche performed a final read-only diff self-check; its findings led to
  switching generated bodies to the self-intersection-required profile, adding
  `beam_wl_m != beam_oa_m` closure coverage, and aligning `docs/PRD.md`.

No sub-agent called `striatum`, edited files, committed, pushed, completed the
job, or updated root `OPERATOR_REPORT.md`.

## Verification

- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q -o cache_dir=/tmp/kayakgen-pytest-cache-0039 tests/test_generated_closed_body.py tests/test_plumb_bow.py tests/test_hull_roundtrip.py tests/test_mesh_diagnostics.py`
  - Result: 37 passed in 1.01s.
- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q -o cache_dir=/tmp/kayakgen-pytest-cache-0039 tests/test_generated_closed_body.py tests/test_plumb_bow.py tests/test_hull_roundtrip.py tests/test_mesh_diagnostics.py tests/test_mesh_package.py tests/test_cli.py tests/test_gui_params.py tests/test_web.py`
  - Result before self-check fixes: 86 passed in 10.59s.
- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q -o cache_dir=/tmp/kayakgen-pytest-cache-0039 tests/test_generated_closed_body.py`
  - Result after self-check fixes: 6 passed in 6.85s.
- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q -o cache_dir=/tmp/kayakgen-pytest-cache-0039 tests/test_generated_closed_body.py tests/test_plumb_bow.py tests/test_hull_roundtrip.py tests/test_mesh_diagnostics.py tests/test_mesh_package.py tests/test_cli.py tests/test_gui_params.py tests/test_web.py tests/test_golden.py`
  - Result: 98 passed in 17.64s.
- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q -o cache_dir=/tmp/kayakgen-pytest-cache-0039-full`
  - Result: 211 passed in 34.85s.
- `PYTHONDONTWRITEBYTECODE=1 /home/halbritt/git/kayak-gen/.venv/bin/python -m ruff check kayakgen tests`
  - Result: not run; venv has no `ruff` module installed.
