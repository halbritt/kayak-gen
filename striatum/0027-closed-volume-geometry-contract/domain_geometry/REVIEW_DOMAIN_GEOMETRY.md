author: operator [self-declared: operator-0027-domain]
# Domain/Geometry Review - Workflow 0027 Closed-Volume Geometry Contract

## Verdict Intent

needs_revision

The proposed RFC 0016 boundary is the right direction: it keeps closed-volume geometry distinct from display STL surfaces and from solver case directories. However, the current contract still leaves the central domain decisions open: which body is closed, what surfaces form its boundary, and how bow/stern/sheerline/deck closure is constructed. Those must be decided before implementation, because signed volume, normal orientation, manifold edge counts, waterline semantics, and future solver/stability consumers all depend on the same choices.

## Findings

### D-001 - Closed body identity is still undecided

RFC 0016 requires a named `ClosedVolumeBody` and says it must stand apart from display meshes and solver case directories, but it still leaves the first accepted body open between a hull-plus-deck body and a hull-only body capped at a chosen sheerline (`docs/rfcs/0016-closed-volume-geometry.md:61`, `docs/rfcs/0016-closed-volume-geometry.md:91`). That open question blocks a domain contract because the two options have different physical meanings: hull-plus-deck encloses reserve buoyancy above the waterline, while hull-only capped at waterline/sheerline represents a different integration boundary.

Required action: Record a single initial body policy before implementation. The policy must state whether the accepted body is `hull_plus_deck_closed` or `hull_only_capped`, name all included surfaces, and declare that downstream signed volume and high-angle stability calculations may only consume that named body.

### D-002 - Bow and stern cap semantics are not explicit enough for plumb stems

The current loft still collapses end decay to zero at the exact endpoint (`kayakgen/model/geometry.py:147`) and then forces a tiny local beam floor for section generation (`kayakgen/model/geometry.py:178`). RFC 0004 and tests intentionally preserve open-surface generation at `bow_rake=0.0` rather than exact endpoint freeboard or watertight caps (`tests/test_plumb_bow.py:78`, `tests/test_plumb_bow.py:112`). RFC 0016 correctly calls out bow/stern cap recording, but it does not define the canonical cap shape.

Required action: Define bow and stern cap construction in the closure policy. The policy must say whether caps are vertical planar stem faces, fan caps from the final non-degenerate station, or another deterministic polygon; it must also define whether the exact `x = +/-L/2` station is included, discarded, or replaced for closed-body construction.

### D-003 - Sheerline and deck-join closure needs a geometric rule, not only metadata

The existing `mesh(part)` API emits separate part surfaces with different face winding for hull and deck and no faces joining the two parts (`kayakgen/model/geometry.py:215`, `kayakgen/model/geometry.py:239`). The package writer preserves that separation as `hull.stl` and `deck.stl` (`kayakgen/eval/mesh_package.py:102`, `kayakgen/eval/mesh_package.py:108`). RFC 0016 says the sheerline join must be recorded, but it does not yet say how hull waterline edges and deck sheer edges are welded, bridged, or rejected when beam-waterline and beam-overall differ.

Required action: Add an explicit sheerline/deck-join rule to the RFC before coding. At minimum, define the source curves, whether `beam_wl_m != beam_oa_m` creates topside side panels, the join tolerance, and whether unmatched join vertices are a hard diagnostic failure.

### D-004 - Normal orientation and signed volume are underspecified as acceptance checks

RFC 0016 requires signed volume diagnostics (`docs/rfcs/0016-closed-volume-geometry.md:74`), while RFC 0010's future watertight profile requires outward normals (`kayakgen/eval/mesh_package.py:67`). Current diagnostics count edges and surface area but do not compute oriented volume or verify winding consistency (`kayakgen/eval/mesh_diagnostics.py:111`, `kayakgen/eval/mesh_diagnostics.py:192`). A closed mesh with reversed winding can have zero boundary edges and still yield negative or inconsistent signed volume.

Required action: Define the closed-body orientation convention and signed-volume acceptance rule. The diagnostics should require zero boundary edges, zero nonmanifold edges, positive signed volume for outward normals, and a tolerance for absolute signed-volume magnitude and orientation correction/rejection.

### D-005 - Manifold edge counts must be evaluated on the combined closed body

Current mesh diagnostics are per-part diagnostics over separate hull and deck surfaces (`kayakgen/eval/mesh_package.py:99`, `kayakgen/eval/mesh_package.py:127`). The watertight profile correctly refuses current packages because each part has boundary edges and the package is not a combined closed volume (`kayakgen/eval/mesh_package.py:154`, `kayakgen/eval/mesh_package.py:161`). RFC 0016 needs to carry that same principle forward: part-level zero-boundary checks are not sufficient if the accepted body has multiple joined parts.

Required action: Require diagnostics over both individual `ClosedSurfacePart`s and the assembled `ClosedVolumeBody`. The body-level report must be authoritative for readiness and must include raw and tolerance-welded boundary-edge counts, nonmanifold-edge counts, and part attribution for any failed edge.

### D-006 - Waterline semantics need to be a closed-volume policy field with hard consequences

The mesh package manifest currently records `waterline_z_m = 0.0` as coordinate metadata (`kayakgen/eval/mesh_package.py:24`), while the open wetted-surface profile allows open waterline boundaries and the watertight profile names closed volume as required (`kayakgen/eval/mesh_package.py:55`, `kayakgen/eval/mesh_package.py:67`). RFC 0016 lists waterline as metadata versus cut boundary, but leaves the choice open (`docs/rfcs/0016-closed-volume-geometry.md:71`).

Required action: Decide for the first closed-volume body whether the design waterline is metadata only or a geometric cut boundary. If it is metadata only, closed-body volume includes all enclosed deck/freeboard volume; if it is a cut boundary, the cap plane and intersection tolerance must be part of the closure policy.

### D-007 - Tolerance ownership should move from mesh-package defaults into the closed-volume policy

Current diagnostics use global mesh tolerances (`kayakgen/eval/mesh_diagnostics.py:16`), while RFC 0016 says closure policy records vertex welding, face degeneracy, and signed-volume tolerances (`docs/rfcs/0016-closed-volume-geometry.md:72`). Without body-owned tolerances, two callers can evaluate the same closed body under different implicit rules and report different readiness.

Required action: Make closure tolerances serialized fields on `ClosedVolumeClosurePolicy`, and require diagnostics to echo the exact tolerances used. Include at least vertex welding, degenerate face area, cap/join matching, self-intersection availability/status, and signed-volume tolerance.

### D-008 - Separation from display STL and solver cases is directionally correct and should be preserved

The current package writer deliberately emits display/open-surface STL artifacts and blocks watertight readiness for them (`kayakgen/eval/mesh_package.py:83`, `kayakgen/eval/mesh_package.py:161`). RFC 0016 also says the new body should be an evaluation body, not a solver-specific case directory (`docs/rfcs/0016-closed-volume-geometry.md:61`). This is a sound boundary and should not be weakened by reusing current STL files as the closed source of truth.

Required action: Keep `ClosedVolumeBody` serialization separate from `MeshPackageManifest.surfaces` and CFD job directories. A later mesh package may reference a closed body artifact, but it must not silently reinterpret `hull.stl` plus `deck.stl` as the closed body.

## Required Contract Additions Before Acceptance

1. Name the first supported closed body type and included parts.
2. Define bow and stern cap algorithms, including plumb endpoint handling.
3. Define the sheerline/deck join and `beam_wl_m != beam_oa_m` behavior.
4. Define waterline as metadata or a cut boundary.
5. Define outward normal convention and signed-volume acceptance.
6. Require body-level manifold diagnostics in addition to part diagnostics.
7. Serialize closure tolerances and diagnostic policy.
8. Preserve separation from display STL packages and solver case directories.
