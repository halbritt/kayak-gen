# SOURCES — 0043 RFC 0043 stage 4 stability-rig pipeline

Per-run context manifest. Required reading for every lane.

## RFCs

- `docs/rfcs/0043-high-angle-gz-successor.md` — stage-4 goal: flip the
  high-angle GZ `result_semantics` from
  `unvalidated_hydrostatic_comparison` to
  `validated_hydrostatic_comparison` once an accepted
  `measured_stability_fixture` exists and a strict-accepted
  `StabilityFitRecord` covers the hull. Read the stage-4 acceptance
  criteria first.
- `docs/rfcs/0056-strain-gauged-gz-rig.md` — defines
  `MeasuredStabilityFixture` schema (already landed schemas-only at
  `kayakgen/eval/stability/measured_fixture.py`). The pipeline this
  workflow builds consumes that schema; it does NOT redefine it.
- `docs/rfcs/0054-calibration-campaign-tooling.md` — the
  `kayakgen calibration` sub-app pattern your acceptance CLI mirrors.
  Read its `accept-fit` shape to understand the acceptance-gate
  vocabulary.
- `docs/rfcs/0027-resistance-calibration-acceptance.md` — the RFC 0027
  `SourceUse` acceptance pattern. The measured-stability acceptance
  gate mirrors this. Cross-reference required.
- `docs/rfcs/0025-cfd-calibration-claim-gates.md` — the claim-gate
  enforcement layer. Your claim-state resolution must respect this
  shape; do not invent a parallel gate.

## Code

### Already landed (read-only for this workflow)

- `kayakgen/eval/stability/measured_fixture.py` —
  `MeasuredStabilityFixture` Pydantic model + validators per RFC 0056.
  The pipeline consumes this; do NOT extend the schema in this
  workflow.
- `kayakgen/eval/stability/accepted_fit.py` — `StabilityFitRecord`,
  `StabilityFixturePromotionPacket`, `HullFamilyScope`, `FixtureRef`
  Pydantic schemas. RFC 0058 stage 1 contract.
- `kayakgen/eval/stability/registry.py` — the load-bearing 13-gate
  accepted-fit registry. `load_stability_fit_registry`,
  `fixture_canonical_sha256`, `REASON_NEXT_ACTION`,
  `ANALYTICAL_EVALUATOR_VERSION` (re-exported via
  `kayakgen.eval.stability.evaluator`). The CLI + web call sites + the
  evaluator all consume this; do NOT re-derive the hash or invent a
  parallel gate set.
- `kayakgen/eval/stability/high_angle_contracts.py` —
  `resolve_analytical_claim_label`; reads `getattr(hull, "hull_class",
  None)` + `hull.design_hash()` and flips `result_semantics` on a
  covered hull. Landed and correct.
- `kayakgen/eval/stability/evaluator.py` — the public `evaluate_gz_curve`
  entry; site 1 of the registry consumer. Already swapped to
  `_loaded_fit_registry()`. Do NOT touch.
- `kayakgen/eval/claims.py` — `ClaimState` literals, `SourceUse`
  vocabulary. Stage 4 introduces NO new literals.
- `kayakgen/eval/calibration/` — sibling calibration acceptance code.
  The stability pipeline lives in a sibling module; the
  `kayakgen calibration` sub-app stays resistance-only.
- `kayakgen/cli/main.py` — Typer sub-app registry that wires
  `kayakgen stability` (the canonical sub-app). The stability commands
  do NOT alias under `kayakgen calibration`.

### To add or extend (stage 4)

- `kayakgen/cli/stability_cli.py` — extends with `promote-fixture`
  (rewritten to write `promotion.json`, never mutate the manifest),
  `accept-fit` (new signature `--fit-record / --fixture-id / --out`;
  `--packet` REMOVED with a structured pointer), `claim-status` (new
  read-only resolver), and structured-JSON refusal lines for every
  gate the registry can emit.
- `kayakgen/ui/web/generate_frontier_view.py` +
  `kayakgen/ui/web/generate_spec_form.py` — replace
  `EMPTY_STABILITY_FIT_REGISTRY` with a lazy mtime-memoized
  `_loaded_fit_registry()` accessor mirroring the evaluator's pattern.
- `kayakgen/model/hull.py` — add `hull_class: str | None = None` so a
  real generated `Hull` can carry the calibration-envelope tag the
  resolver matches against. ``None`` is the safe default; the resolver
  keeps `None` hulls at `unvalidated_hydrostatic_comparison`.
- `tests/conftest.py` — lift the `(fixture, packet, fit)` triple
  factory from `tests/test_stability_fit_registry.py` as
  `make_stability_acceptance_triple` + `stage_acceptance_triple`.
- `tests/test_measured_stability_acceptance.py` — new; CLI gate refusals
  for `promote-fixture` + `accept-fit`.
- `tests/test_measured_stability_ingest.py` — new; canonical-manifest
  writer + immutability-after-promotion invariant.
- `tests/test_claim_state_measured_promotion.py` — new; end-to-end
  flip + memoization + env-var resolution + `claim-status` integration.
- `tests/test_cli_stability.py` — sweep to the new `accept-fit`
  signature and the structured-JSON refusal shape.
- `tests/test_resolve_analytical_claim_label.py` — add a
  production-path integration test that builds a real `Hull` (no
  `_HullWithScope` stub) and asserts the flip happens once the hull
  carries a real `hull_class` covered by an accepted fit.

### On-disk role line (new)

- `data/stability/fixtures/<fixture_id>/promotion.json` — the on-disk
  `AcceptedStabilityFixtureRecord`. The role is "acceptance record";
  the type is the existing `StabilityFixturePromotionPacket`. The
  registry loader uses `promotion.json` as the source of truth; the
  manifest's `intended_use` field is a hint only.

## Decision log rows

- `docs/DECISION_LOG.md` — read the D006 / D007 / D014 / D039 / D042
  rows for context on the physical rig + measurement campaign that
  gates acceptance and the stage-2/3 graduation contracts. The
  pipeline you build does NOT depend on those rows being closed; it
  depends on the RFC 0056 schema, which is landed.

## User-facing docs

- `docs/USER_GUIDE.md` — append the §E.2 stage-4 subsection ("Stage 4
  — accepted-fit registry and label flip") under the existing RFC 0058
  stability subsection. Document the three on-disk artifacts, the
  `claim-status` resolver, the `KAYAKGEN_STABILITY_FITS_ROOT` override,
  and the structured-JSON refusal shape.

## Out-of-scope reminders

- **No physical rig acquisition.** This workflow does not require
  measured rig data; it lands the pipeline that consumes such data
  when it arrives. D007 / D014 stay independent.
- **No flip of RFC 0043 / RFC 0056 Status.** Doc-only flip is a
  parent-agent commit after the full workflow converges.
- **No CFD or resistance subsystem touches.** This is the stability
  subdomain only.
- **No new `ClaimState` literal or `SourceUse` vocabulary.** Reuse the
  existing acceptance grammar.
- **No `kayakgen calibration` aliases for stability commands.** The
  `kayakgen stability` sub-app is the canonical surface; the prior
  obsolete `kayakgen calibration ingest-measured-stability` /
  `accept-measured-stability` lines and the `measured_acceptance.py`
  reference are dropped from this manifest.
- **No mutation of `intended_use` in place.** The manifest is
  immutable after ingest; acceptance is the separate
  `promotion.json` record.
- **No per-heel claim labels.** Partial heel-range acceptance flips
  hull-family-wide; per-heel is future RFC scope.
- **No index file or CFD-in-loop fit-record schema.** Scan-based
  registry + analytical-only flip in stage 4.
