# RFC 0006: Hull Design Constraints — Canonical Parameter Space and Class Presets

Status: proposed
Date: 2026-05-09
Context: generator.py, gui.py; informs RFC 0005 (resistance) and any
future optimizer RFC. Source: `kayak_hull_design_constraints.md`
(research synthesis on ocean kayak / surfski hull design).

## Problem

The generator and GUI today expose a flat list of sliders (`length`,
`beam`, `draft`, `deck_height`, `Cp`, `deck_flatness`, `center_box_ratio`)
with hand-picked ranges. There is no codified relationship between those
ranges and the design space they purport to cover.

That has three concrete consequences:

1. **Slider ranges are arbitrary.** Nothing prevents a user from setting
   beam = 0.30 m at length = 6.5 m (an L/B ratio of 21, beyond elite
   surfski). The hull generates and the resistance estimate runs, but the
   result is not a kayak any human can paddle.
2. **No design intent shortcut.** A user wanting to design "an
   intermediate surfski" must look up the right combination of length,
   beam, rocker, and Cp themselves. The GUI offers no class presets.
3. **Stability is invisible.** Beam-at-waterline (the parameter that
   actually drives stability) is not represented; only total beam is. The
   generator implicitly assumes `B_wl = B_oa`, which is wrong for any V-
   sectioned hull.

We have a synthesis document
(`kayak_hull_design_constraints.md`) that quantifies the parameter space,
class boundaries, and the metrics that discriminate good designs. This
RFC adopts it as the canonical reference and proposes the minimal
generator/GUI changes needed to honour it.

## Goals

- Adopt the parameter table in §9 of the constraints document as the
  authoritative ranges for generator and GUI sliders.
- Add four named class presets (touring sea kayak, performance sea kayak,
  intermediate surfski, elite surfski) selectable from the GUI.
- Surface beam-at-waterline (`B_wl`) as a first-class generator parameter
  distinct from total beam.
- Surface the CFD/hydrostatic objective list (§10 of the document) as a
  shared contract that future RFCs (resistance, stability, optimizer)
  consume.
- Keep the constraints document under version control alongside the RFCs
  so the rationale travels with the code.

## Non-Goals

- Implementing the GZ-curve or stability calculation (separate future
  RFC; this one only reserves the API).
- Implementing rocker, plumb-bow, or asymmetric-end behaviour beyond
  what RFC 0004 already specifies.
- Multi-chine or deadrise parameterisation (mentioned in §6 of the
  document; deferred).
- Hard-locking the GUI to in-class ranges. The presets seed values; the
  user can still slide outside them.
- Optimisation / generative search (orthogonal; relies on this RFC).

## Proposal

### 1. Vendor the constraints document

Copy `kayak_hull_design_constraints.md` into `docs/design/` so it lives
in the repo. All RFCs and code comments that reference design ranges
cite it by section number rather than restating numbers.

### 2. New `KayakClass` presets

Add `kayak_classes.py` with a small dataclass and four canonical
presets, derived directly from §3, §4, §5, and §8 of the document:

```python
@dataclass(frozen=True)
class KayakClass:
    name: str
    length_m: tuple[float, float]      # (min, max, default)
    beam_oa_m: tuple[float, float]
    beam_wl_m: tuple[float, float]
    draft_m:  tuple[float, float]
    bow_rocker_m: tuple[float, float]
    Cp: tuple[float, float]
    notes: str

CLASSES = {
    "touring":      KayakClass(...,  L=4.3-5.5, B_oa=0.56-0.61, ...),
    "performance":  KayakClass(...,  L=4.6-5.5, B_oa=0.51-0.56, ...),
    "surfski_int":  KayakClass(...,  L=5.5-5.8, B_oa=0.48-0.54, ...),
    "surfski_elite":KayakClass(...,  L=5.8-6.4, B_oa=0.42-0.46, ...),
}
```

Exact numbers come from the constraints table; this RFC fixes them as
the canonical defaults so downstream code does not have to re-derive
them.

### 3. Generator changes (`generator.py`)

- Add `beam_wl: float | None = None` to `KayakGenerator.__init__`.
  When `None`, default to `0.92 * beam` (mid of the 0.85–0.95 ratio
  guidance in §9). When set, the cross-section is interpolated so that
  the waterline (z = 0) intercept matches `beam_wl` while the gunwale
  (sheer) sits at total beam.
- Add `LCB_frac: float = 0.50` (longitudinal centre of buoyancy as a
  fraction of LWL, range 0.48–0.55 per §9). Default keeps current
  symmetric behaviour.
- No change to the section-shape routine yet; `beam_wl` is honoured by
  scaling the lower half of each station independently of the upper
  half. Implementation detail deferred to the implementation step.

### 4. GUI changes (`gui.py`)

- Add a class dropdown above the sliders:
  `[Touring | Performance | Intermediate Surfski | Elite Surfski |
   Custom]`.
- Selecting a class:
  - Sets each slider's range to the class's (min, max).
  - Sets each slider's value to the class's default.
  - Persists until the user moves any slider, at which point the class
    auto-switches to "Custom" and ranges relax to the global maxima
    (4.0–6.5 m length, 0.42–0.65 m beam, etc., per §9).
- Add a `beam_wl` slider underneath `beam`. Its max is bounded by the
  current `beam` value (live-clamped on `beam` changes).
- Add a small advisory line below the metrics panel that flags
  out-of-class combinations:
  `"L/B_wl = 12.4 — exceeds Performance class (10–11)"`.
  Pure advisory; no hard block.

### 5. Hydrostatic / CFD objective contract

Define a single dictionary returned by a new
`generator.evaluate_hydrostatics()` method, with these keys (matching
§10 of the document):

| Key | Units | Source |
|---|---|---|
| `displaced_volume` | m³ | trapezoidal integration of section areas |
| `wetted_surface`   | m² | sum of below-waterline triangle areas |
| `LCB_frac`         | — | computed centroid / L_wl |
| `Cp`               | — | recomputed from geometry (verifies input) |
| `GM0`              | m | I_T / ∇ + KB − KG (KG = 0.25 m placeholder) |
| `gz_curve`         | dict[deg, m] | empty until the stability RFC lands |
| `Fn_at`            | dict[float, …] | reserved for resistance plug-in |

`resistance.py` (RFC 0005) and the future stability module both write
into this dictionary. Treating it as a shared contract here keeps later
RFCs from re-negotiating the schema.

### 6. Validation banner

When any of the following is true, render a yellow warning above the 3D
view:

- `L / B_wl < 8` (sub-touring proportions)
- `L / B_wl > 15` (beyond elite surfski)
- `Cp < 0.50` or `Cp > 0.65` (outside the §8 envelope)
- `displaced_volume < 0.075 m³` (below paddler-only displacement)
- `displaced_volume > 0.180 m³` (loaded-expedition territory; user
  should confirm)

The user can dismiss the banner; it reappears if any flagged value
changes again.

## Acceptance Criteria

- `docs/design/kayak_hull_design_constraints.md` exists in the repo.
- `kayak_classes.CLASSES` has exactly the four named presets and each
  preset's defaults round-trip through `KayakGenerator` without
  warnings.
- Selecting "Touring" in the GUI produces a hull with L = 5.0 m,
  B_oa = 0.58 m, B_wl ≈ 0.53 m, Cp = 0.54, draft ≈ 0.12 m.
- Selecting "Elite Surfski" produces L = 6.1 m, B_oa = 0.43 m,
  B_wl ≈ 0.40 m, Cp = 0.58, draft ≈ 0.11 m.
- A unit test verifies that `KayakGenerator(beam_wl=0.5,
  beam=0.6).evaluate_hydrostatics()["displaced_volume"]` is strictly
  less than the same generator with `beam_wl = 0.6`.
- The advisory text under the metrics panel updates within one slider-
  drag tick (< 50 ms).
- No regression: with the GUI in "Custom" and all sliders at their
  prior defaults, every existing metric and the STL output match the
  pre-RFC values bit-for-bit.

## Open Questions

- Should the class presets also seed `bow_rake` (RFC 0004) and rocker
  values once those parameters land? Proposed: yes, but defer the
  preset values until both RFCs are accepted to avoid two churn passes.
- Where should `KG` (vertical centre of gravity) come from for `GM0`?
  The constraints doc suggests "paddler CoG 10 inches above the seat";
  hard-code 0.25 m for now or expose as a slider? Lean: hard-code now,
  expose later if the stability RFC needs it.
- Do we want a fifth "Recreational" preset for completeness, even
  though §1 calls flat-bottomed recreational hulls "inappropriate for
  ocean use"? Lean: no — keep the preset list aspirational.
- The constraints document lists rocker, deadrise, and chine radius as
  parameters we do not yet model. Do we add stub fields to
  `KayakGenerator` now (so the class presets can reference them) or
  wait for each parameter's own RFC? Lean: stub fields, marked
  `# unused: see RFC NNNN`, so the preset literals are stable.

## Implementation Path

1. Copy `kayak_hull_design_constraints.md` into `docs/design/` and add
   a one-line pointer in `docs/rfcs/README.md`.
2. Write `kayak_classes.py` with the dataclass and four presets
   (~60 lines).
3. Add `beam_wl` and `LCB_frac` parameters to `KayakGenerator`; modify
   `_get_slice_points` so the lower half of the section honours
   `beam_wl` (~25 lines changed).
4. Add `evaluate_hydrostatics()` method returning the contract dict
   (~40 lines).
5. Add the class dropdown, `beam_wl` slider, and advisory banner to
   `gui.py` (~80 lines).
6. Unit tests: preset round-trip, displacement monotonicity in
   `beam_wl`, advisory banner triggers (~50 lines).

Total: ~250 lines across four files plus the vendored doc.

## Domain Modeling

`KayakClass` is a **value object** (immutable, equality by content,
identifies a region of the design space rather than a specific hull).
The preset registry `CLASSES` is a small **bounded registry**, not an
aggregate root.

The hydrostatics dictionary returned by `evaluate_hydrostatics()` is a
**read model** (per `DDD.md § "Adding to the model"`): downstream
modules (resistance, stability, GUI) consume it but do not mutate the
hull aggregate through it. New objective metrics extend the read model
without changing `KayakGenerator`'s public surface.
