author: operator [self-declared: operator-0027-traceability]

# Workflow 0027 Traceability Review

Verdict intent: accept_with_findings

## Scope

This review maps workflow 0027 against the named source set: RFC 0004 exact
plumb-stem/end-cap deferrals, RFC 0006 validity constraints, RFC 0010 mesh
readiness/profile boundaries, RFC 0015 dispatch gating/raw-result wording, and
RFC 0016 acceptance criteria.

## Findings

### T-001 - RFC 0016 cannot land implementation before the plumb-stem/end-cap policy is explicit

RFC 0004 still marks exact non-zero endpoint area, explicit end-cap polygons,
and closed/watertight hull-plus-deck readiness as deferred. Its accepted safe
slice keeps `x = -L/2` as a zero-area closure point until a future end-cap
design lands. Current geometry implements that trace: `_end_decay()` returns
zero at the endpoints, `_get_slice_points()` only clamps local beam to a tiny
value, and `mesh()` lofts station strips without end-cap faces.

RFC 0016 correctly depends on "a decision on RFC 0004 plumb-stem and end-cap
semantics", and its implementation path makes closure policy decision step 1.
That dependency must remain a hard gate, not a documentation nicety.

Required action: before implementing generated closed-volume bodies, record the
canonical bow/stern cap policy in RFC 0016 or a referenced decision. It must
state whether plumb ends are true vertical faces, finite-area cap polygons,
zero-area parametric closure points plus separate caps, or another explicit
rule, and it must state how that policy maps to `bow_rake = 0.0`, `bow_rake =
1.0`, and intermediate values.

### T-002 - Closed-volume acceptance must remain separate from current mesh packages and STL surfaces

RFC 0010 and workflow 0024 intentionally keep current generated packages below
watertight `cfd_ready`: the open wetted-surface profile is
`cfd_surface_candidate`, while `watertight_solid_resistance_v1` requires closed
volume semantics. The current package writer emits separate hull/deck STL
surfaces and explicitly returns `stl_surface` for watertight-required profiles
with warnings about zero boundary edges, closed combined hull/deck volume, and
separate open surfaces.

RFC 0016 acceptance criteria align with this by requiring a closed-volume body
separate from current display meshes and mesh package surfaces. The
implementation must preserve that separation.

Required action: any landed 0027 code must introduce a distinct closed-volume
body/manifest/diagnostics boundary. Do not change `write_mesh_package()` so the
existing hull/deck package is marked `cfd_ready`, and do not satisfy RFC 0016 by
relabeling `open_wetted_surface_resistance_v1` artifacts.

### T-003 - RFC 0006 constraints are advisory today but still affect valid-body metadata

RFC 0006 adopts the constraints document as canonical for parameter space and
surface-level validity. Current `Hull` validation only enforces physical
positivity and `beam_wl_m <= beam_oa_m`; the wider class/design constraints
remain advisory. The constraints that matter for closed-volume traceability are
especially `B_wl < B_oa`, displacement at design waterline matching system
weight before CFD, Cp envelope, rocker ranges, LCB range, and the currently
unmodeled cross-section/deadrise/bilge-radius shape space.

Because RFC 0016 is a geometry contract rather than an optimizer or GUI lock,
it should not reject every out-of-class exploratory hull. But it must not hide
which canonical RFC 0006 constraints were enforced, advisory, or unsupported
when producing a closed body.

Required action: include a validity/advisory section in closed-volume metadata
or diagnostics that records at minimum enforced model checks, advisory RFC 0006
range warnings, unresolved unsupported shape parameters, and whether
displacement/system-weight matching was evaluated or left to a caller-supplied
load case.

### T-004 - RFC 0015 dispatch gating must remain based on named readiness, and outputs must stay raw/unvalidated

RFC 0015 landed only local dispatch. Current job records and run records carry
`result_semantics = raw_unvalidated`, and prepare rejects packages whose
manifest readiness is below the selected solver profile requirement. The
watertight solver profile requires `cfd_ready`, so current watertight-profile
packages are rejected because they remain `stl_surface`.

Workflow 0027 may create closed-volume diagnostics and possibly a future path
toward watertight readiness, but it does not validate CFD physics or add a real
solver adapter.

Required action: if 0027 wires a successful closed-volume diagnostic into mesh
or dispatch readiness, it must do so through a named profile transition and
tests proving the gate. CLI/status wording must continue to describe any CFD
job output as raw and unvalidated, with no calibrated drag, final design
fitness, or validated solver-result wording.

### T-005 - RFC 0016 can land serializable contracts and synthetic diagnostics now, but generated-body success depends on closure-policy resolution

RFC 0016 acceptance criteria that can land immediately are the closed-volume
body format, manifest serialization, diagnostics that reject open/nonmanifold
bodies, separation from display meshes, and synthetic fixtures for valid,
open, and nonmanifold bodies. The default generated hull can be evaluated for
closure diagnostics without changing STL export behavior, but a "valid default
generated closed body" should not be accepted until bow/stern caps, deck join,
sheerline, waterline handling, normal orientation, and signed-volume
tolerances are explicit.

Required action: split 0027 implementation evidence into two tiers: contract
and diagnostics may be accepted now; generated hull-plus-deck closed-body
success and any `cfd_ready` handoff remain blocked until the closure policy is
recorded and tested against generated geometry.

## Traceability Summary

Accept RFC 0016 as the correct successor contract only with the findings above.
It is traceable to the existing deferrals because it keeps open packages honest,
requires explicit closure metadata, and does not claim high-angle GZ, real CFD,
volume meshing, or validated solver output. The main risk is implementation
ordering: generated closed-body success must not precede the policy decision
that RFC 0004 and RFC 0016 both identify as deferred.
