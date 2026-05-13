# REVIEW_OPS_TEST - workflow 0033 generated closed-body construction

Verdict intent: accept_with_findings

Role: `reviewer_ops_test`  
Lane/model: `codex / Codex GPT-5.5`  
Artifact path: `striatum/0033-generated-closed-body-construction/ops/REVIEW_OPS_TEST.md`

## Sub-Agent Help Used

This review used four read-only explorer sub-agents with disjoint scopes: implementation/display-STL boundaries, deterministic test coverage, CLI/JSON serialization, and verification/regression commands. No sub-agent was asked to mutate project code, call `striatum`, publish artifacts, or update `OPERATOR_REPORT.md`.

## Summary

Existing regression coverage passes, and the current code does not promote generated or synthetic closed bodies to `cfd_ready`. The workflow can proceed to findings consolidation, but the ledger should carry the findings below into implementation because RFC 0022 generated closed-body construction is not present yet and the workflow source/write-scope metadata is stale.

## Findings

### F1 - High - Workflow source and write-scope paths are stale

`docs/workflows/0033-generated-closed-body-construction/SOURCES.md:10`, `:11`, and `:14` list `kayakgen/geometry/lofted_hull.py`, `kayakgen/domain/hull.py`, and `tests/test_geometry.py`, but those files do not exist in this checkout. The workflow also marks those paths as required context at `docs/workflows/0033-generated-closed-body-construction/workflow.json:49`, `:50`, and `:53`.

The live equivalents are `kayakgen/model/geometry.py`, `kayakgen/model/hull.py`, and `tests/test_geometry_lofted.py`. The implementation write scope allows `kayakgen/domain/` and `kayakgen/geometry/` but not `kayakgen/model/` at `docs/workflows/0033-generated-closed-body-construction/workflow.json:176-183`, which risks forcing implementation into duplicate packages instead of the current model layer.

### F2 - High - RFC 0022 generated closed-body construction is not implemented yet

RFC 0022 requires deterministic `generated_hull_plus_deck_closed_body_v1` construction and acceptance tests for caps, plumb/default rake, `beam_wl_m != beam_oa_m`, waterline metadata, outward normals, positive volume, display-STL separation, and no `cfd_ready` promotion at `docs/rfcs/0022-generated-closed-body-construction.md:139-152`.

Current production code remains explicit-synthetic only: `ClosedVolumeBodyType` is limited to `explicit_synthetic_triangle_mesh` in `kayakgen/eval/closed_volume.py:16-17`, policy metadata is synthetic/not-applicable in `kayakgen/eval/closed_volume.py:62-76`, and `diagnose_closed_volume_body` rejects other body types in `kayakgen/eval/closed_volume.py:228-234`. This is acceptable for a pre-implementation review, but it is the main ledger item for workflow 0033.

### F3 - Medium - Generated-body fixture coverage is missing

`tests/test_closed_volume.py:70-346` covers synthetic tetrahedra and self-intersection fixtures, while `tests/test_mesh_package.py:63-86` verifies current mesh packages stay below `cfd_ready`. There are no tests yet for a generated hull-plus-deck body, endpoint caps, default and non-default `bow_rake`, `beam_wl_m != beam_oa_m` sheer joins, serialized generated-body policy, or display-STL separation for the new builder. Those should be required before final gate.

### F4 - Medium - Synthetic diagnostic coverage has small gaps

The closed-volume code reports nonfinite vertices/faces, out-of-range indices, degenerate faces, boundary edges, nonmanifold edges, signed volume, and self-intersection status in `kayakgen/eval/closed_volume.py:1074-1099`. Tests cover open, nonmanifold, reversed orientation, out-of-range indices, and self-intersection cases, but do not directly cover nonfinite closed-volume input or degenerate-face rejection. Tolerance echo coverage is also thin: tests assert one default tolerance is positive at `tests/test_closed_volume.py:86`, but custom tolerance preservation is not asserted after serialization.

## Positive Checks

Display STL remains separate from closed-volume semantics. `LoftedHullGeometry.mesh()` returns one requested part at a time in `kayakgen/model/geometry.py:215-244`, `generate_stl()` writes that selected part in `kayakgen/model/geometry.py:299-306`, and mesh packages serialize separate `hull.stl` and `deck.stl` surfaces in `kayakgen/eval/mesh_package.py:99-123`.

No `cfd_ready` overclaim was found. `ClosedVolumeDiagnostics.cfd_ready` is `Literal[False]` at `kayakgen/eval/closed_volume.py:193`, synthetic dispatch evidence is rejected in `kayakgen/eval/closed_volume.py:307-325`, and watertight-profile mesh packages remain `stl_surface` with open-surface warnings in `kayakgen/eval/mesh_package.py:154-169`.

## Verification

- `.venv/bin/python -m pytest tests/test_closed_volume.py tests/test_geometry_lofted.py tests/test_mesh_package.py tests/test_mesh_diagnostics.py tests/test_cli.py tests/test_cfd_jobs.py -q` -> `59 passed`
- `.venv/bin/python -m pytest -q` -> `192 passed`
- `git diff --stat` -> no tracked diff
- `git status --short` -> only existing untracked `striatum/0033...`, `0037...`, `0038...`, `0039...`, `0040...`, and `0041...` directories