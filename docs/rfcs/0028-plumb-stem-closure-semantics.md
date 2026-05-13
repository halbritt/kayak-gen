# RFC 0028: Plumb-Stem Closure Semantics

Status: proposed
Date: 2026-05-13
Context: closes deferred RFC 0004 exact plumb-stem and watertight semantics;
depends on the generated closed-body work from RFCs 0022-0024.

## Problem

RFC 0004 landed the safe near-plumb slice: `bow_rake` preserves fullness close
to the stem and the legacy default remains unchanged. It deliberately deferred
four semantics that now block later geometry, hydrostatics, and CFD work:

1. Whether `bow_rake = 0` means non-zero section area at the exact endpoint or
   only inside the final transition zone.
2. How bow and stern rake should become independent without breaking the
   existing `bow_rake` compatibility field.
3. Which coordinate/sign convention names the bow, stern, forward rake, and
   aft rake unambiguously.
4. Which package owns generated closed hull/deck/body construction and which
   surfaces remain open inspection artifacts.

The current open hull and deck STLs are valid inspection surfaces, but they are
not closed bodies. Exact plumb semantics must not silently promote those
surfaces to watertight solver inputs.

## Goals

- Define exact plumb endpoint behavior for bow and stern stems.
- Add asymmetric rake semantics while preserving `bow_rake` as a compatibility
  alias for symmetric rake.
- Fix coordinate and sign conventions for all stem-related fields.
- Define end-cap polygons and closed-body dependency boundaries.
- Keep legacy open-surface generation and golden geometry stable unless a new
  closed-body path is explicitly requested.

## Non-Goals

- New rocker, flare, tumblehome, reverse-rake, or multi-chine controls.
- Declaring generated bodies CFD-ready. Closed geometry can still fail mesh
  quality, self-intersection, volume, or solver-profile gates.
- Replacing the existing hull/deck inspection STL surfaces.

## Proposal

### 1. Coordinate and sign conventions

The model coordinate system is:

- X increases from bow to stern.
- Bow endpoint is `x = -length_m / 2`.
- Stern endpoint is `x = +length_m / 2`.
- Z increases upward from the design waterline convention already used by the
  geometry layer.
- Port/starboard symmetry remains implicit; Y spans half-beam in section
  generation and mirrored meshes.

Stem rake fields use dimensionless fullness, not geometric angle:

- `bow_rake = 1.0` is the legacy raked taper.
- `bow_rake = 0.0` is exact plumb at the bow.
- `stern_rake = 1.0` is the legacy raked taper.
- `stern_rake = 0.0` is exact plumb at the stern.

Values outside `[0, 1]` are invalid. Reverse rake is out of scope.

### 2. Compatibility field

Keep `Hull.bow_rake` and the legacy `generator.KayakGenerator(..., bow_rake=)`
argument as a symmetric compatibility field:

- If only `bow_rake` is supplied, it seeds both bow and stern rake in the
  package model.
- New code should prefer `bow_rake` plus `stern_rake` on `Hull`.
- If both `bow_rake` and `stern_rake` are supplied, they are independent.
- Serialized hull JSON must include enough metadata for older files that only
  contain `bow_rake` to round-trip without changing geometry.

The field name `bow_rake` is retained even though it historically controlled
both ends. Documentation must call that historical behavior out.

### 3. Exact plumb endpoint semantics

For `rake = 0.0`, the generated *closed-body* path must not collapse the final
station to a zero-area point. Instead it creates a terminal station at the
endpoint whose below-water and above-water boundaries are the limiting section
shape after the plumb transition. The terminal station is then capped by a
single planar polygon fan per end, with stable vertex ordering and outward
normals.

For `0.0 < rake <= 1.0`, the open inspection surfaces may continue to use the
existing blended decay and zero-area terminal point. The closed-body path may
still add a cap at the collapsed endpoint, but exact non-zero endpoint area is
required only for `rake = 0.0`.

The cap station must be deterministic:

- No duplicate coincident ring vertices except the intentional center/fan
  vertex if the implementation uses one.
- Positive signed body volume with outward normals.
- No body-level boundary edges after hull, deck, and caps are joined.
- Bow and stern caps use mirrored orientation under the X convention above.

### 4. Dependency boundaries

Closed-body construction lives below presentation surfaces and above raw hull
parameter validation:

- `kayakgen.model.Hull` owns validated rake fields and compatibility behavior.
- `kayakgen.geometry` owns station/ring construction and open hull/deck meshes.
- A generated closed-body builder owns joining hull, deck, bow cap, and stern
  cap into a single body artifact.
- Mesh diagnostics own watertight, nonmanifold, orientation, volume, and
  self-intersection classification.
- CLI, desktop, web, and CFD code consume readiness metadata; they do not infer
  watertightness from `bow_rake = 0`.

Open STL generation remains an inspection/export path. Closed-body artifacts are
requested through an explicit profile or command surface and are never implied
by changing rake sliders.

## Acceptance Criteria

- `Hull` or its accepted successor can represent independent bow and stern rake
  while old symmetric `bow_rake` inputs preserve legacy behavior.
- Documentation and tests pin X-coordinate and orientation conventions for bow,
  stern, cap winding, and signed volume.
- With `bow_rake = 0.0`, the generated closed-body path has non-zero terminal
  bow section area at `x = -L/2`.
- With `stern_rake = 0.0`, the generated closed-body path has non-zero terminal
  stern section area at `x = +L/2`.
- Mixed cases such as plumb bow plus raked stern are tested and produce
  asymmetric geometry without changing the default hull.
- Open hull/deck STL exports continue to be labeled as open inspection surfaces
  unless a closed-body command/profile is explicitly selected.
- Mesh diagnostics, not rake settings, decide whether an artifact can claim
  closed-volume or watertight-solid readiness.

## Open Questions

- Should exact plumb caps be planar in Y/Z at the endpoint or should a very
  short finite stem thickness be introduced for manufacturing-oriented exports?
  Lean: planar caps for this RFC; thickness belongs to a production-export RFC.
- Should non-zero endpoint area apply to intermediate rake values below a
  threshold such as `rake < 0.05`? Lean: no; exact endpoint semantics should be
  tied to the exact value `0.0` for deterministic tests.

## Implementation Path

1. Add independent `stern_rake` validation and compatibility round-trip tests.
2. Extract station/ring metadata needed by a closed-body builder.
3. Add deterministic cap construction for exact plumb bow and stern cases.
4. Extend diagnostics/golden tests for cap winding, signed volume, boundary
   edges, and mixed bow/stern rake.
5. Update CLI/user-guide wording so open surfaces and generated closed bodies
   remain visibly distinct.
