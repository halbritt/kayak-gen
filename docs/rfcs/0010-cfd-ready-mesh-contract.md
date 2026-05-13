# RFC 0010: CFD-Ready Mesh Contract

Status: landed-package-profile
Date: 2026-05-13
Context: builds on RFC 0004 plumb-bow ambiguity, RFC 0007 `HullGeometry`, RFC
0008 job stubs, and the reserved `kayakgen.eval.cfd` boundary.

Status note (workflow 0015, 2026-05-13): mesh diagnostics, deterministic mesh
package writing, and the first open wetted-surface solver profile have landed.
Current packages are open-surface CFD candidates, not watertight `cfd_ready`
solids. Solver dispatch, volume meshing, and watertight solid readiness remain
future work.

## Problem

The project can export STL surfaces, but "CFD-ready" is not defined. RFC 0008
reserves heavy-CFD jobs, and RFC 0005 is only an analytical fast filter. Before
an external solver can be wired in, the project needs a mesh contract: units,
coordinate system, part boundaries, waterline semantics, manifold expectations,
quality checks, metadata, and failure modes.

The current hull and deck meshes are useful display/export surfaces. They should
not be silently promoted to a watertight CFD artifact.

## Human Decisions Recorded 2026-05-13

- Longitudinal coordinates are stern-positive: `+x` points toward the stern,
  `-x` points toward the bow. In left-to-right side views, the bow is expected
  on the left.
- The first CFD mesh target is an open wetted-surface resistance profile. A
  complete deck or capped hull/deck solid is not required for that profile.
- Watertight solid readiness remains a separate future solver profile, not the
  global meaning of `cfd_ready`.

## Goals

- Define the minimum mesh and metadata contract required by future CFD workers.
- Add validation that classifies current mesh output honestly.
- Produce deterministic mesh-package artifacts from a `Hull`.
- Keep current STL export behavior intact.
- Surface open-boundary and plumb-stem/end-cap ambiguity as explicit readiness
  blockers instead of hiding them.

## Non-Goals

- Integrating OpenFOAM, SU2, panel solvers, RANS, or meshing tools.
- Producing volume meshes.
- Changing geometry goldens.
- Solving exact plumb-stem/end-cap semantics from RFC 0004.
- Guaranteeing a watertight hull-plus-deck solid in this RFC.

## Proposal

Add a mesh diagnostics/readiness layer over existing `HullGeometry.mesh()`:

- `MeshDiagnostics`
- `MeshPackageManifest`
- `MeshReadinessLevel`
- `MeshSolverProfile`

Readiness levels:

- `display`: enough for GUI/web rendering.
- `stl_surface`: finite, nondegenerate triangle surface that can be exported.
- `cfd_surface_candidate`: has stable metadata and quality reports but may
  still be open or solver-dependent.
- `cfd_ready`: passes the selected solver profile's strict contract.

`cfd_ready` may only be emitted when a named `MeshSolverProfile` is attached to
the report. The default diagnostics profile cannot promote current open
hull/deck surfaces beyond `stl_surface`.

`MeshSolverProfile` fields are `profile_name`, `requires_watertight`,
`accepted_parts`, `normal_orientation`, `waterline_boundary_policy`,
`duplicate_vertex_tolerance_m`, `degenerate_area_tolerance_m2`, and
`max_nonmanifold_edges`.

Initial checks:

- finite vertex coordinates;
- zero-area or near-zero-area triangle count;
- edge incidence counts;
- tolerance-welded edge incidence counts;
- boundary-edge count;
- tolerance-welded boundary-edge count;
- nonmanifold-edge count;
- tolerance-welded nonmanifold-edge count;
- bounding box sanity against hull dimensions;
- surface area;
- part identity;
- waterline metadata.

Example manifest:

```json
{
  "schema_version": "1",
  "hull_hash": "...",
  "units": "m",
  "coordinate_system": {
    "x": "longitudinal, stern positive, bow negative, spans -L/2 to +L/2",
    "y": "port/starboard",
    "z": "up positive",
    "waterline_z_m": 0.0
  },
  "readiness": "stl_surface",
  "parts": ["hull", "deck"],
  "quality_reports": ["quality.hull.json", "quality.deck.json"]
}
```

CLI:

```text
kayakgen mesh-check hull.json --out quality.json
kayakgen mesh-package hull.json --out mesh-package/
```

## Acceptance Criteria

- `mesh-check` produces diagnostics for any valid `Hull`.
- The default hull passes finite-coordinate, bounding-box, and
  nondegenerate-face checks.
- The default hull is not falsely labeled `cfd_ready` while open boundaries
  remain.
- Reports include vertex count, face count, boundary edges, nonmanifold edges,
  degenerate faces, nonfinite vertices, surface area, and bounding box.
- `mesh-package` writes a manifest, hull JSON, quality reports, and STL
  surfaces.
- Tests cover the default hull, deck mesh, and synthetic degenerate/nonfinite
  mesh fixtures.

## Open Questions

- Which external solver profile lands first?
- What additional checks are needed for a future watertight solid profile?

## Implementation Path

- Step 1 - Add mesh diagnostics models, solver profile schema, default
  tolerances, and generic triangle checks.
- Step 2 - Add `kayakgen mesh-check`.
- Step 3 - Add mesh package manifest writing.
- Step 4 - Add `kayakgen mesh-package`.
- Step 5 - Update CFD stub wording to require a mesh package before future
  solver dispatch.

## Domain Modeling

The mesh contract is a boundary clarification between the `HullGeometry` domain
model and future external solver adapters. It does not change the `Hull`
aggregate.
