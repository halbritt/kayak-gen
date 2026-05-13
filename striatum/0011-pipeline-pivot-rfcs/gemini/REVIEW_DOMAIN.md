# Domain/math/mesh review - RFCs 0009-0013

author: operator
Verdict recommendation: accept_with_findings

The RFC direction is sound, but several domain contracts need tightening before
the drafts can safely guide implementation. The main risks are mesh readiness
semantics, load-case reference frames, resistance provenance, and Pareto ranking
over exploratory resistance.

## Findings

### F-DOM-001 - Blocker - `cfd_ready` is untestable without a solver profile

RFC 0010 defines `cfd_ready` as passing a selected solver profile's strict
contract, but no profile schema exists. Add `MeshSolverProfile` fields such as
`profile_name`, `requires_watertight`, `accepted_parts`, `normal_orientation`,
`waterline_boundary_policy`, tolerances, and nonmanifold limits. Current output
must not emit `cfd_ready` without a named profile.

### F-DOM-002 - High - Mesh diagnostics must include tolerance-based geometry

The current mesh builder emits independent station-ring vertices and clamps
near-zero local beam. Raw edge incidence alone will miss coincident or
near-coincident defects. Diagnostics should report both raw and tolerance-welded
boundary/nonmanifold counts and detect collapsed station rings.

### F-DOM-003 - High - Bow-positive axis direction cannot remain open

The mesh manifest should declare bow/stern and flow direction. Add `bow_x`,
`stern_x`, and `flow_direction` so future asymmetric/plumb geometry and CFD
handoff have a stable convention.

### F-DOM-004 - Blocker - Load cases do not define displacement equilibrium

RFC 0011 defines mass but does not decide whether stability solves for load
waterline or reports design-waterline diagnostics. Add a human-decision boundary
or v1 output fields `load_mass_kg`, `displaced_mass_kg`, and
`displacement_error_kg` with warnings.

### F-DOM-005 - Blocker - `kg_above_waterline_m` conflicts with current GM formula

Current `GM0_m` subtracts `0.25` as if KG is measured from the keel/baseline.
If the RFC field means above waterline, the formula changes. Rename the field to
a baseline-referenced value or defer waterline-referenced KG behind a human
decision.

### F-DOM-006 - High - `GZCurve` cannot be the top-level stability result

`GZCurve` cannot carry load case, method status, warnings, or not-implemented
provenance. Introduce `StabilityResult` with optional nested `gz_curve`, and
change `EvaluationResult.stability` to that type.

### F-DOM-007 - High - Resistance wording mixes verification and calibration

The current code says the Michell prefactor is calibrated against Wigley, while
RFC 0012 says no canonical calibration dataset has been chosen. Distinguish
`verification_fixture` from `calibration`, and mark current raw output as not
kayak-calibrated.

### F-DOM-008 - High - Raw resistance validity ranges are not declared

Current raw curves need metadata and warnings even before calibration exists.
Add `ResistanceMetadata` with model family, accepted use, calibration status,
quadrature settings, raw validity envelope or no-envelope warning, and warnings.

### F-DOM-009 - Blocker - Pareto defaults can optimize exploratory resistance

RFC 0013 should not default to primary frontiers over raw uncalibrated
resistance. Add objective provenance/accepted-use requirements, or label such
reports as exploratory and require opt-in.

### F-DOM-010 - Medium - Sweep records need evaluator provenance

Candidate records should include evaluator settings and versions: load case,
water density, mesh profile, resistance quadrature/model metadata, warnings, and
diagnostics version.

## Human decisions required

- CFD mesh readiness semantics: watertight solid vs open wetted-surface
  profiles.
- Coordinate convention: bow-positive axis and flow direction.
- Stability KG reference frame.
- Whether load cases solve displacement or report design-waterline diagnostics.
- Raw resistance validity ranges and Wigley verification/calibration wording.
- Whether default Pareto reports may include exploratory resistance objectives.
