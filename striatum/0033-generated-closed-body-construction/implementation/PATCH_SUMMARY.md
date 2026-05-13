# Patch Summary - workflow 0033 generated closed-body construction

## Findings Addressed

- L1: Repaired workflow-local source metadata and implementation write-scope
  metadata to point at the live `kayakgen/model/` paths and
  `tests/test_geometry_lofted.py`.
- L2-L5: Added the RFC 0022 `generated_hull_plus_deck_closed_body_v1`
  profile, generated body type, serialized cap/join/waterline/tolerance
  policy, source hull hash, deterministic builder from `Hull`, body-level
  diagnostics, RFC 0021 self-intersection gating, positive signed-volume
  orientation, and kept `cfd_ready` hard false.
- L6: Added generated-body acceptance coverage for deterministic construction,
  default and plumb `bow_rake`, `beam_wl_m != beam_oa_m` sheer/topside joins,
  waterline metadata without cutting the body, outward normals, display-STL
  separation, and dispatch rejection.
- L7: Added synthetic diagnostic hardening coverage for nonfinite vertices,
  degenerate faces, and custom tolerance JSON round-trip.

## Changed Files

- `CHANGELOG.md`
- `docs/workflows/0033-generated-closed-body-construction/SOURCES.md`
- `docs/workflows/0033-generated-closed-body-construction/workflow.json`
- `kayakgen/eval/closed_volume.py`
- `tests/test_cfd_jobs.py`
- `tests/test_closed_volume.py`
- `tests/test_generated_closed_body.py`
- `striatum/0033-generated-closed-body-construction/implementation/PATCH_SUMMARY.md`

## Tests Run

- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest tests/test_closed_volume.py -q`
  -> 15 passed.
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest tests/test_generated_closed_body.py tests/test_closed_volume.py -q`
  -> 24 passed.
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest tests/test_closed_volume.py tests/test_generated_closed_body.py tests/test_cfd_jobs.py tests/test_mesh_package.py -q`
  -> 44 passed.
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest tests/test_closed_volume.py tests/test_generated_closed_body.py tests/test_geometry_lofted.py tests/test_mesh_package.py tests/test_mesh_diagnostics.py tests/test_cli.py tests/test_cfd_jobs.py -q`
  -> 72 passed.
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m pytest -q`
  -> 205 passed.
- `git diff --check` -> clean.
- `/home/halbritt/git/kayak-gen/.venv/bin/python -m json.tool docs/workflows/0033-generated-closed-body-construction/workflow.json >/dev/null`
  -> passed.

Ruff was not run because `/home/halbritt/git/kayak-gen/.venv/bin/python -m ruff
check ...` failed with `No module named ruff`.

## Deferred Findings

- Solver-specific surface meshing, volume meshing, and
  `watertight_solid_resistance_v1` handoff remain deferred.
- No generated closed-volume body is promoted to `cfd_ready`; CFD dispatch
  still rejects generated closed-volume diagnostics as solver evidence.
- High-angle `GZ`, secondary-stability physics, geometry repair/healing,
  cockpit/opening modeling, real CFD adapters, and calibrated drag remain
  outside this workflow.

## Sub-Agent Help Used

- Meitner performed read-only geometry-construction analysis and recommended a
  single assembled part with endpoint caps, topside/sheerline strips, and
  positive signed-volume orientation.
- Sartre performed read-only diagnostics/serialization and CFD-boundary
  analysis, including no-`cfd_ready` and dispatch-rejection assertions.
- Plato drafted tests in `tests/test_closed_volume.py` and
  `tests/test_generated_closed_body.py`; final integration adjusted them to
  match the single assembled-part implementation.
- Ohm repaired workflow-local metadata in `SOURCES.md` and `workflow.json`.

No sub-agent called `striatum`, committed, pushed, or updated an operator
report.
