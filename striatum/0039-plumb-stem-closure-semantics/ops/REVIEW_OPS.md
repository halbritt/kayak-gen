# Review Ops: 0039 Plumb-Stem Closure Semantics

Verdict intent: accept_with_findings

## Scope

This is the `reviewer_ops` artifact for workflow `0039-plumb-stem-closure-semantics`. I reviewed serialization compatibility, CLI/user-guide wording, mesh diagnostics, readiness metadata, and tests that should prevent open STL surfaces from being mislabeled as watertight solids.

No `striatum` command was called. No project code was mutated. `OPERATOR_REPORT.md` was not updated.

## Sub-Agent Help Used

I spawned four read-only sub-agents with disjoint scopes:

- Ramanujan: serialization compatibility and readiness metadata.
- Bohr: CLI/user-guide wording and readiness claims.
- Epicurus: loft behavior and mesh diagnostics.
- Hooke: focused pytest verification and coverage gaps.

I also performed direct read-only inspection and verification in the main session.

## Sources Reviewed

- `AGENTS.md`, followed by the workflow sources, role, and prompt files.
- `docs/rfcs/0004-plumb-bow.md`
- `docs/rfcs/0028-plumb-stem-closure-semantics.md`
- `docs/USER_GUIDE.md`
- `kayakgen/model/hull.py`
- `kayakgen/model/geometry.py`
- `kayakgen/eval/mesh_diagnostics.py`
- `kayakgen/eval/mesh_package.py`
- Relevant tests under `tests/`

The workflow `SOURCES.md` lists two stale implementation paths: `kayakgen/geometry/loft.py` and `kayakgen/mesh/diagnostics.py` at `docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md:8-9`. The active code is currently `kayakgen/model/geometry.py` and `kayakgen/eval/mesh_diagnostics.py`.

## Findings

### OPS-001: Workflow source list points reviewers at stale code paths

`SOURCES.md` names nonexistent or obsolete paths for geometry and diagnostics. Reviewers following it literally can miss the active loft and readiness code.

Required action: update `docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md` to reference `kayakgen/model/geometry.py` and `kayakgen/eval/mesh_diagnostics.py`.

### OPS-002: `stern_rake` serialization is not implemented yet

RFC 0028 requires independent bow/stern rake while preserving legacy `bow_rake` compatibility (`docs/rfcs/0028-plumb-stem-closure-semantics.md:67-80`, `:124-125`). Current `Hull` has only `bow_rake` and forbids extra fields (`kayakgen/model/hull.py:27`, `:43`), so JSON containing `stern_rake` is rejected by `load_hull()`.

Required action: add compatibility-preserving `stern_rake` validation and round-trip tests. Legacy JSON with only `bow_rake` must seed both ends without changing geometry.

### OPS-003: Mixed bow/stern rake is not represented in geometry

The loft uses one symmetric scalar through `self.hull.bow_rake` and `abs(x)`-based decay (`kayakgen/model/geometry.py:131-164`, `:246-279`). RFC 0028 requires mixed cases such as plumb bow plus raked stern (`docs/rfcs/0028-plumb-stem-closure-semantics.md:132-133`).

Required action: implement side-specific rake selection under the documented X convention, and add tests for default, symmetric legacy, and mixed asymmetric cases.

### OPS-004: Exact endpoint/cap semantics are still untested

RFC 0028 requires non-zero terminal closed-body sections at `x = -L/2` and `x = +L/2` for exact plumb ends (`docs/rfcs/0028-plumb-stem-closure-semantics.md:82-103`, `:128-131`). Current open loft endpoints still collapse to zero (`kayakgen/model/geometry.py:122-149`) and `mesh()` builds open strips without caps (`kayakgen/model/geometry.py:215-244`). The existing “at end” test samples `-0.45 * L`, not the endpoint (`tests/test_plumb_bow.py:55-61`).

Required action: add closed-body builder tests for bow cap, stern cap, cap winding, signed volume, zero body-level boundary edges, and mixed-rake geometry. Rename or clarify the existing near-end test so it does not imply exact endpoint coverage.

### OPS-005: User-guide rake wording is incomplete, but readiness caveats are mostly correct

The guide lists `bow_rake` only (`docs/USER_GUIDE.md:52-55`). It does not call out bow `x = -L/2`, stern `x = +L/2`, `stern_rake`, or the historical fact that `bow_rake` controlled both ends. However, it correctly keeps generated mesh packages below watertight/CFD-ready claims (`docs/USER_GUIDE.md:194-198`, `:240-242`, `:342-347`).

Required action: update the user guide with the coordinate convention, `stern_rake`, and the legacy symmetric meaning of `bow_rake`. Preserve the existing open-surface and non-`cfd_ready` caveats.

### OPS-006: Mesh diagnostics still overstate finite bad meshes as `stl_surface`

RFC 0010 defines `stl_surface` as finite, nondegenerate triangle surface (`docs/rfcs/0010-cfd-ready-mesh-contract.md:67-73`). Current `_readiness()` records degenerate or non-manifold reasons but still returns `stl_surface` unless nonfinite values exist (`kayakgen/eval/mesh_diagnostics.py:250-267`). Existing tests only prove invalidity when degeneracy is combined with nonfinite vertices.

Required action: add finite degenerate-only and finite nonmanifold-only tests, then either demote those cases below `stl_surface` or document the intentionally weaker current readiness level.

### OPS-007: CLI watertight-profile failure details are only in the manifest

`kayakgen mesh-package --solver-profile watertight-solid` correctly keeps current packages at `stl_surface`, and tests assert the manifest warning for separate open surfaces (`tests/test_cli.py:151-173`). CLI stdout prints only the manifest path and readiness level (`kayakgen/cli/main.py:129`), so users must inspect JSON for why the watertight profile did not pass.

Required action: consider echoing concise warning lines for non-ready watertight profiles. This is not a blocker because the manifest and tests already preserve the readiness gate.

## Positive Checks

I found no current path that labels generated open hull/deck STL surfaces as watertight or `cfd_ready`. Default diagnostics report `stl_surface`; default mesh packages report `cfd_surface_candidate`; `watertight-solid` packages stay at `stl_surface` with explicit warnings; plumb `bow_rake=0.0` does not promote readiness.

## Verification

Local environment checks:

- `pytest` was not on `PATH`.
- `python` was not on `PATH`.
- `python3 -m pytest` failed because system Python has no `pytest`.
- `.venv/bin/python -m pytest -q tests/test_plumb_bow.py tests/test_mesh_diagnostics.py tests/test_mesh_package.py tests/test_hull_roundtrip.py -o cache_dir=/tmp/kayakgen-pytest-cache-0039` passed: 29 passed in 1.24s.

Additional direct smoke checks showed:

- `kayakgen mesh-check` default hull readiness: `stl_surface`.
- Default `mesh-package` readiness: `cfd_surface_candidate`, with boundary-edge/open-volume warnings.
- `mesh-package --solver-profile watertight-solid` readiness: `stl_surface`, with closed combined hull/deck and separate open-surface warnings.
- `Hull(bow_rake=0.0)` open diagnostics remained `stl_surface`, not closed or watertight.

Hooke also reported a broader focused subset passing: 38 passed in 2.29s.

## Recommendation

The workflow can proceed with recorded findings. The current open-surface readiness boundaries are conservative enough to avoid a false watertight-solid claim, but implementation must add `stern_rake` compatibility, exact endpoint/cap tests, updated user-facing wording, and stronger readiness regression tests before RFC 0028 can be considered landed.