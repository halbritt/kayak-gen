# RFC 0088: Topsides for distribution_v2 hulls

Status: landed optional topsides record
Date: 2026-11-10
Context: RFC 0048 (`distribution_v2`), RFC 0022 (generated closed body),
RFC 0043 (high-angle GZ), RFC 0049/0068 (identity); D074;
`kayakgen/model/distribution_v2.py`, `kayakgen/model/geometry.py`.

## Problem

A `distribution_v2` body joined its deck to its hull on the design
waterline. Every station was widest at the waterline and narrowed
above it, so no v2 hull could gain breadth as it heeled. The owner's
fast-tourer study showed the consequence: at equal load and centre of
gravity a 0.48 m v2 hull had a negative righting arm from about 7
degrees, and matching the calculated righting arm of a scan-reconstructed production kayak at
20 degrees required 0.54-0.56 m of waterline beam. That model reaches
it with a 0.51 m waterline and 0.56 m at the sheer. The design space
could not express the form, so the search penalised narrow waterlines
for a limit of the model.

## Goals

- A v2 hull can carry hull sides above the waterline, wall-sided or
  flared, varying along the length.
- Every surface that consumes the canonical closed body (generated
  closed body, equilibrium hydrostatics, high-angle GZ, section
  exports) sees the same sides without a second code path.
- Existing hulls keep their geometry, serialized bytes, record
  identity and design identity.

## Non-Goals

- No topsides for `lofted` geometry.
- No tumblehome (sheer narrower than the waterline), chine or knuckle
  within the topside strip, or separate deck and hull parts above the
  waterline.
- No coupling of `Hull.beam_oa_m` to the sheer breadth. V2 geometry
  already ignores the scalar beam fields; that is unchanged.
- No physical validation of any GZ value. Claim states are unchanged.

## Proposal

`DistributionV2Spec` gains an optional `topsides: TopsidesSpec | None`.

`TopsidesSpec` has two fields, each a scalar or a
`LongitudinalDistribution`:

- `sheer_beam_ratio` (default 1.0): sheer half-breadth divided by the
  local waterline half-breadth. Range [1, 1.5]. A ratio, not an angle
  or an offset, so the flare shrinks with the local breadth and is
  zero at a pointed end.
- `sheer_height_frac` (default 0.6): sheer height above the design
  waterline divided by the local deck freeboard. Range [0.05, 0.95].

Values are checked at 201 stations when the record is built;
out-of-range, non-finite and unknown fields are refused.

With topsides set, the upper ring at each station runs centreline to
sheer over the deck, then sheer to the waterline edge down the topside
strip. The strip is a quadratic Bezier from the waterline edge to the
sheer. Its control point lies on the hull arc's own tangent at the
waterline, as far along as the sheer breadth or half the sheer height,
whichever is reached first. The strip therefore continues the hull
section without a knuckle on the waterline for every section family,
the sheer is the widest point, and height rises monotonically. (The
first landing used a parabola that left the waterline vertically. Only
`shallow_arch` is vertical there; `round` meets the waterline at about
35-50 degrees, and the result was a visible chine along the waterline.)
A ratio of 1 on a family that is not vertical at the waterline keeps
the knuckle: a wall-sided strip cannot follow an outward tangent. The deck keeps its existing arch
exponent between the sheer and the crown. The ring keeps its point
count and its three anchor points (both waterline edges and the crown),
so meshing and the closed-body builder are unchanged. The lower ring is
untouched, so upright hydrostatics and resistance at the design
waterline do not change.

The strip belongs to the `deck` part. `hull` stays the surface below
the design waterline, which is what wetted-surface and section-area
consumers assume.

`topsides` is omitted from serialized output while unset. A record
written before the field existed therefore serializes to the same
bytes, and `record_hash` / `design_hash` do not move. Setting it
changes both.

`DistributionV2Geometry.sheer_line()` returns `(x, half_breadth, z)`.
The offsets export reports `sheer_Z` at the widest upper-ring point
when that point is wider than the waterline.

## Acceptance Criteria

- Unset: no `topsides` key in serialized output; the pinned v2
  identity, STL payload and golden tests pass unchanged.
- Set: JSON round trip; identity changes; ring point count and anchor
  points preserved; widest point at `ratio * b`, `frac * freeboard`.
- Upright displaced volume, wetted surface, waterplane area and GM0
  are identical with and without topsides.
- Generated closed bodies with a varying flare reach `closed_volume`
  for all six section families.
- Righting arm at 20 and 30 degrees orders no-topsides < wall-sided <
  flared on the same hull and load.
- The strip's direction at the waterline matches the hull arc's within
  2 degrees for all six section families.
- Out-of-range scalars and distributions are refused.
- Tests: `tests/test_v2_topsides.py`.

## Open Questions

- Whether search variables should expose `sheer_beam_ratio` by default
  in class presets. Dotted keys (RFC 0063) already reach it once a
  base hull carries a `topsides` record.

## Implementation Path

- Step 1 — spec record, serializer, geometry, sheer line, offsets
  export, tests, docs. Landed.

## Domain Modeling

`TopsidesSpec` is a value object owned by `DistributionV2Spec`
(`DDD.md § "Adding to the model"`). "Topsides" and "sheer" are added to
`UBIQUITOUS_LANGUAGE.md`.
