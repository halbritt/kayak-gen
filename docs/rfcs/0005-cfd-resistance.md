# RFC 0005: Resistance Estimation (Michell Integral + ITTC Friction)

Status: landed-raw-filter
Date: 2026-05-09
Context: generator.py, gui.py; follows RFC 0003

Status note (workflow 0013, 2026-05-13): landed as a raw comparative filter.
The current ITTC viscous estimator is usable, and the Michell implementation is
retained as an exploratory fast-filter signal with explicit metadata warnings.
It is not accepted as a calibrated final performance predictor. The original
low-Froude wave/viscous component-ratio target, calibrated kayak envelope, and
200 ms full-curve interactive target are deferred to future calibrated and/or
optimized work rather than carried as expected failures in the active test
suite.

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
- Raw curve computation is suitable for snapshot/offline comparison and carries
  enough metadata to prevent calibrated-performance overclaiming.
- A future optimized or surrogate-backed curve implementation should complete
  within 200 ms so it does not lag interactive UI use.

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

The original RFC expected every operation to fit an interactive 200 ms budget.
That is now treated as a future optimized-evaluator target. The landed raw
filter is accepted for snapshot/offline comparison under the regression budget
enforced by tests.

| Operation | Landed raw-filter expectation |
|---|---|
| Wetted surface | Fast enough for test and snapshot use |
| ITTC Cf at one speed | Fast enough for test and snapshot use |
| Michell Rw at one speed | Finite and non-negative across the paddling band |
| Resistance curve | Under the current test regression budget |

An optimized, cached, or surrogate-backed implementation may reintroduce a
strict 200 ms full-curve acceptance target in a later RFC or follow-up.

## Acceptance Criteria

### Landed raw-filter tier

- Zero speed returns zero viscous and wave drag.
- ITTC-57 viscous drag increases monotonically with speed and scales with
  wetted surface.
- At 3.5 kt, viscous and total drag remain in a paddler-class sanity envelope
  rather than returning negligible or explosive values.
- Michell wave resistance returns finite, non-negative values across the kayak
  speed band.
- `resistance_curve` returns speed, Froude number, viscous drag, wave drag,
  total drag, and metadata arrays with consistent shapes and units.
- Resistance metadata declares `model_family = "raw_ittc_michell"`,
  `calibration_status = "uncalibrated"`, accepted use as a comparative filter,
  and warnings that it is not a final performance prediction.
- Resistance metadata records quadrature settings, verification fixtures, and
  empty calibration/provenance fields when no accepted calibration fixture is
  present.
- The default resistance source registry contains reviewed source records but
  no canonical calibration fixtures.
- The Michell integral result for a standard Wigley parabolic hull matches the
  published Michell value within 5% in the verification unit test.
- The raw curve remains within the current regression budget used by tests for
  snapshot comparison. The accepted budget is not the original 200 ms
  interactive full-curve target.

### Deferred criteria

- Low-Froude wave drag less than 5% of viscous drag is not accepted for the
  current kayak loft and raw Michell discretization.
- A 200 ms full-curve target is deferred until an optimized, cached, or
  surrogate-backed evaluator exists.
- Calibrated kayak resistance prediction, validity envelopes, and default
  Pareto resistance scoring remain future work.

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

1. Land the raw evaluator with `wetted_surface`, `viscous_resistance`,
   `wave_resistance_michell`, and `resistance_curve`.
2. Verify Michell's prefactor against a Wigley parabolic hull.
3. Record metadata that makes the evaluator's uncalibrated comparative-only
   status machine-readable.
4. Keep the GUI integration limited to claims supported by the raw-filter tier.
5. Defer calibrated kayak fixtures, validity envelopes, optimized full-curve
   latency, and Pareto-frontier use until source and implementation support
   exist.
