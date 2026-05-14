# FINDINGS - workflow 0035 high-angle GZ generated-body handoff

Verdict intent: accept_with_findings

This ledger consolidates the traceability, domain, and ops review artifacts for
workflow 0035. The gate is open for a conservative RFC 0024 implementation
slice, but not for broad user-facing secondary-stability claims.

The safe slice is contract-first: generated-body validation, structured
unavailable results, fixture-only labeling, JSON/schema hardening, and tests.
Real kayak high-angle GZ values remain gated on generated closed-body
diagnostics and unresolved policy decisions.

## Inputs read

- `AGENTS.md`
- `docs/workflows/0035-high-angle-gz-generated-body-handoff/SOURCES.md`
- `docs/workflows/0035-high-angle-gz-generated-body-handoff/workflow.json`
- `docs/workflows/0035-high-angle-gz-generated-body-handoff/prompts/findings_ledger.md`
- `striatum/0035-high-angle-gz-generated-body-handoff/traceability/REVIEW_TRACEABILITY.md`
- `striatum/0035-high-angle-gz-generated-body-handoff/domain/REVIEW_DOMAIN.md`
- `striatum/0035-high-angle-gz-generated-body-handoff/ops/REVIEW_OPS.md`
- The RFCs, evaluator sources, CLI source, and tests listed by `SOURCES.md`
- On-demand GZ exposure surfaces: `kayakgen/eval/contract.py`,
  `kayakgen/search/sweep.py`, `kayakgen/search/compare.py`,
  `kayakgen/ui/web/app.py`, and `tests/test_generated_closed_body.py`

No product code, RFC, changelog, root operator report, workflow metadata, or
Striatum state was changed by this ledger role.

## Helper passes

Three independent read-only helper passes were used before consolidation:

- A traceability pass compared the three review artifacts against RFC 0014,
  RFC 0016, RFC 0020, and RFC 0024.
- A domain pass checked body-reference semantics, generated/synthetic body
  boundaries, heel-grid assumptions, summary metrics, and fixture-only labels.
- An ops pass checked JSON compatibility, unavailable behavior, CLI/sweep/UI
  hiding, comparison leakage, and validation expectations.

The helpers were instructed not to write files and not to run Striatum
commands. Their outputs were used only as consolidation inputs; this ledger was
written in the main ledger role.

## Gate verdict

Proceed to implementation with findings.

The workflow scaffold and RFC inputs are coherent enough to send to the
implementation lane. The review findings are implementation, schema, warning,
surface, and test gaps. They do not require an RFC or workflow repair before
the next lane starts.

The implementation lane must not treat this verdict as approval to display
fixture, open-mesh, CFD-package, or unlabeled generated-body output as real
kayak high-angle stability.

## Deduplicated findings

### F-001 - High - `evaluate_gz_curve` still has no RFC 0024 handoff boundary

RFC 0024 requires `evaluate_gz_curve(hull, load_case, heel_grid_deg, body_ref)`
to emit real kayak GZ only when `body_ref` resolves to a generated closed body
whose diagnostics pass. Current code still exposes the old reserved boundary:
`kayakgen/eval/stability.py:501` accepts arbitrary args and raises
`GZNotImplementedError` mentioning `closed_volume_body_not_defined`.

Required action:

- Add the RFC 0024 evaluator boundary with explicit hull, load case, requested
  heel grid, and body reference inputs.
- Return structured unavailable output for missing, unsupported, synthetic,
  failed, mismatched, or unresolvable bodies instead of a blanket
  not-implemented raise.
- Emit `generated_closed_body_not_available` or a more specific
  diagnostic-derived warning at the GZ boundary.
- Echo `heel_grid_deg` exactly and keep computed `heel_deg` separate from the
  requested grid.
- Add a machine-readable availability/status field either on the GZ read model
  or the adjacent result envelope, because RFC 0024 requires an unavailable
  status.

Existing upright and trim stability warnings such as
`high_angle_gz_not_implemented` remain truthful for current non-GZ paths, but
the GZ evaluator boundary itself must move to generated-body wording.

Review sources: traceability F1/F2, domain findings 1-4, ops high finding,
helper traceability/domain/ops passes.

### F-002 - High - `GZCurve` cannot carry RFC 0024 provenance or summaries

The current `GZCurve` model in `kayakgen/eval/contract.py:109` contains only
`angles_deg` and `gz_m`. It cannot serialize the RFC 0024 contract:
`body_ref`, `body_type`, `body_diagnostic_ref`, `heel_grid_deg`, `heel_deg`,
`righting_moment_nm`, `max_gz_m`, `heel_at_max_gz_deg`,
`range_positive_stability_deg`, `area_under_positive_gz_m_deg`,
`assumptions`, and `warnings`.

The residual `Hydrostatics.gz_curve` field in
`kayakgen/eval/hydrostatics.py:31` is also an unsafe legacy surface. It has no
body provenance, diagnostic reference, fixture-only label, or warnings.

Required action:

- Extend or replace the GZ read model with the RFC 0024 fields and strict JSON
  round-trip tests.
- Add explicit availability/provenance fields so a curve cannot be interpreted
  as real kayak stability unless its generated-body evidence is present.
- Quarantine, remove, or migrate `Hydrostatics.gz_curve` deliberately. Old JSON
  with `hydrostatics.gz_curve: null` should remain compatible if possible, but
  non-null legacy curves must not be promoted to real GZ.
- Do not silently upgrade old minimal `GZCurve(angles_deg, gz_m)` data into
  real secondary-stability output.

Review sources: traceability F3/F5, ops high finding, helper ops/domain
passes.

### F-003 - High - Generated and synthetic closed-body gates are not wired into stability

Closed-volume code now distinguishes
`explicit_synthetic_triangle_mesh` from
`generated_hull_plus_deck_closed_body` and can diagnose generated bodies, but
stability code does not consume `ClosedVolumeBody` or
`ClosedVolumeDiagnostics`.

Required action:

- Validate that real kayak GZ body references resolve to generated closed
  bodies, not display meshes, mesh packages, CFD case directories, or
  synthetic explicit bodies.
- Require matching `source_hull_hash`, coordinate system, units, closure
  policy, tolerances, positive signed volume, zero boundary/nonmanifold edges,
  and passed self-intersection diagnostics before any real generated-body GZ
  values are emitted.
- Return unavailable output with warnings and `None` summary metrics when any
  generated-body diagnostic gate fails.
- Enforce `fixture_only` at the evaluator/result-construction boundary for
  synthetic explicit bodies. Synthetic math fixtures may test the righting-arm
  math, but they must not satisfy generated kayak `body_ref` requirements.

Review sources: traceability F1/F4, domain findings 1/5, ops high finding,
helper domain pass.

### F-004 - Medium - Sweep, comparison, CLI, and UI need explicit GZ claim guards

Current public surfaces mostly hide high-angle GZ: the CLI stability command
emits only initial/equilibrium stability, sweep summaries omit secondary
stability fields, and the web UI says "High-angle GZ unavailable." That is the
correct current behavior.

The risk is future leakage. `CandidateRecord.summary` is an arbitrary dict in
`kayakgen/search/sweep.py:96`, and comparison promotes every finite numeric
summary key in `kayakgen/search/compare.py:213`. Arbitrary objective names are
accepted by `parse_objective` in `kayakgen/search/compare.py:94`. A future
fixture-only `max_gz_m`, `heel_at_max_gz_deg`, or
`area_under_positive_gz_m_deg` field could become a comparison objective
unless GZ metrics are explicitly provenance-gated.

Required action:

- Do not put unavailable or fixture-only numeric GZ metrics into public sweep
  summaries or `summary.csv`; status and warning fields are acceptable.
- Add comparison gating so GZ-like objective metrics require accepted
  generated-body provenance and are warned/excluded when fixture-only,
  unavailable, or unlabeled.
- Keep CLI and UI surfaces in unavailable/warning mode until the generated-body
  handoff is available for real curves.
- Add negative tests with crafted records containing GZ-like numeric fields.

Review sources: ops medium finding, traceability F7, helper traceability/ops
passes.

### F-005 - Medium - High-angle GZ test coverage is absent

Existing tests cover load-case serialization, initial stability, upright
equilibrium, trim behavior, old high-angle not-implemented behavior, and
closed-volume diagnostics. They do not cover the RFC 0024 high-angle contract.

Required action:

- Test missing body refs, open display/CFD refs, synthetic refs used as real,
  failed closure diagnostics, self-intersection failures, hull-hash mismatches,
  and generated-body diagnostic success/failure boundaries.
- Test that unavailable output has canonical warnings, no synthetic GZ values,
  exact heel-grid echo, empty or absent computed values, and `None` summary
  metrics.
- Test finite monotonic heel-grid validation and same-length arrays for
  computed fixture output.
- Test deterministic synthetic fixture math, summary derivation only from
  computed `gz_m`, and mandatory `fixture_only` labeling.
- Test per-heel non-convergence or missing heel-point warnings before any
  partial curve can be consumed.
- Test JSON round trips for the extended GZ model and compatibility behavior
  for old null legacy surfaces.

Review sources: traceability F6, ops medium finding, helper ops pass.

## Conservative implementation slice

Implementers may do the following in this workflow:

1. Add the RFC 0024 `evaluate_gz_curve` boundary and result contract.
2. Add generated-body validation against the existing closed-volume body and
   diagnostic models.
3. Return structured unavailable GZ results with generated-body warnings and
   `None` summary metrics when gates fail.
4. Add `fixture_only` synthetic math fixtures that prove heel-grid handling and
   summary derivation without claiming kayak stability.
5. Add JSON-compatible extended GZ fields and compatibility guards for legacy
   null or minimal curve surfaces.
6. Add sweep/comparison/CLI/UI hiding and provenance gates so fixture-only or
   unavailable values cannot become public secondary-stability claims.
7. Add the focused tests listed in this ledger.

This slice should be small enough to review as an RFC 0024 handoff and safety
contract. It should not introduce broad new stability physics beyond the
fixture-only math needed to test the contract.

## Explicit deferrals

The implementation lane must defer:

- real user-facing generated-kayak high-angle GZ curves unless every
  generated-body diagnostic gate passes and the unresolved policy choices below
  are pinned in code and tests;
- per-heel trim solving versus fixed upright trim as a general policy;
- CG fixed-to-hull versus fixed-to-world behavior beyond explicit recorded
  assumptions;
- deck inclusion, deck immersion, cockpit/flooding warning semantics, and
  paddler/body-volume modeling;
- interpolation policy for `range_positive_stability_deg`;
- any CFD-ready, solver-ready, watertight-solid, or dispatchable claim from
  generated closed-body diagnostics;
- optimization, Pareto ranking, or design-fitness use of secondary-stability
  metrics;
- validation against measured kayak stability data.

Safe wording for implementation artifacts is "GZ unavailable",
"generated closed-body diagnostic gate", "fixture_only math fixture", and
"secondary-stability metrics hidden until generated-body handoff passes."
Avoid "real stability", "kayak stability curve", or "comparison-ready GZ" for
fixture or unavailable output.

## Validation expectations

Before the implementation lane hands off to final review, it should run the
focused unit tests it adds plus the existing relevant suites, at minimum:

- `tests/test_stability.py`
- `tests/test_closed_volume.py`
- `tests/test_generated_closed_body.py`
- comparison/sweep tests covering crafted GZ-like summary metrics
- CLI/UI tests or static assertions proving unavailable GZ is not rendered as
  secondary-stability numbers

The final review should reject the patch if any of these are true:

- an open mesh, CFD package, synthetic body, or unlabeled legacy curve can
  produce real kayak GZ;
- fixture-only output appears in public sweep summaries, comparison objectives,
  CLI output, or UI stability claims;
- unavailable output contains numeric GZ values or non-`None` summary metrics;
- result JSON lacks body provenance, diagnostic reference, requested heel grid,
  assumptions, warnings, or availability status;
- generated-body diagnostics are treated as CFD-ready or solver-ready.

## Preservation notes

- Current display STL and mesh-package surfaces remain open/inspection
  artifacts.
- Current generated closed-body diagnostics are evidence for closed-volume
  evaluation only; they are not CFD readiness.
- Existing initial/equilibrium stability results remain useful and should keep
  their current method/status semantics.
- Existing high-angle unavailable UI copy is acceptable until a later verified
  generated-body GZ slice replaces it.
