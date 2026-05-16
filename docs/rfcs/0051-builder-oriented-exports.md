# RFC 0051: Builder-Oriented Exports

Status: proposed
Date: 2026-05-16
Context: Phase 8 item 2 of
`ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`. Today's hull
exports stop at STL. STL is fine for digital previews and CFD, but it
is not the right format for someone cutting plywood molds or
plotting offsets on a building jig.

## Problem

Builders need plan-view section curves, an offsets table, the sheer
curve, the waterline curve, the keel curve, and a per-station mold
DXF or SVG. A 3D STL is several layers downstream from those needs.
Today the operator must export the STL, open it in CAD, and reverse
the section curves by intersecting planes with the mesh — work
kayakgen can do directly from the lofted geometry.

## Goals

- Land a new CLI subcommand or `kayakgen generate` flag that produces
  builder-oriented artifacts alongside (not instead of) STL.
- Use industry-standard formats: DXF for vector mold geometry,
  CSV for the offsets table, SVG for plotted curves.
- Make every output deterministic and reproducible (same hull →
  byte-identical artifact, modulo non-determinism in the underlying
  CAD libraries).

## Non-Goals

- No new geometry model. RFC 0048's Geometry V2 is a separate
  proposal; this RFC consumes whatever `HullGeometry` produces.
- No structural / fairness analysis of the curves. The operator
  decides whether the mold is buildable.
- No automatic registration / nesting of plates on a sheet. That is
  CAD/CAM work, out of scope.
- No 3D printing support (today's STL already covers that case).

## Proposal

A new `kayakgen build-export <hull.json> --out <dir>` subcommand
writes:

- `offsets.csv`: per-station X, half-breadth (Y), keel-line Z,
  sheer Z, and (optional) deck-centreline Z. Columns are explicit;
  units are metres.
- `sections.dxf`: one DXF entity per station; sections are polylines
  in the YZ plane, with X annotated as a layer or attribute.
- `sheer.svg`, `keel.svg`, `waterline.svg`, `deck_centreline.svg`:
  plan/profile/elevation curves as SVG (mm grid; configurable scale).
- `station_molds.dxf`: one DXF sheet per station with the mold
  cross-section, registration marks, and a labeled scale bar.

Each artifact carries a header comment with the hull SHA-256 and the
kayakgen version pin (per RFC 0049 identity vocabulary).

## Acceptance Criteria

- `kayakgen build-export default.json --out build/` produces all six
  artifact types and writes a `manifest.json` enumerating them with
  SHA-256.
- The offsets table agrees with the section data at each station
  within 1 mm.
- The DXF and SVG artifacts open in at least one mainstream CAD tool
  (regression-tested by re-parsing the DXF with `ezdxf` and the SVG
  with `xml.etree.ElementTree`).
- The output is deterministic across two invocations (modulo
  per-file timestamps stripped from the header).
- No regression in `kayakgen generate`, `kayakgen evaluate`, or any
  other existing surface.

## Open Questions

- Library choice: `ezdxf` (BSD, well-maintained) for DXF; pure-Python
  SVG (no library) for SVG. Both are pure-Python; no compiled-binary
  deps. Add as optional extras under a new `builder` extras group?
- Scale: should the default be 1:1 in mm, or operator-supplied via a
  flag? Default 1:1; flag for plot-sheet sizing.
- Should `kayakgen generate` gain a `--build-export` flag instead of
  a separate subcommand? Pros: one entry point. Cons: muddles the
  generate API. Separate subcommand is cleaner.

## Implementation Path

1. Add `ezdxf` as an optional dep under `kayakgen[builder]` extras.
2. Land `kayakgen/services/build_export.py` with focused writers per
   artifact type.
3. Add the `kayakgen build-export` Typer subcommand.
4. Land tests that re-parse each artifact and assert structural
   correctness (no rendering-pixel comparison).
5. Update `docs/USER_GUIDE.md`.

## Domain Modeling

`build_export` is a service over the existing Hull aggregate. It adds
no new aggregate root, no value object beyond a small `BuildExportSpec`
options record, and no new domain event. The new artifact files are
durable per the existing artifact catalogue in `docs/SPEC.md`.
