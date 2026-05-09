# RFC 0004: Plumb Bow Support

Status: proposed
Date: 2026-05-09
Context: generator.py, gui.py; follows RFC 0003

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
- `bow_rake` applies independently to bow and stern; a single scalar
  controls both (symmetric). A future RFC may split them.
- The 3D mesh, STL export, cross-section view, and sheer plan all update
  correctly for any `bow_rake` value.
- The station slider at x = −L/2 shows a non-zero cross-section area when
  `bow_rake < 0.5`.

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

- With `bow_rake = 1.0` (default) the hull is identical to the current
  output.
- With `bow_rake = 0.0` the station at x = −L/2 has non-zero area (visible
  sliver in cross-section view).
- With `bow_rake = 0.0` the sheer plan shows the keel running nearly flat to
  the bow, then dropping sharply to the waterline in the last 5% of length.
- STL export produces a watertight mesh at all `bow_rake` values (no
  degenerate zero-area end caps).
- The `center_box_ratio` and `Cp` sliders interact correctly with `bow_rake`:
  prismatic coefficient is still honoured at midship.

## Open Questions

- Should `bow_rake = 0.0` guarantee a truly vertical stem (the very last
  strip of triangles is perpendicular to X), or is the 5% linear fade
  sufficient? For STL printing, a hard vertical face would require an
  explicit end-cap polygon.
- Should bow and stern rake be independently controllable? (Stern often
  raked even on plumb-bow designs.) Deferred to RFC 0006.

## Implementation Path

1. Add `_end_decay` method to `KayakGenerator` (~10 lines).
2. Replace `np.sqrt(frac)` calls with `self._end_decay(x)` everywhere in
   generator (~4 substitutions).
3. Add `bow_rake` slider to GUI (~3 lines).
4. Verify STL mesh is watertight at bow_rake=0, 0.5, 1.0.

Total: ~20 lines changed/added across two files.
