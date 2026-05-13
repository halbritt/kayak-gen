author: operator [self-declared: operator-domain-review]

# Domain review - equilibrium stability semantics

Verdict intent: accept_with_findings

## Findings

### D-001 - Full trim equilibrium is under-specified by the current load case

RFC 0011 says equilibrium should solve sinkage and trim together, but
`LoadCase` has no longitudinal center of gravity, cargo location, paddler
station, or moment target. The current lofted hull is also symmetric enough that
a centered load implies zero trim by construction, not by a general trim solve.

Required action: implement a truthful safe slice: solve sinkage/displacement
equilibrium now, report trim as zero only for the centered/symmetric assumption,
and emit an explicit warning that generalized trim requires longitudinal load
inputs and trimmed-volume hydrostatics.

### D-002 - KG references must be normalized at the equilibrium draft

Waterline-relative KG currently normalizes against `hull.draft_m`. In an
equilibrium pass, the operating draft can differ from the design draft, so using
the design draft would move KG by the same amount as the sinkage correction.

Required action: compute `kg_above_keel_for_draft()` with the equilibrium draft
when evaluating equilibrium GM0.

### D-003 - Load-case water density is ignored by hydrostatic mass

`LoadCase` carries `seawater_density_kg_m3`, but `evaluate_hydrostatics()`
returns displaced mass using the module constant. Equilibrium matching should
honor the load-case density when comparing displacement to load mass.

Required action: either add density support to hydrostatics or compute
equilibrium displaced mass from displaced volume and the load-case density in
the stability layer, preserving legacy hydrostatics behavior for existing
callers.

### D-004 - Convergence failure needs an explicit status and warning

A too-heavy load can exceed the hull's supported draft range. Without a
bounded failure mode, callers could confuse a best-effort draft with a valid
equilibrium result.

Required action: expose converged vs not-converged status, tolerance, iteration
count, and warnings such as load outside bracket or max iterations exceeded.

### D-005 - Nick Schade explainer remains non-normative

The external stability explainer helps frame KG/CB/righting-arm concepts, but it
does not supply a numerical validation dataset for this hull generator.

Required action: keep documentation language contextual and avoid adding
calibration/validation claims from that source.
