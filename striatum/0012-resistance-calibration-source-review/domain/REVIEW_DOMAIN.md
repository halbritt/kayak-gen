# Domain review - 0012

author: operator [self-declared: operator-domain-review]
run: run_b8d2bd2b94f345c1a30521671cf0ba67
job: review_domain
verdict: accept_with_findings

## Summary

The reviewed sources can support validation and guardrails, but none is a
defensible general calibration anchor for touring/sea-kayak resistance.

## Findings

### D-001 - Sprint K1 data are measured but too narrow

- Severity: high
- Sources: Gomes et al.; Tzabiras et al.
- Statement: K1 tow/passive-drag data provide measured kayak resistance over
  useful speed bands, but the hulls are sprint race craft with narrow geometry,
  different load cases, and high-Froude behavior relative to touring sea
  kayaks.
- Required action: Use K1 studies as validation/holdout cases only until the
  project has a sprint-specific calibration profile.

### D-002 - Sea-kayak tables are class-relevant but model-derived

- Severity: high
- Sources: Sea Kayaker / KAPER / Broze-Taylor tables.
- Statement: These tables cover the right hull class and speeds, but using them
  for calibration would mostly tune the current analytical model toward another
  empirical/model prediction surface.
- Required action: Do not label output calibrated from these tables alone.

### D-003 - Calibration source requirements need to be explicit

- Severity: medium
- Statement: A future accepted source must carry enough hull/load/speed context
  to map data to `Hull` inputs and Froude/slenderness validity ranges.
- Required action: Add a source requirement checklist to RFC 0012 and any
  calibration registry.

## Gate recommendation

Accept the review with findings. Do not create `calibrated_kayak_v1` yet.
Create explicit validation-source categories and keep Pareto defaults blocked
on calibrated resistance.
