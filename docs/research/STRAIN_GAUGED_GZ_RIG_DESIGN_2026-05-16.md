# Strain-gauged moment-arm rig for measured high-angle GZ — design — 2026-05-16

This memo is the detailed design for measurement option 2 of
`CALIBRATION_DATA_FINDINGS_2026-05-16.md` ("force-arm rig with a single-axis
or six-axis load cell"). It is the physical-instrument counterpart to
RFC 0050, which scopes the data fixture and acceptance gates.

The motivation is unchanged from the findings memo: D007 / D014 cannot be
closed from public datasets, and protocol 1 (inclining-by-known-weight)
yields only discrete `(M, θ)` points and runs out of usable range near the
angle of maximum GZ, where the boat wants to capsize. Replacing the fixed
weight with a strain-gauged moment arm lets the operator ride the GZ curve
continuously and safely past the maximum, then back through the angle of
vanishing stability, in a single sweep.

## What is measured

For a heeled hull in free equilibrium, the righting arm `GZ(θ)` satisfies

```
M_righting(θ) = Δ · g · GZ(θ) = F_applied(θ) · L_eff(θ)
```

where `Δ` is the displaced mass at upright, `F_applied` is the force the
rig applies tangentially to the arm at heel `θ`, and `L_eff` is the
component of the arm length perpendicular to the local gravity vector at
the gauge's line of action. The rig measures `F_applied(t)` and `θ(t)`
continuously; `L_eff(θ)` comes from the arm geometry plus the encoder.

The output is a dense `(θ, GZ)` trace that resolves:

- the angle and value of `GZ_max`;
- the inflection between primary and secondary stability;
- the angle of vanishing stability `φ_v` where `GZ` crosses zero;
- the area under the positive `GZ` curve to `φ_v` (dynamic stability
  proxy);
- hysteresis between the loading and unloading legs of the sweep
  (a diagnostic, not a published metric).

The rig does **not** measure dynamic capsize, bracing response, wave or
surf forcing, or flooding progression. Those are excluded for the same
reasons RFC 0043 excludes them from the analytical evaluator.

## Rig geometry

A rigid, kinematically simple lever beats a clever multi-bar mechanism.
The geometry the operator commits to before the run is:

- **Pivot point.** A horizontal pivot fixed in the *hull frame* on the
  centerplane at a recorded longitudinal station and a recorded height
  above the upright waterline. The pivot moves with the hull as it
  heels, trims, and heaves. Recording the pivot in hull coordinates is
  what lets the post-run reduction know where the arm is in space at
  every angle.
- **Arm.** A single rigid lever of length `L_arm` (pivot to gauge
  attachment) with bending stiffness high enough that arm deflection
  under peak `F_applied` is negligible relative to `L_arm`. The arm
  extends transversely from the centerplane in the direction of the
  applied heel.
- **Force application line.** The arm terminates in a low-friction
  attachment (cable, low-stretch tether) running over a fixed pulley
  whose position is surveyed in the *world frame*. The cable transmits
  `F_applied` to a winch or hand line. The pulley location plus the
  arm tip position give the line-of-action vector at every instant.
- **Pivot encoder.** A rotary encoder or six-axis IMU rigidly mounted
  at the pivot reports heel `θ` directly. A second IMU on the hull
  near the bow gives an independent check and resolves any roll-yaw
  coupling.
- **Waterline reference.** A static water-surface sensor (capacitive
  staff gauge, or two webcams with calibrated targets at bow and stern)
  resolves heave and trim against the hull frame at each `θ`. This is
  what lets the post-run reduction either accept the measured free
  equilibrium or detect that the rig is constraining it.

The hull is **otherwise free**: no bow or stern restraint that prevents
trim or heave, no transverse restraint that prevents sway, only soft
station-keeping (slack lines fore and aft) to keep the hull from
drifting out of the test area. Constraining trim or heave changes what
is being measured and breaks the comparison to RFC 0043's free-floating
hydrostatic model.

## Instrumentation

| Channel        | Sensor                                              | Target accuracy        |
|----------------|-----------------------------------------------------|------------------------|
| `F_applied`    | Single-axis tension load cell, ≥ 2× peak expected   | ±0.25 % FS             |
| Heel `θ`       | Rotary encoder at pivot + 6-axis IMU on hull        | ±0.1 deg (encoder)     |
| Trim `ψ`       | 6-axis IMU on hull                                  | ±0.2 deg               |
| Heave / sinkage| Capacitive water-line staff or surveyed cameras     | ±2 mm                  |
| Time           | Common DAQ clock                                    | 1 ms across channels   |
| Arm geometry   | Surveyed once, recorded in hull frame               | ±1 mm pivot, ±1 mm tip |
| Pulley pose    | Surveyed once, recorded in world frame              | ±2 mm                  |

A six-axis load cell at the arm tip is optional and only worth its cost
if the off-axis components (transverse force, torsion in the arm) turn
out to be non-negligible during a pilot run. Start single-axis.

Sample rate: 100 Hz is sufficient for quasi-static sweeps and gives
clean low-pass-filtered traces; 1 kHz is fine if storage is cheap.

## Procedure

Each run produces one continuous sweep plus its calibration record.

1. **Static survey.** Photograph and measure the pivot and pulley in
   their respective frames. Record arm length and stiffness. Capture
   the upright waterline at the day's displacement and CG (paddler,
   ballast, sealed-deck or flooded-cockpit configuration). All of
   this becomes the fixture's `geometry_manifest`.
2. **Dead-weight calibration sweep.** With the rig disconnected from
   the hull, hang a sequence of known masses on the cable and record
   `F_measured` vs known force. Fit and store the gauge transfer
   function for this run. Repeat after the on-water sweep to bound
   drift.
3. **Forward sweep.** Apply force smoothly to heel the hull from
   upright through `GZ_max` and past `φ_v` to capsize-or-near-capsize.
   Sweep rate slow enough that `dθ/dt` is small relative to the
   hull's natural sloshing frequency; rule of thumb is 60 to 90 s from
   upright to `φ_v`. The operator should be able to pause at any
   angle without the trace drifting.
4. **Reverse sweep.** Release smoothly back through `φ_v` and `GZ_max`
   to upright. Hysteresis between forward and reverse legs is the
   primary quasi-static check: if it exceeds an accepted threshold
   (e.g. 3 % of `GZ_max`), the sweep was too fast or the rig is
   binding.
5. **Repeat.** At least three forward+reverse pairs per
   configuration to bound run-to-run scatter.

## Reduction

Per sample:

- correct `F_measured` through the dead-weight transfer function;
- compute the arm-tip position in world coordinates from the hull
  pose (encoder + IMU) and the surveyed pivot location;
- compute the line-of-action unit vector from arm tip to pulley;
- project `F_applied` onto the tangential direction to obtain
  `F_tangential` at the arm tip;
- compute `M_applied = F_tangential · L_arm`;
- divide by `Δ · g` to obtain `GZ(θ)`;
- bin to a regular `θ` grid for output, retaining standard deviation
  per bin across forward, reverse, and repeated sweeps.

Free-equilibrium check: trim and heave traces should follow smooth
curves consistent with the hull moving through static equilibria. If
trim oscillates or heave clamps at a fixed value, the rig is
constraining the hull and the result is not a free-hydrostatic GZ.

## Error budget

For an in-envelope sea kayak (`Δ` ≈ 100–130 kg with paddler,
`L_arm` ≈ 0.6–1.0 m, peak `F_applied` ≈ 50–150 N) the principal
contributors are:

| Source                          | Contribution to `GZ`      |
|---------------------------------|---------------------------|
| Load cell ±0.25 % FS            | ~0.5 % of `GZ_max`        |
| `L_eff(θ)` from geometry + θ    | ~1.0 % of `GZ_max`        |
| Δ uncertainty (mass + paddler)  | ~1.0 % of `GZ_max`        |
| Gauge drift between calibrations| ~0.5 % of `GZ_max`        |
| Quasi-static rate residual      | ~1.0 % of `GZ_max`        |
| **Combined (RSS)**              | **~2 % of `GZ_max`**      |

This is consistent with the findings memo's protocol-2 estimate
("0.5 deg, ~1-2 % GZ; clean to 90 deg") and an order of magnitude
better than protocol 1.

## What this rig cannot do

- It does not replace the RFC 0043 acceptance gates. A rig run on a
  hull whose generated closed body is not yet diagnosed cannot
  retroactively make that body's analytical `GZCurve` "calibrated."
  It only produces a measured `GZCurve` for the *physical* hull that
  was actually tested.
- It does not authorize a `calibrated_kayak_v1` resistance fixture
  (D006). Resistance and stability are independent gates.
- It does not measure dynamic response, surf, or paddler bracing.
- It cannot test a generated hull that has never been built. The
  comparison is `analytical(generated_body) vs measured(physical_boat)`
  for hulls where both exist.

## Cost and timeline

Per the findings memo's protocol-2 line: load cell + DAQ + encoder
+ rigging is $5–15 k in components, plus tank or pool time and
labor. Calendar 1–3 months to first valid run if a venue is
available. A university partnership (protocol 3) packages the
same rig under existing facility coverage and is the recommended
path if available.

## Open questions for review

- **Sealed-deck vs flooded-cockpit configuration.** Two distinct
  measured fixtures, or one fixture per (hull, configuration) pair?
  Recommended: one fixture per pair, configuration enumerated on the
  manifest.
- **Paddler CG convention.** Fixed ballast on the seat, instrumented
  paddler, or both? Recommended: fixed ballast for the first fixture
  to remove an active-control variable.
- **Inverted-rig extension to 90–180 deg.** Doable but doubles the
  rig complexity. Recommended: defer until `0–φ_v` is producing
  accepted fixtures.
- **Repeatable hull identity.** Hash a 3D scan of the tested hull
  and include it in the fixture, since manufacturer model name is
  not sufficient.

## Cross references

- `docs/research/CALIBRATION_DATA_FINDINGS_2026-05-16.md` — research
  context and the original protocol enumeration.
- `docs/rfcs/0050-strain-gauged-gz-rig.md` — fixture schema, gates,
  and integration with RFC 0043 claim semantics.
- `docs/rfcs/0011-hydrostatic-stability-load-cases.md` — mass and KG
  conventions the rig must record.
- `docs/rfcs/0014-generalized-trim-and-gz-stability.md` — `GZCurve`
  boundary.
- `docs/rfcs/0024-high-angle-gz-generated-body-handoff.md` — the
  generated-body handoff that any measured comparison binds against.
- `docs/rfcs/0043-high-angle-gz-successor.md` — analytical evaluator
  claim gates this rig is intended to validate.
- `docs/DECISION_LOG.md` D007 and D014 — the open measured-GZ gates.
