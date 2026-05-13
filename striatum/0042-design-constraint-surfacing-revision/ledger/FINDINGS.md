# Findings - workflow 0042 design constraint surfacing revision

## Ledger Verdict

Verdict intent: accept with implementation-required findings.

RFC 0031 is the conservative implementation target for workflow 0042. It
supersedes RFC 0029 only for this implementation slice, preserves RFC 0006's
advisory posture, and must not change geometry, solver, calibration,
closed-volume, high-angle stability, optimizer, or layout semantics
(`docs/rfcs/0031-design-constraint-surfacing-revision.md:55`,
`docs/rfcs/0031-design-constraint-surfacing-revision.md:61`,
`docs/rfcs/0031-design-constraint-surfacing-revision.md:41`).

This ledger deduplicates:

- Traceability review findings F1-F5
  (`striatum/0042-design-constraint-surfacing-revision/traceability/REVIEW_TRACEABILITY.md:170`).
- Ops review findings F-OPS-001 through F-OPS-004
  (`striatum/0042-design-constraint-surfacing-revision/ops/REVIEW_OPS.md:9`).
- Domain review confirmation that RFC 0031 is domain-correct if it stays within
  enforced/advisory/unsupported semantics and avoids false precision
  (`striatum/0042-design-constraint-surfacing-revision/domain/REVIEW_DOMAIN.md:7`).

## Implementation-Required Findings

### F-001 - Add one shared design-validity model and evaluator

Implement `kayakgen/model/validity.py` with `DesignValidityFinding`,
`DesignValidityReport`, and `evaluate_design_validity(...)` near the
model/evaluator boundary (`docs/rfcs/0031-design-constraint-surfacing-revision.md:160`).

Required record fields are `code`, `level`, `severity`, `message`, `source`,
and `parameters`; optional fields may include `value`, `bounds`,
`selected_class`, and `surface`
(`docs/rfcs/0031-design-constraint-surfacing-revision.md:66`). The finding
model must tolerate unknown future optional fields, while top-level serializers
should add explicit defaulted fields so old records without `design_validity`
still load (`docs/rfcs/0031-design-constraint-surfacing-revision.md:78`,
`striatum/0042-design-constraint-surfacing-revision/ops/REVIEW_OPS.md:15`).

Each finding must pin `source` to an explicit constraints-document section or
RFC reference, not a generic document pointer
(`striatum/0042-design-constraint-surfacing-revision/traceability/REVIEW_TRACEABILITY.md:172`).
Minimum source mapping:

- `L/B_wl`: `docs/design/kayak_hull_design_constraints.md` section 4
  (`docs/design/kayak_hull_design_constraints.md:90`).
- Displacement sanity: constraints section 7
  (`docs/design/kayak_hull_design_constraints.md:179`).
- `Cp`: constraints section 8
  (`docs/design/kayak_hull_design_constraints.md:202`).
- Class/default envelope guidance: constraints sections 3, 4, and 9 as
  applicable (`docs/design/kayak_hull_design_constraints.md:52`,
  `docs/design/kayak_hull_design_constraints.md:222`).
- Unsupported reserved controls: RFC 0031 plus the relevant `Hull` fields
  (`docs/rfcs/0031-design-constraint-surfacing-revision.md:93`,
  `kayakgen/model/hull.py:58`).

### F-002 - Preserve existing advisory strings while adding structured records

`design_advisory()` may become a wrapper over the new evaluator, but
`DesignAdvisory.warnings` must continue to return the existing warning strings
for current callers (`docs/rfcs/0031-design-constraint-surfacing-revision.md:102`,
`kayakgen/model/advisory.py:15`, `kayakgen/model/advisory.py:25`).

The structured advisory families for the first pass are the existing
`L/B_wl`, `Cp`, and displacement bands already represented in
`kayakgen/model/advisory.py:46`, `kayakgen/model/advisory.py:51`, and
`kayakgen/model/advisory.py:56`, plus selected-class drift when a selected
class is explicitly known (`docs/rfcs/0031-design-constraint-surfacing-revision.md:89`,
`docs/rfcs/0031-design-constraint-surfacing-revision.md:91`).

### F-003 - Define unsupported neutral sentinels for reserved controls

Unsupported does not mean invalid. It means a value is accepted for schema
continuity or future work, but is not a full geometry or evaluation control
yet (`docs/rfcs/0031-design-constraint-surfacing-revision.md:98`).

For this slice, neutral reserved values are:

- `LCB_frac == 0.50`
- `rocker_bow_m == 0.0`
- `rocker_stern_m == 0.0`

Any non-neutral value for those fields should emit an `unsupported` record until
the field is fully honored by geometry or evaluation
(`striatum/0042-design-constraint-surfacing-revision/traceability/REVIEW_TRACEABILITY.md:187`,
`kayakgen/model/hull.py:58`). Do not emit unsupported records for neutral
defaults unless a surface would otherwise imply the control is fully honored
(`docs/rfcs/0031-design-constraint-surfacing-revision.md:154`).

### F-004 - Propagate additive metadata through all required serialization boundaries

Wire the shared report through every RFC 0031 first-pass surface
(`docs/rfcs/0031-design-constraint-surfacing-revision.md:112`):

- `EvaluationResult`, which is currently strict and has no design-validity
  field (`kayakgen/eval/contract.py:281`, `kayakgen/eval/contract.py:284`).
- `kayakgen evaluate` JSON (`kayakgen/cli/main.py:66`,
  `kayakgen/cli/main.py:76`).
- Web evaluation payloads, with `EvaluationResult.design_validity` as the
  canonical structured REST/CLI payload target
  (`kayakgen/ui/web/controllers.py:287`,
  `kayakgen/ui/web/controllers.py:927`,
  `striatum/0042-design-constraint-surfacing-revision/ops/REVIEW_OPS.md:21`).
- Completed sweep candidate records (`kayakgen/search/sweep.py:95`,
  `kayakgen/search/sweep.py:242`, `kayakgen/search/sweep.py:287`).
- Comparison candidate summaries/reports and report-level warning counts
  (`kayakgen/search/compare.py:30`, `kayakgen/search/compare.py:48`,
  `kayakgen/search/compare.py:171`).

Advisory and unsupported findings must not change CLI exit behavior for valid
hulls, candidate status, sweep completion, Pareto eligibility, or comparison
ranking (`docs/rfcs/0031-design-constraint-surfacing-revision.md:108`,
`docs/rfcs/0031-design-constraint-surfacing-revision.md:121`,
`striatum/0042-design-constraint-surfacing-revision/ops/REVIEW_OPS.md:11`).

### F-005 - Derive desktop and web design-warning text from shared records

Desktop and web warning text must come from the same shared codes/messages for
equivalent hulls (`docs/rfcs/0031-design-constraint-surfacing-revision.md:136`).
Current desktop text is built directly from `advisory.warnings`
(`kayakgen/ui/desktop.py:321`, `kayakgen/ui/desktop.py:359`), while web compact
metrics and analysis helpers separately expose or combine advisory and
resistance warnings (`kayakgen/ui/web/controllers.py:96`,
`kayakgen/ui/web/controllers.py:125`, `kayakgen/ui/web/controllers.py:170`,
`kayakgen/ui/web/app.py:221`).

Implementation should keep visible design-warning text derived from
`design_validity` and may render resistance/calibration/CFD warnings nearby,
but those warning streams must remain separate
(`striatum/0042-design-constraint-surfacing-revision/traceability/REVIEW_TRACEABILITY.md:202`).

### F-006 - Keep selected-class drift explicit and optional

Class drift should be evaluated only when a surface supplies a selected class.
Do not infer a selected class from `Hull.name` or from automatic classification
(`docs/rfcs/0031-design-constraint-surfacing-revision.md:157`,
`striatum/0042-design-constraint-surfacing-revision/ops/REVIEW_OPS.md:27`).

`evaluate_design_validity(..., selected_class=None)` should not emit class-drift
records. Preset defaults must remain advisory-quiet
(`docs/rfcs/0031-design-constraint-surfacing-revision.md:142`,
`tests/test_classes.py:86`). Add one explicit selected-class drift test.

### F-007 - Preserve enforced validation authority

Existing enforced model constraints remain enforced by `Hull` validation or live
UI clamping, with CLI validation as the final authority
(`docs/rfcs/0031-design-constraint-surfacing-revision.md:125`).

Do not loosen Pydantic validation, do not turn `beam_wl_m > beam_oa_m` into an
advisory, and do not require duplicating every Pydantic error as structured
metadata in this slice (`docs/rfcs/0031-design-constraint-surfacing-revision.md:85`,
`kayakgen/model/hull.py:73`, `tests/test_classes.py:57`,
`tests/test_sweep.py:55`). Web live clamping should remain a pre-validation UI
behavior, not the authoritative model rule (`kayakgen/ui/web/controllers.py:50`,
`tests/test_web.py:120`).

## Non-Blocking Preservation Notes

- Preserve existing hydrostatics, resistance, stability, and evaluation keys;
  `design_validity` is additive and must not replace existing read models
  (`striatum/0042-design-constraint-surfacing-revision/traceability/REVIEW_TRACEABILITY.md:231`).
- Keep design-validity records distinct from resistance calibration warnings,
  CFD readiness warnings, solver dispatch state, and claim-gate warnings
  (`striatum/0042-design-constraint-surfacing-revision/traceability/REVIEW_TRACEABILITY.md:202`,
  `docs/USER_GUIDE.md:304`, `docs/USER_GUIDE.md:359`).
- Preserve the PRD and User Guide boundary: current hydrostatics are integrated
  geometry readouts, resistance is an exploratory analytical screening filter,
  and local CFD support is job/run/profile plumbing rather than real solver
  execution (`docs/PRD.md:39`, `docs/PRD.md:40`, `docs/PRD.md:42`,
  `docs/USER_GUIDE.md:3`).
- Advisory records are user guidance only. They are not proof of seaworthiness,
  race performance, final design fitness, calibrated resistance, or CFD validity
  (`docs/rfcs/0031-design-constraint-surfacing-revision.md:50`,
  `docs/PRD.md:51`, `docs/USER_GUIDE.md:388`).
- Preserve RFC 0006 as partial. Closing this workflow does not close all RFC
  0006 desktop acceptance criteria or future shape-parameter work
  (`docs/rfcs/0006-design-constraints.md:15`,
  `docs/rfcs/0006-design-constraints.md:202`,
  `striatum/0042-design-constraint-surfacing-revision/traceability/REVIEW_TRACEABILITY.md:218`).
- The comparison/Pareto layer may summarize warning counts and records, but
  objective warnings and accepted-use provenance remain separate from
  design-validity records (`kayakgen/search/compare.py:99`,
  `kayakgen/search/compare.py:135`).

## Explicit Deferrals

The implementation agent should not include these in the RFC 0031 slice:

- RFC 0006 yellow dismissible desktop banner UX and manual desktop visual
  confirmation (`docs/rfcs/0006-design-constraints.md:170`,
  `docs/rfcs/0006-design-constraints.md:202`).
- Desktop or web layout redesign
  (`docs/rfcs/0031-design-constraint-surfacing-revision.md:49`).
- Full rocker geometry, deadrise, chine radius, flare, section archetype
  controls, or full `LCB_frac` volume redistribution
  (`docs/rfcs/0031-design-constraint-surfacing-revision.md:43`,
  `docs/design/kayak_hull_design_constraints.md:124`,
  `docs/design/kayak_hull_design_constraints.md:159`).
- High-angle `GZ`, secondary-stability curves, and final capsize-range
  stability claims (`docs/USER_GUIDE.md:133`, `docs/USER_GUIDE.md:400`).
- Calibrated resistance prediction, final design-fitness claims, resistance
  claim-gate rewrites, or optimizer warning penalties
  (`docs/rfcs/0031-design-constraint-surfacing-revision.md:46`,
  `docs/rfcs/0031-design-constraint-surfacing-revision.md:48`,
  `docs/PRD.md:56`).
- CFD readiness semantics, closed-volume solver dispatch, real OpenFOAM/SU2 or
  hosted solver adapters, and constraints-document section 10 CFD objective
  closure (`docs/rfcs/0031-design-constraint-surfacing-revision.md:46`,
  `docs/design/kayak_hull_design_constraints.md:244`,
  `striatum/0042-design-constraint-surfacing-revision/traceability/REVIEW_TRACEABILITY.md:231`).
- Automatic class inference or broad classification UX beyond explicit
  selected-class drift (`docs/rfcs/0031-design-constraint-surfacing-revision.md:157`).

## Conservative Safe Implementation Slice

1. Add `kayakgen/model/validity.py` with tolerant finding/report models, stable
   codes/messages, explicit source references, and `evaluate_design_validity(...)`.
2. Convert or wrap `design_advisory()` so current warning strings remain
   compatible while the structured findings become the shared source of design
   warning text.
3. Add defaulted additive `design_validity` fields at strict serialization
   boundaries: `EvaluationResult`, completed `CandidateRecord`s,
   `CandidateSummary`, and `ComparisonReport`.
4. Wire `kayakgen evaluate` and `evaluation_payload()` through
   `EvaluationResult.design_validity`; let compact web metrics and analysis view
   helpers render design warning messages from the same report.
5. Update desktop/web helper paths so equivalent hulls share the same
   design-warning codes and messages. Keep resistance and CFD warnings separate.
6. Extend sweeps and comparison reports with per-candidate records and warning
   counts without changing candidate status, sweep failure behavior, Pareto
   eligibility, or objective ranking.
7. Add unsupported records for non-neutral `LCB_frac`, `rocker_bow_m`, and
   `rocker_stern_m`; leave neutral defaults quiet.
8. Add focused tests for schema compatibility, advisory parity, source pins,
   class defaults, selected-class drift, invalid-beam enforcement,
   advisory-not-failure behavior, sweep/report propagation, and unsupported
   reserved fields.

Suggested test anchors include `tests/test_classes.py:74`,
`tests/test_web.py:80`, `tests/test_sweep.py:55`, `tests/test_compare.py:29`,
and `tests/test_hull_roundtrip.py`.

