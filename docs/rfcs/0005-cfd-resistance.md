# RFC 0005: Resistance Estimation (Michell Integral + ITTC Friction)

Status: proposed
Date: 2026-05-09
Context: generator.py, gui.py; follows RFC 0003

## Problem

The GUI shows estimated displacement and waterplane area, but gives no
feedback on hydrodynamic performance. A builder has no way to compare hull
forms on resistance without exporting STLs and running external software.

For a kayak operating at typical paddling speeds (3–6 kt, Froude number
Fn = V / sqrt(gL) ≈ 0.25–0.50) the two dominant drag components are:

| Component | Fraction of total | Notes |
|---|---|---|
| Viscous (friction) | 60–80% at Fn 0.3 | Scales with wetted surface × ITTC-57 coefficient |
| Wave-making | 20–40% at Fn 0.4–0.5 | Rises steeply near hull speed (Fn = 1.0) |
| Appendages, windage | negligible for hull design | Out of scope |

Both can be computed analytically from the hull offsets with no external
solver: viscous drag via the ITTC-57 friction line, wave drag via the
Michell (thin-ship) integral.

## Goals

- Display total resistance at a user-selected speed in the metrics panel,
  updated live with each slider change.
- Show a resistance-vs-speed curve (Fn 0.2–0.6) in a pop-out or an
  additional panel, broken into viscous and wave components.
- No external CFD dependency; all computation in Python/NumPy.
- Computation completes within 200 ms so it does not lag the GUI.

## Non-Goals

- Full RANS or panel-method CFD (out of scope; for final design validation
  only).
- Induced resistance from paddler weight distribution.
- Resistance in waves (seakeeping), turning, or directional stability.
- Optimisation / parameter sweeping (orthogonal concern).

## Proposal

### 1. New module: `resistance.py`

#### Wetted surface

Computed from the hull mesh via the trapezoidal strip method:

```python
def wetted_surface(kg: KayakGenerator, stations: int = 60) -> float:
    """Integrate wetted perimeter × dx along the hull."""
```

Alternatively, use `get_mesh_arrays("hull")` and sum triangle areas for
faces with at least one vertex below z = 0.

#### ITTC-57 viscous resistance

```python
def viscous_resistance(kg: KayakGenerator, V_ms: float,
                       Sw: float, nu: float = 1.19e-6) -> float:
    """
    Rv = 0.5 * rho * V^2 * Sw * Cf
    Cf = 0.075 / (log10(Rn) - 2)^2    (ITTC-57 line)
    Rn = V * L / nu                    (kinematic viscosity of seawater at 15°C)
    """
```

#### Michell integral (wave resistance)

The Michell integral gives wave resistance for a slender displacement hull
in inviscid, linearised free-surface flow:

```
Rw = (rho * g^2) / (pi * V^2) * integral_1^inf  |I(lambda)|^2 / sqrt(lambda^2 - 1)  dlambda

where
  I(lambda) = integral_hull  dS/dx * exp(-k0 * lambda^2 * d) * cos(k0 * lambda * x)  dx dd
  k0 = g / V^2
  d  = depth below waterline
  dS/dx = waterplane half-breadth at longitudinal position x (thin-ship approximation)
```

Implementation:
```python
def wave_resistance_michell(kg: KayakGenerator, V_ms: float,
                             stations: int = 60,
                             depth_strips: int = 20) -> float:
    """Numerically evaluate the Michell integral."""
```

The double integral is discretised over x (60 stations) and depth d (20
strips). The outer lambda integral is evaluated by Gauss-Laguerre
quadrature (20 points) after the substitution lambda = 1/cos(theta). Total
cost: 60 × 20 × 20 = 24 000 multiply-adds per speed point. At 20 speed
points this is ~500 000 operations — sub-millisecond in NumPy.

**Accuracy note:** The Michell integral assumes a wall-sided, thin ship and
linearised free-surface conditions. For Fn < 0.5 and LOA/B > 6 (both true
for kayaks) the error vs. model tests is typically 10–25%. This is
sufficient for comparative design evaluation but not for final performance
prediction.

#### Speed sweep

```python
def resistance_curve(kg: KayakGenerator,
                     V_knots: np.ndarray | None = None) -> dict:
    """
    Returns dict with keys:
      V_knots, Fn, Rv_N, Rw_N, Rt_N  (all 1-D arrays)
    """
```

Default speed range: 1.0–6.0 kt in 0.25-kt steps (21 points).

### 2. GUI changes (`gui.py`)

#### Target speed slider

Add a speed slider to the control panel:

```python
("target_speed_kt", "Target Speed (kt)", 1.0, 6.0),
```

Default: 3.5 kt (typical cruising pace).

#### Metrics panel update

Replace the current four-line metrics block with a six-line version that
adds:
```
Target speed  3.5 kt   (Fn 0.34)
Viscous drag   12.3 N
Wave drag       3.1 N
Total drag     15.4 N
```

These are recomputed in `_refresh_metrics` by calling
`resistance.viscous_resistance` and `resistance.wave_resistance_michell`.

#### Resistance curve pop-up

A new button "Resistance Curve" opens a second matplotlib figure (not
a PyVista window) with:
- X axis: speed (kt) or Fn
- Y axis: resistance (N)
- Two filled areas: viscous (blue) + wave (orange), stacked
- A vertical marker at the current target speed
- A secondary Y axis showing effective power (W = R × V)

The figure is generated fresh on each button click (no live update — the
user clicks when they want a snapshot). This avoids adding another 200 ms
computation to every slider drag.

### 3. Performance budget

| Operation | Cost (estimated) |
|---|---|
| Wetted surface (60 stations) | < 1 ms |
| ITTC Cf at one speed | < 0.1 ms |
| Michell Rw at one speed | < 5 ms |
| Resistance curve (20 points) | < 100 ms |

The single-speed metrics update (triggered by slider drag) stays under
10 ms. The full curve (triggered by button) stays under 100 ms. Both are
within the 200 ms perceptual threshold.

## Acceptance Criteria

- Changing the `beam` slider from 0.55 m to 0.65 m increases total drag at
  3.5 kt by ≥ 5% (physically expected: more wetted surface + more wave drag).
- At Fn = 0.1 (very slow), wave drag is < 5% of viscous drag.
- At Fn = 0.5 (near hull speed), wave drag is ≥ 20% of viscous drag.
- `resistance_curve` returns in < 200 ms on a modern laptop.
- The Michell integral result for a standard Wigley parabolic hull matches
  the published Michell value within 5% (unit test).

## Open Questions

- Should the target speed slider live in the main control panel (always
  visible) or only in the resistance curve pop-up? Current proposal: main
  panel, since the single-speed drag figure in metrics is useful during
  design.
- Froude number display: show Fn alongside knots so users understand the
  regime?
- Form factor (1 + k): the ITTC method typically applies a form factor
  correction for viscous pressure resistance. For slender kayaks (LOA/B > 7)
  k ≈ 0.05–0.10. Include as a fixed constant or expose as a parameter?

## Implementation Path

1. Write `resistance.py` with `wetted_surface`, `viscous_resistance`,
   `wave_resistance_michell`, and `resistance_curve` (~120 lines).
2. Add unit test against the Wigley hull analytical solution (~30 lines).
3. Add `target_speed_kt` slider to `gui.py` (~3 lines).
4. Expand `_refresh_metrics` to call `resistance.py` functions (~15 lines).
5. Add "Resistance Curve" button and pop-up handler (~30 lines).

Total: ~200 lines across three files.
