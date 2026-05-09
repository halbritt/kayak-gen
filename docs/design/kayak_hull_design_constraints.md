# Kayak Hull Design Constraints for Generative CFD Pipeline

Research synthesis on the design parameters and quantified ranges that matter for ocean kayak and surfski hull generation, organized so they map cleanly onto optimization variables and CFD objectives.

---

## 1. Core Tradeoff Structure

Every kayak hull sits on three fundamental tradeoffs that pull against each other. A generative pipeline should treat them as a Pareto frontier rather than expect a single optimum.

1. **Speed (low drag) vs. stability** — narrower hulls reduce wetted area and wave-making but reduce righting moment per degree of heel.
2. **Tracking vs. maneuverability** — long waterline + low rocker = straight-line speed + resistance to turning; short effective waterline (from rocker) = the inverse.
3. **Primary vs. secondary stability** — flat/wide-bottomed cross sections are stiff at zero heel but give up suddenly when leaned; rounded/V cross sections feel "tippy" at rest but build a stronger restoring moment as you edge them.

For ocean use, the design center has historically pushed toward secondary stability, narrower beams, and moderate length. A flat bottom is actually less secure in waves and current — high-performance sea kayaks use round or V-shaped cross sections that feel tippy on flat water but maximize secondary stability.

---

## 2. Stability — Quantification for CFD

The qualitative "primary vs. secondary" framing maps onto naval architecture cleanly.

### Primary stability ≈ initial metacentric height GM₀

```
GM = KB + BM − KG
BM = I_T / ∇
```

Where `I_T` is the transverse second moment of area of the waterplane and `∇` is displaced volume. For small heel angles (≤ ~5°), the righting arm `GZ ≈ GM·sin(θ)` and that's the slope of the stability curve at the origin. Wide waterline beam blows up `I_T` and so blows up `GM₀`.

### Secondary stability ≈ shape of the GZ curve at higher heel

Typically 10°–45° for a kayak. The linear `GM·sin(θ)` approximation breaks down past ~10–15°; you have to integrate the actual displaced-volume centroid shift at each heel angle.

A reasonable convention: assume paddler CoG **10 inches above the seat**, paddler sitting bolt upright, no active correction.

### Required outputs per candidate hull

- `GM₀` — primary stability (analytic from waterplane geometry, no CFD needed)
- **Max GZ and the heel angle at which it occurs** — secondary stability and the "edge" before capsize. Sea kayaks typically peak GZ in the 25°–40° range.
- **Full GZ curve from 0° to 90°** — purely hydrostatic; this is geometry.

Reference order of magnitude: a Night Heron with 200 lb paddler (240 lb total system) has max GZ of ~0.047 ft, yielding peak righting moment ~11.3 ft·lbs.

### Critical pitfall

**Total beam is uninformative on its own — what drives stability is beam at the waterline.** A hull with 22" total beam but 18" waterline beam (typical V-section) behaves very differently than 22"/22". The generator needs both as independent parameters.

---

## 3. Length

### Sea kayaks (ocean/touring)

- **Practical sweet spot:** 14–18 ft (4.3–5.5 m)
- Solo range: 14–20 ft (4.3–6.1 m)
- Tandem range: 18–24 ft (5.5–7.3 m)
- General-purpose ocean design center: **5.0–5.25 m**
- Below ~14 ft → recreational class, poor seakeeping
- Above ~18 ft → maneuverability/weight penalties; crosses into surfski territory

### Surfskis

Ocean racing surfskis are longer than long-distance racing kayaks, with more rocker, less transverse stability, more longitudinal stability (paddler seated more toward center for wave riding), bow volume to punch through surf, and a long waterline for swell riding.

- **Modern design center:** 5.5–6.4 m (18–21 ft)
- 6.4 m / 21 ft is the elite class limit
- 19 ft is the "magic number" — required length for surf lifesaving spec skis
- Intermediate skis cluster around 5.5 m / 18 ft

### Froude number context

```
Fn = v / √(g · L_wl)
```

Wave-making resistance is governed by `Fn`. Classical "hull speed" sits at `Fn ≈ 0.40` (speed/length ratio ~1.34), but racing kayaks regularly exceed hull speed by more than 100% without planing because they have very fine ends and high length-to-beam ratios. Slim, fine-ended displacement hulls don't see the wall at `Fn ≈ 0.4` the way fatter hulls do.

| Regime | Fn | Speed at L_wl = 5.2 m |
|---|---|---|
| Touring sea kayak cruise | 0.30–0.40 | ~6–7 mph |
| Surfski cruise/race | 0.40–0.55 | ~7–10 mph |
| Top elite paddler avg | ~0.50 | 8.5+ mph (Greg Barton class) |

**Recommended CFD evaluation points:** run resistance at three speeds — typical cruise (`Fn ≈ 0.30`), sustained pace (`Fn ≈ 0.40`), and sprint (`Fn ≈ 0.50`) — to get a curve. The optimum hull at each Fn is different.

---

## 4. Beam

This is the parameter that does the heaviest lifting on the speed/stability tradeoff. Use beam-at-waterline (`B_wl`) as your primary variable; total beam (`B_oa`) as a secondary parameter for deck flare.

| Class | Total Beam (B_oa) | Waterline Beam (B_wl) | L/B_wl |
|---|---|---|---|
| Recreational kayak | 28–32" / 71–81 cm | ~26–30" / 66–76 cm | 5–7 |
| Touring sea kayak (stable) | 22–24" / 56–61 cm | ~20–22" / 51–56 cm | 8–10 |
| Performance sea kayak | 20–22" / 51–56 cm | ~18–20" / 46–51 cm | 10–11 |
| Greenland-style / expedition | 20–22" / 51–56 cm | ~18–20" / 46–51 cm | 10–12 |
| Stable surfski (V8-class) | 21.25" / 54 cm | ~19–20" / ~50 cm | 10–11 |
| Intermediate surfski | 19–20" / 48–51 cm | ~18–19" / ~46–48 cm | 11–12 |
| Elite surfski | 16.5–17.3" / 42–44 cm | ~15–17" / ~38–43 cm | 13–15 |

### Real-world reference points (Epic V-series)

- V7: 17' × 21.25"
- V8: 18' × 21.25"
- V8 Pro / V9: 19' × 20" / 19.3"
- V10 cluster: ~17.5–18"
- V11: 16.9"

### Hard floors / ceilings

- **Adult-male paddleability floor:** ~21" total width. Narrower than this is too unstable for a beginner.
- **Practical ceiling:** ~23" total width. Wider than this feels clumsy and lurches in rough water.

### Beam location

- **Surfskis:** widest section just behind the seat; very gradual taper, beam-at-seat ≈ max beam.
- **Sea kayaks:** max beam often pulled slightly aft of cockpit center.

---

## 5. Rocker

The parameter with the worst standardization. Pick a definition and stick to it.

### Three live definitions

1. **Absolute rise at the ends** — quoted as `1.5"` at bow, `0.5"` at stern with the boat resting on a flat surface. Easiest physical measurement; useless for design comparison since it ignores LWL.
2. **Naval architect method** — set the boat with waterline parallel to the floor; drop a plumb line from the foremost bow point and measure the keel-to-floor distance 10 inches aft of that line. Repeat at the stern.
3. **Normalized curvature** — rise as a fraction of LWL measured at 90% LWL station. Best for cross-design comparison. **Use this as the canonical parameter.**

### Practical ranges (bow rise / stern rise from a flat baseline along keel line)

| Hull type | Bow rocker | Stern rocker |
|---|---|---|
| Whitewater playboat | 6–10" | 6–10" (often symmetric) |
| Whitewater creek boat | 3–5" | 2–3" |
| Crossover / day-touring sea kayak | 2–4" | 1–2" |
| **Ocean kayak (general purpose)** | **2–3"** | **1–2"** |
| Expedition / tracking-priority sea kayak | 1–2" | 0.5–1" |
| Flat-water racing K1 | ~0.5" | ~0.25" |
| Surfski (intermediate) | 2–3" | 1–1.5" |
| Surfski (elite, downwind-optimized) | 3–5" | 1–2" |

### Asymmetry is the norm

Ocean kayaks consistently carry more rocker forward than aft. Forward rocker → bow lift in waves and turning ease. Trailing waterline → tracking via stern.

The modern surfski trend is more pronounced bow rocker specifically to prevent bow burying when surfing downwind runs (e.g., Gen 4 Epic V10 has streamlined bow with greater rocker for best downwind performance of the V10 series).

### Turning rate

The relevant geometric quantity is **effective waterline length when heeled**. Rocker shortens the static-flat WL but, more importantly, when you edge the boat the waterline becomes asymmetric and the hull pivots around a shorter effective length. Evaluate turning by computing static turning radius at 15° and 25° of edge.

---

## 6. Cross-Section / Chines

### Five canonical archetypes

1. **Flat-bottomed** — high primary, low secondary, sudden stability collapse past ~15° heel. **Inappropriate for ocean use** — only relevant as a baseline.
2. **Shallow-arch** — moderate primary, good secondary, balanced. The dominant general-purpose ocean kayak shape.
3. **Shallow-V** — lower primary, higher secondary, better tracking. Common in performance touring boats.
4. **Deep-V (Greenland flat-V)** — low primary, very high secondary, excellent rough-water stability. Demands rolling/bracing skill. Always wants to sit on one side of the V or the other.
5. **Round** — lowest primary, smoothest secondary curve, lowest wetted area for given displacement → fastest hull form. Surfski territory.

### Chine type (partially independent)

Best parameterized as the radius of curvature at the bilge.

- **Hard chine** (radius ~5–15 mm) — adds bite when edging, gives a distinct stability "shelf" at the chine angle. Easier to roll.
- **Soft chine** (radius 50+ mm) — smoother stability curve, slightly less wetted surface drag. Multi-chine hulls have ~3.2% less wetted surface than equivalent hard-chine hulls.
- **Multi-chine** — compromise common on Greenland-derived designs. Model as 2–3 break angles instead of a single chine.

---

## 7. Volume / Displacement

The hard constraint your generator must satisfy before any CFD: **displaced volume at design waterline = total system weight**.

### German touring rule of thumb

Total transport weight (kg) should be **30%–60% of kayak volume (L)**.

- Lower end (30–40%) → racing/performance
- Middle (40–50%) → general touring
- Upper (50–60%) → loaded expedition

### Working numbers

Single-paddler ocean kayak, no load:
- Paddler (75–95 kg) + hull (15–25 kg) = ~95–120 kg total
- → ~0.095–0.120 m³ = **95–120 L of submerged hull volume**

Surfski, no expedition load:
- Target ~85–110 L design displacement

---

## 8. Prismatic Coefficient & Volume Distribution

```
Cp = ∇ / (A_max × L_wl)
```

Ratio of displaced volume to a prism with the max-section area projected over the waterline length. For displacement hulls in the kayak Froude regime:

| Application | Cp |
|---|---|
| Low Fn cruising (touring sea kayak, Fn 0.30–0.35) | 0.52–0.55 |
| Sustained higher Fn (surfski, racing K1) | 0.55–0.60 |
| General guidance: don't exceed | 0.70 |

**Heuristic:** Cp should decrease with smaller Froude numbers down to ~0.55 up to Fr ≈ 0.33, then increase with rising Froude number.

A surfski wants **fuller ends** than a touring sea kayak — that's the bow volume requirement for downwind/wave punching. A traditional tracking-focused expedition sea kayak wants **finer ends**.

---

## 9. Generator Parameter Space (Recommended)

Continuous variables plus 1–2 discrete shape selectors per hull:

| Parameter | Range | Notes |
|---|---|---|
| `L_oa` (overall length) | 4.0–6.5 m | |
| `L_wl` (waterline length) | 0.93–0.98 × L_oa | Function of rocker/end fineness |
| `B_oa` (max beam) | 0.42–0.65 m | |
| `B_wl` (waterline beam) | 0.36–0.58 m | Constrained < B_oa, typically 0.85–0.95 × B_oa |
| Bow rocker (rise at 90% LWL fwd) | 0–0.13 m | |
| Stern rocker (rise at 90% LWL aft) | 0–0.06 m | |
| Max draft | 0.10–0.16 m | |
| `Cp` (prismatic coefficient) | 0.50–0.62 | |
| Cross-section archetype | discrete (flat / arch / shallow-V / deep-V / round) | OR continuous via deadrise angle (0°–25°) + bilge radius |
| Bilge radius | 0.005–0.080 m | |
| LCB position (fraction of LWL) | 0.48–0.55 | Slightly aft of center is normal |
| Bow flare angle | — | Above-water bow shape; relevant for wave-piercing surfskis |
| Freeboard at bow / mid / stern | min ~0.10 m at midship | For ocean conditions |

---

## 10. CFD Objectives Worth Computing

For each candidate hull, the metrics that actually discriminate good from bad designs:

| Metric | Method | Purpose |
|---|---|---|
| Drag at three speeds (Fn ≈ 0.30, 0.40, 0.50) | CFD | Total resistance, broken into wave-making vs. viscous |
| Wetted surface area | Geometric | Proxy for skin friction at low Fn |
| `GM₀` | Hydrostatic (analytic) | Primary stability |
| GZ curve 0°–90° | Hydrostatic | Full stability picture, secondary stability peak |
| Bow pitch response in waves | Unsteady CFD or strip-theory | Surfski only |
| Effective turning radius at edge | Geometric (heeled waterplane) | Maneuverability |
| Reserve buoyancy at bow | Geometric | % of bow volume above design waterline; surfski-critical |

### Reynolds regime

`Re ~ 10⁶–10⁷` for `L_wl × v`. **Skin friction dominates** and is well-approximated by flat-plate skin friction over the wetted surface area. Laminar flow only over roughly the first 3 cm at cruise speeds — assume turbulent boundary layer everywhere else.

### Pipeline strategy

The cheap-to-compute metrics (everything geometric/hydrostatic) should run as filters before spending cycles on CFD. A generator producing 10,000 candidates can be culled to 100 plausible ones via hydrostatics in seconds, then run resistance CFD only on the survivors.

---

## 11. Bottom Line

The surfski/sea kayak distinction collapses at the design level into roughly three knobs:

1. **L/B_wl ratio** — drives the speed/stability tradeoff
2. **Bow rocker** — drives downwind/wave behavior
3. **Cp / volume distribution** — drives where displacement sits along the length

Most marketing distinctions between "intermediate" and "elite" surfskis collapse to those three variables plus seat height, which is a paddler-fit issue rather than hydrodynamics.
