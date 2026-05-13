# RFC 0004: Plumb Bow Support

Status: partial
Date: 2026-05-09
Context: generator.py, gui.py; follows RFC 0003

Status note (workflow 0010, 2026-05-12): partially landed. The `bow_rake`
parameter and blended end decay exist, but the exact-stem non-zero-area and
watertight-STL acceptance wording remains unresolved because the current hull
and deck meshes are separate open surfaces. Treat exact plumb-stem/end-cap
semantics as a follow-up design decision.

Status note (workflow 0019, 2026-05-13): still partial. The safe slice is
landed in the package model/geometry path: `Hull.bow_rake` exists, default
`bow_rake = 1.0` preserves legacy golden geometry, and non-default rake
drives near-plumb inboard fullness through `LoftedHullGeometry._end_decay`.
Tests cover the near-stem positive-section behavior inside the plumb
transition zone, monotonic displaced-volume changes, waterplane shape, and
STL generation. The legacy `generator.KayakGenerator` shim accepts `bow_rake`
and `beam_wl`, and the deck centerline now uses the same raked/plumb blend for
non-default rake. Focused tests cover `Cp` and `center_box_ratio` interactions
with non-default rake. Exact non-zero area at `x = -L/2`, explicit end-cap
polygons, closed/watertight hull-plus-deck solid readiness, asymmetric bow/stern
rake, and manual visual confirmation of the sheer-plan annotation remain
deferred.

Status note (workflow 0039, 2026-05-13): RFC 0028 owns the deferred exact
plumb-stem/end-cap semantics, independent `stern_rake`, bow/stern coordinate
convention, and closed-body readiness wording. RFC 0004 remains the historical
near-plumb open-surface safe slice and the origin of the legacy symmetric
`bow_rake` compatibility behavior.

## Problem

The current hull generator always produces a raked bow and stern: both keel
depth and deck height taper smoothly to zero at x = ±L/2 via
`decay = sqrt(area_fraction(x))`. This is appropriate for a traditional
Greenland-style kayak with a fine, swept entry, but it cannot represent the
plumb (near-vertical) bow used in modern sea kayaks, surf skis, and many
whitewater designs.

A plumb bow has three defining characteristics that are currently impossible
to model:

1. **Vertical stem in profile.** The bow face is nearly perpendicular to the
   waterline. The keel reaches its full draft almost all the way to the
   stem; there is no long, gentle rocker curve running up to the bow.
2. **Maintained freeboard at the bow.** The deck at the stem does not taper
   to zero; there is still meaningful bow height (often 60–80% of midship
   deck height).
3. **Sharper entry waterline.** Because the bow volume is redistributed
   inboard rather than swept forward, the waterplane entry is finer at a
   given Cp.

## Goals

- Add a continuous `bow_rake` parameter (0.0 = fully plumb, 1.0 = current
  raked behaviour).
- In RFC 0004, `bow_rake` is a symmetric compatibility control for both bow and
  stern. RFC 0028 owns the later independent `stern_rake` split.
- The 3D mesh, STL export, cross-section view, and sheer plan all update
  correctly for any `bow_rake` value.
- Stations near `x = -L/2` inside the plumb transition zone show non-zero
  cross-section area when `bow_rake < 0.5`. Exact endpoint non-zero area is
  deferred until explicit end-cap semantics are designed.

## Non-Goals

- Asymmetric bow/stern treatment (future RFC).
- Flared or tumblehome bow topside geometry (orthogonal to bow rake).
- Overhang (reverse rake / negative bow angle).

## Proposal

### 1. Generator changes (`generator.py`)

#### New parameter

Add `bow_rake: float = 1.0` to `KayakGenerator.__init__`. Store as
`self.bow_rake`.

#### Modified decay function

Currently the end-taper is purely:
```python
decay = sqrt(area_fraction(x))
```

Replace with a blended decay that preserves volume near the ends when
`bow_rake < 1`:

```python
def _end_decay(self, x: float) -> float:
    frac = self._get_area_fraction(x)          # 0 at ends, 1 at mid
    raked  = np.sqrt(frac)                      # current shape: tapers to 0
    plumb  = np.clip(frac / 0.05, 0.0, 1.0)   # step: full until last 5% of half-length
    return float(self.bow_rake * raked + (1.0 - self.bow_rake) * plumb)
```

`_end_decay` replaces every occurrence of `np.sqrt(frac)` in the hull/deck
computation (half-beam, keel depth, deck-height scaling).

The `plumb` formula above keeps the decay at 1.0 everywhere except within
5% of each end, where it drops linearly to zero. This gives a near-vertical
stem while still closing the hull at the tip.

The specific 5% transition zone is a starting point; it may be adjusted once
the 3D result is reviewed. A future version could expose the transition width
as a parameter (`bow_entry_length_frac`, default 0.05).

#### Deck height at ends

`_get_deck_height_scaling` currently mirrors `_end_decay`. Apply the same
blend there, so plumb bow has visible bow freeboard in the sheer plan.

Workflow 0019 status: this is landed for the package geometry. Exact end-cap
freeboard at `x = +/-L/2` remains deferred with end-cap semantics.

### 2. GUI changes (`gui.py`)

Add `bow_rake` to `SLIDERS`:
```python
("bow_rake", "Bow Rake (1=raked)", 0.0, 1.0),
```

Add to `DEFAULTS`:
```python
bow_rake=1.0,
```

`_station_data` and `_make_generator` pick up the new parameter
automatically since they pass `**self.params`.

### 3. Sheer plan annotation

When `bow_rake < 0.5`, annotate the sheer plan with "Plumb" near the bow
station line. When `bow_rake >= 0.5`, no annotation (existing behaviour).
This is a one-liner in `update_plots` after the sheer plan is drawn.

## Acceptance Criteria

- **Landed:** with `bow_rake = 1.0` (default), the package geometry preserves
  the legacy output.
- **Landed:** with `bow_rake = 0.0`, stations near `x = -L/2` inside the
  5% transition zone retain positive section area. The exact endpoint
  `x = -L/2` remains a zero-area closure point until a future end-cap design
  lands.
- **Landed hull/deck slice:** with `bow_rake = 0.0`, the hull waterplane, keel,
  and deck centerline remain full close to the stem, then drop through the final
  transition zone.
- **Deferred:** STL export currently produces open hull and deck surfaces that
  can be generated at all `bow_rake` values. It does not produce a closed
  watertight hull-plus-deck solid or explicit non-degenerate end-cap polygons.
- **Landed:** `Cp` and `center_box_ratio` interaction tests cover non-default
  `bow_rake` without changing default golden geometry.

## Open Questions

- Should `bow_rake = 0.0` guarantee a truly vertical stem (the very last
  strip of triangles is perpendicular to X), or is the 5% linear fade
  sufficient? For STL printing, a hard vertical face would require an
  explicit end-cap polygon.
- Should bow and stern rake be independently controllable? Owned by RFC 0028;
  `bow_rake` remains the legacy symmetric compatibility field and `stern_rake`
  is the independent stern control.

## Implementation Path

1. Add `_end_decay` method to `KayakGenerator` (~10 lines).
2. Replace `np.sqrt(frac)` calls with `self._end_decay(x)` everywhere in
   generator (~4 substitutions).
3. Add `bow_rake` slider to GUI (~3 lines).
4. Verify STL mesh generation at bow_rake=0, 0.5, 1.0, and keep closed-volume
   watertightness as a separate end-cap/solid-readiness decision.

Total: ~20 lines changed/added across two files.
