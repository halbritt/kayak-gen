# RFC 0069: Geometry export capabilities and complete bundle publication

Status: landed shared geometry exports + staged builder bundles
Date: 2026-11-07
Context: KAYGEN-9 / W4 of the system architecture implementation plan;
RFCs 0048, 0051 and the existing open-surface inspection contract.

## Problem

`generate` asks geometry for a legacy `generate_stl` convenience method,
which Geometry V2 does not implement. Builder exports reject any geometry
that is not the lofted implementation even though both implementations
already provide the required sections and curves. A failed builder retry
can overwrite some files while leaving an older completion manifest.

## Goals

- Export both admitted geometry kinds through existing mesh/section data.
- Preserve lofted triangle payloads, names, coordinates and units.
- Publish a builder manifest only with its complete, matching artifact set.
- Refuse missing extras, unsupported section capability and invalid station
  counts before creating the output tree.

## Non-Goals

Geometry math, physical-identity migration, structural adequacy, mold
fairness and new file formats are outside this change. Exported STL files
remain open inspection surfaces, not closed bodies or CFD readiness evidence.

## Proposal

The STL writer serializes `HullGeometry.mesh()` arrays into the same
numpy-stl triangle format used by the legacy convenience method. It stages
one file beside its destination before replacement so serialization failure
preserves a prior artifact. Each file keeps metre coordinates.

Builder writers declare their existing closed-section and curve needs as a
structural `SectionExportGeometry` capability. Both lofted and distribution_v2
satisfy it without another geometry path. CSV coordinates remain metres;
Mold spacing and scale-bar placement include actual sampled section width/depth
when those exceed legacy scalar dimensions. DXF coordinates and SVG plots remain
millimetres, with the DXF station plane
mapping `(Y, Z)` and station X in the layer name. Source metadata continues
to bind the full Hull record hash, independently of physical hash migration.

`write_build_export` validates the station count, geometry capability and
DXF dependency first. Its destination must be absent or empty and separate from the current
working directory (which cannot be replaced without stranding its users). It writes all
seven artifacts and their manifest in a temporary sibling directory, then
publishes that complete directory with one rename. A nonempty destination
is refused without changing it; users select a new directory for another
export. This also prevents two publishers from replacing the same nonempty
completed bundle. It is not a power-loss/fsync guarantee.

## Acceptance Criteria

- Native `generate` and `build-export` CLI paths succeed for every admitted
  v2 section family; readback retains mesh coordinates, section geometry,
  units, source record identity and per-artifact hashes.
- Lofted STL triangle payloads match the pinned golden hashes.
- CSV offsets and DXF sections agree after millimetre/metre conversion;
  DXF mold contours remain closed.
- Missing dependency/capability or invalid station count creates no output
  directory. Mid-write failure publishes no bundle and removes staging.
- An existing completed bundle is refused and remains byte-for-byte intact.
  A failed STL serialization leaves its prior destination intact.
- Full pytest with the documented skip pin and Ruff pass before integration.

## Open Questions

None for the supported inspection formats. New format capabilities require
separate consumers and acceptance evidence.

## Implementation Path

1. Reproduce v2 CLI failures with mesh and section readback tests.
2. Serialize the common mesh capability and consume existing section data.
3. Add staged directory publication, preflight/refusal and failure tests.
4. Update public usage and preserve the lofted golden checks.

## Domain Modeling

This is a boundary clarification over the existing Hull aggregate, consistent
with `DDD.md`'s model extension convention. `BuildExportSpec` remains the
existing invocation value object; no aggregate or event lifecycle is added.
