author: operator [self-declared: operator-domain-review]

# Domain review - generalized trim and GZ stability

Verdict intent: accept_with_findings

RFC 0014 is directionally sound, and the current implementation remains safe
because generalized trim is not claimed and high-angle GZ still raises an
explicit not-implemented error. The accepted implementation slice needs tighter
domain contracts before it emits trim or any righting-arm curve values.

## Findings

### D-001 - Trim sign is not yet a domain contract

RFC 0014 preserves the RFC 0010 longitudinal convention: `+x` is stern/aft and
`-x` is bow/forward. It also says a forward LCG must produce bow-down trim and
an aft LCG must produce stern-down trim, but it does not define the numeric sign
of `trim_angle_deg`.

With the current coordinate system, a negative load LCG should move the
buoyancy LCB negative by immersing the bow, and a positive load LCG should move
the buoyancy LCB positive by immersing the stern. That expectation is safe only
if the result contract says whether positive trim means stern-down/bow-up or
bow-down/stern-up.

Required action: define `trim_angle_deg` sign in RFC/code comments/result
metadata before emitting nonzero trim. Prefer one explicit convention, for
example `trim_angle_deg > 0` means stern-down/bow-up, which implies forward LCG
tests assert negative trim and aft LCG tests assert positive trim. Add tests
that sample `x_m < 0` as bow/forward and `x_m > 0` as stern/aft so symmetry
cannot hide a sign inversion.

### D-002 - Load components need mass-weighted LCG/KG semantics

RFC 0014 introduces `LongitudinalLoadComponent`, but current `LoadCase` still
has only compact paddler/hull/cargo mass fields and one aggregate KG. That is
not enough to represent a paddler forward of midship, aft cargo, hull mass
center, or mixed KG assumptions.

The domain model should make the normalized computation inputs explicit:
component mass, `x_m`, and keel-referenced KG. Total load mass is the sum of
component masses. Load LCG is `sum(mass_kg * x_m) / total_mass_kg`. Load KG is
mass-weighted over component KGs after reference normalization. If a compact
legacy field is accepted, the generated compatibility components must carry
named assumptions rather than silently inventing a longitudinal moment.

Required action: add component normalization as a value-object operation on
`LoadCase`. Record the default paddler, hull, and cargo stations and KG
fallbacks in assumptions/warnings. Reject negative masses and nonfinite
positions. For zero total mass, return a validation error rather than a trim
result.

### D-003 - Moment balance must use signed LCB in meters, not only `LCB_frac`

RFC 0014's trim equilibrium is a two-equation solve: displaced mass equals load
mass, and displaced longitudinal moment equals load longitudinal moment. The
current hydrostatics read model exposes only `LCB_frac`, while RFC 0014 needs
`buoyancy_lcb_m` in the same signed coordinate frame as component `x_m`.

The moment equation may use kg*m because gravitational acceleration cancels for
static balance, but the sign must remain consistent: load moment is
`sum(mass_kg * x_m)`, and buoyancy moment is `displaced_mass_kg *
buoyancy_lcb_m`. At convergence, `buoyancy_lcb_m` should match `load_lcg_m`
within the stated moment tolerance.

Required action: expose signed `LCB_m`/`buoyancy_lcb_m` in trim results and use
it for residual reporting. Keep `LCB_frac` for compatibility, but do not derive
moment sign from the fraction without converting back to signed meters relative
to midship.

### D-004 - Generalized trim requires fixed-body volume integration

`evaluate_equilibrium_stability()` currently solves sinkage by bisection over
`Hull(draft_m=...)`. That was an acceptable centered-load safe slice, but it is
not a valid template for generalized trim because it changes the generated hull
shape instead of immersing a fixed hull body under a shifted and rotated
waterplane.

For a forward LCG, bow-down trim should increase immersed bow volume and move
LCB forward on the same hull. For an aft LCG, stern-down trim should do the
opposite. Mutating `draft_m` cannot represent that longitudinal redistribution,
and the current open hull surface is not enough to integrate arbitrary heeled or
trimmed displacement.

Required action: implement trim solving against a named evaluation body clipped
by an upright-but-trimmed waterplane, or explicitly defer nonzero trim. The
solver must not extend the current draft-parameter bisection into a claimed
trim solve. Keep legacy equilibrium-sinkage output compatible while labeling it
as centered-load/sinkage-only.

### D-005 - Convergence tolerances need separate mass and moment residuals

Current equilibrium reports mass residuals and iteration counts, but RFC 0014
adds longitudinal moment residuals. A single kg tolerance cannot certify trim.
The result must distinguish mass convergence from moment convergence, and
non-convergence must be visible to CLI, sweep, and JSON consumers.

For kayak-scale comparisons, a default mass tolerance around 0.1-1.0 kg is
domain-credible for fast screening. Moment tolerance should be explicit in
kg*m, preferably tied to load scale or waterline length rather than hidden in
solver internals. Returning `status="converged"` with a small mass residual but
a large moment residual would be a false stability claim.

Required action: add `moment_error_kg_m`, a moment tolerance, convergence
status, iteration count, and warnings for mass out of bracket, moment out of
bracket, max iterations, degenerate waterplane/body, and trim-angle bounds. If
not converged, nullable fields such as `trim_angle_deg` and `buoyancy_lcb_m`
should either be absent/null or clearly marked as best-effort diagnostics.

### D-006 - High-angle GZ is not safe until the closed-volume body is named

The design constraints correctly require secondary stability from an actual GZ
curve, and the PRD keeps full GZ in scope. RFC 0014 also correctly gates real
GZ values on a named closed-volume model. The current code is safe because
`evaluate_gz_curve()` raises `GZNotImplementedError` and tests assert that no
placeholder curve is emitted.

No high-angle GZ values are safe now. The current hull/deck meshes are display
surfaces, and RFC 0014 has not chosen hull-only, hull-plus-deck, or a separate
evaluation body. The current `GZCurve` model in `contract.py` is also too small
for RFC 0014 because it lacks righting moment, maximum GZ, range of positive
stability, assumptions, and warnings.

Required action: keep high-angle stability unavailable with a named reason such
as `closed_volume_body_not_defined`. Before any real GZ values are emitted,
land the closed-body decision, expand the `GZCurve` contract to the RFC 0014
shape, specify fixed-paddler-CG behavior, and test that unsupported bodies still
return unavailable/not-implemented rather than synthetic righting arms.

## Required Gate

Proceed to ledger with generalized trim as an implementation candidate only
after the trim sign, component normalization, fixed-body volume, and residual
tolerance contracts are recorded. High-angle GZ must remain unavailable unless
the closed-volume decision lands in the same workflow with tests.
