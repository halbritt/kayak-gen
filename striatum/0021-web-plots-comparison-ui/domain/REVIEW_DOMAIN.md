author: operator [self-declared: operator-domain-review]

# Domain review - plots and comparison semantics

Verdict intent: accept_with_findings

## Findings

### D-001 - Resistance views must preserve uncalibrated/exploratory status

`kayakgen.eval.resistance` explicitly labels Michell+ITTC output as
`comparative_filter_only`, not final performance prediction. RFC 0013 also
excludes raw resistance from default Pareto objectives.

Required action: any resistance plot/table must show units and warnings, and
any report with `report_kind == "exploratory_frontier"` must make that label
visible.

### D-002 - Pareto displays need objective-aware labels

`ComparisonReport.objectives` names metrics and directions, while
`pareto_front_keys` marks non-dominated candidates. A generic "best" label
would hide the objective set and could mislead users when only GM0 is available
or when explicit exploratory resistance objectives are used.

Required action: show objective metric/direction labels and Pareto membership
separately. Do not rank or recommend candidates beyond the report data.

### D-003 - Failed and skipped candidates must remain visible

RFC 0013 requires missing metrics and invalid candidates to be warnings, not
crashes. Current comparison tests preserve failed/skipped candidates and warn
that they are not eligible for Pareto membership.

Required action: display failed/skipped candidates with status, warnings, and
errors rather than filtering them out.

### D-004 - Plot units and axes must be explicit

Hydrostatics and resistance values mix kg, square meters, meters, knots, Froude
number, and Newtons. The current metrics panel uses text labels; new plot/table
views should keep that clarity.

Required action: label resistance speed in knots and resistance in Newtons;
label hydrostatic quantities with units; keep dimensionless values such as Cp,
Cm, and Fn clearly separate.

## Required gate

Proceed to ledger. The safe domain slice is read-only visualization and report
inspection with candidate reload only if the state mapping is explicit and
tested.
