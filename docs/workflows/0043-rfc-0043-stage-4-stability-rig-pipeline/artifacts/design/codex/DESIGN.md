author: designer-codex-gpt-5.5-001

# Codex Design: Measured-Stability Stage-4 Promotion

## Position

Use the RFC 0058 stability path as canonical. `kayakgen stability` already owns
rig-run ingest, fixture promotion, accepted-fit records, residual plots, and
the `resolve_analytical_claim_label` / `cfd_in_loop_evaluator_status` pattern.
Stage 4 should harden that path from schema-only to real registry-backed
promotion. `kayakgen calibration` may expose aliases for operator discovery,
but no duplicate state or second acceptance grammar should exist.

## A. CLI Shape

Canonical commands:

```bash
kayakgen stability ingest-rig-run <fixture.json> \
  --out data/stability/fixtures/<fixture_id>

kayakgen stability promote-fixture <fixture_id> \
  --packet <promotion_packet.json>

kayakgen stability accept-fit <fit_record.json> \
  --packet <promotion_packet.json>

kayakgen stability residual-plot <fit_record.json> --out <fit_id>.svg
```

Optional compatibility aliases under `kayakgen calibration`:

```bash
kayakgen calibration ingest-measured-stability <fixture.json> --out <dir>
kayakgen calibration accept-measured-stability <fixture_id> \
  --rig-source-review <promotion_packet.json>
```

The aliases call the same functions as `kayakgen stability`; they do not write a
separate calibration registry.

Ingest output:

- `data/stability/fixtures/<fixture_id>/manifest.json`: canonical
  `MeasuredStabilityFixture.model_dump_json(indent=2)`.
- `data/stability/fixtures/<fixture_id>/ingest.json`: small sidecar
  `{schema_version, fixture_id, source_path, manifest_path, manifest_sha256,
  ingested_at, stage_label: "candidate_run"}`.

The manifest carries RFC 0056 fields verbatim: `fixture_id`, `title`,
`source_citation`, `source_url`, `rights`, `extraction_method`,
`hull_identity`, `configuration`, `loading`, `measured_quantity`, `heel_units`,
`arm_units`, `valid_heel_range_deg`, `rig_design_ref`,
`geometry_manifest_ref`, `calibration_trace`, `free_equilibrium_trace`,
`hysteresis_bound`, `rows`, `runs_dir`, `intended_use`,
`non_promotion_reasons`, and `warnings`.

Accepted fit output:

```json
{
  "schema_version": "1",
  "fit_id": "stability-fit-001",
  "kind": "analytical",
  "analytical_evaluator_version": "rfc-0043-generated-body-v1",
  "hull_family_scope": {"hull_class": "sea kayak", "design_hash_envelope": ["design-hash-001"]},
  "valid_heel_range_deg": [0.0, 70.0],
  "fixtures": [{"fixture_id": "...", "fixture_path": "...", "fixture_sha256": "..."}],
  "fit_metrics": {"rmse_m": 0.0, "mape_fraction": 0.0, "max_error_m": 0.0, "coverage_fraction": 1.0},
  "acceptance_verdict": "accepted",
  "rejection_reasons": [],
  "reviewer_signature": {"reviewer_label": "...", "reviewer_role": "...", "signed_at": "..."},
  "accepted_at": "...",
  "notes": [],
  "warnings": []
}
```

This is `StabilityFitRecord` plus a Stage-4 registry discriminator `kind`. It
differs from RFC 0054 `AcceptedFitRecord` by binding a measured GZ fixture,
an analytical evaluator version, a hull-family/design-hash envelope, a heel
range, and `(theta, GZ)` error metrics. It is not a resistance model-version
fit and it does not authorize final prediction.

## B. Acceptance Gates

Fixture promotion to `measured_stability_fixture` requires:

- RFC 0056 schema validation succeeds: rights present, 64-char hull scan hash,
  calibration trace present and within drift bound, free-equilibrium trace
  present, hysteresis observed value within bound, rows inside
  `valid_heel_range_deg`, and no constrained trim/heave for promotion.
- Promotion packet verdicts `rights_review`, `hull_identity_review`,
  `calibration_drift_review`, `hysteresis_review`, and
  `free_equilibrium_review` are all `"accepted"`.
- `rig_design_match == true`, `rejection_reasons == []`, fixture id/path match
  the manifest, and packet fixture SHA-256 matches the canonical manifest.
- RFC 0027 pattern is preserved: promotion is review-driven, not caused by
  loading rows. Candidate and validation-only data do not promote a model.
- RFC 0025 claim gates are preserved: no safety, seaworthiness, calibrated
  model, final prediction, or design-fitness wording is permitted.

Fit acceptance additionally requires:

- Every cited fixture resolves to `intended_use == "measured_stability_fixture"`.
- `analytical_evaluator_version` matches the runtime RFC 0043 evaluator version.
- The accepted fit's `valid_heel_range_deg` is inside the fixture and evaluator
  converged range.
- Default strict metrics pass: `rmse_m <= 0.005`, `mape_fraction <= 0.05`,
  `max_error_m <= 0.01`, `coverage_fraction >= 0.9`.
- The output path `data/stability/fits/<fit_id>.json` does not already exist.

Structured refusal:

```json
{
  "ok": false,
  "code": "calibration_drift_above_bound",
  "fixture_id": "msf-2026-001",
  "details": {"observed": 0.012, "bound": 0.005},
  "next_action": "rerun the dead-weight calibration review or keep the fixture as validation_candidate"
}
```

Stable codes: `fixture_schema_invalid`, `fixture_sha256_mismatch`,
`rights_review_not_accepted`, `hull_identity_review_not_accepted`,
`rig_design_mismatch`, `calibration_drift_above_bound`,
`hysteresis_above_bound`, `free_equilibrium_not_accepted`,
`constrained_trace_blocks_promotion`, `outside_stability_envelope`,
`fixture_not_promoted`, `evaluator_version_mismatch`,
`valid_heel_range_not_covered`, `stability_fit_metrics_outside_default_thresholds`,
and `fit_id_already_exists`.

Partial acceptance exists only as explicit bounds: `valid_heel_range_deg` and
`hull_family_scope.design_hash_envelope`. Inside both, a curve may use the
validated label. Outside either, it stays unvalidated and carries
`valid_stability_fit_not_found` or `requested_heel_range_outside_validated_range`.

## C. Claim-State Resolution

Do not add a `ClaimState` literal. `measured_validated` would duplicate RFC
0058's result-label contract and weaken RFC 0025's calibrated-model gates.

The promoted high-angle surface is:

- fixture artifact: `MeasuredStabilityFixture.intended_use =
  "measured_stability_fixture"`;
- fit artifact: `StabilityFitRecord.acceptance_verdict = "accepted"`;
- generated-body GZ output: `result_semantics` flips from
  `unvalidated_hydrostatic_comparison` to
  `validated_hydrostatic_comparison`.

Add `StabilityFitRegistry.load(data/stability/fits/index.json)`. The CLI writes
immutable fit JSON and updates the index with `{fit_id, kind, path, sha256,
hull_class, design_hash_envelope, valid_heel_range_deg}`. Library evaluators
accept an explicit registry object; they do not scan global paths at import.
CLI/web entry points load the index once and pass it to
`resolve_analytical_claim_label`.

UI propagation mirrors RFC 0058:

- `kayakgen stability --high-angle-gz` JSON records `result_semantics`,
  `validated_by_fit_ids`, and `validation_fixture_ids`.
- Sweep high-angle artifacts use the same block; high-angle metrics remain
  display-only and frontier-ineligible.
- Web frontier points keep the existing `kg-state-validated` /
  `kg-state-raw` mapping.
- Generate-panel CFD-in-loop becomes `first_class` only when the registry has
  both covering `kind="analytical"` and covering `kind="cfd_in_loop"` accepted
  fits, and persistent operator opt-out is not false.
- Desktop remains minimal unless it consumes a high-angle JSON block; no default
  desktop stability claim changes.

## D. Test Surface

- `test_ingest_measured_stability_writes_canonical_manifest_and_index`: happy
  path ingest, canonical JSON, SHA sidecar.
- `test_ingest_measured_stability_refuses_invalid_fixture_schema`: bad RFC 0056
  manifest fails without writing.
- `test_promote_fixture_refuses_sha_mismatch`: packet hash must bind manifest.
- `test_promote_fixture_refuses_unaccepted_review_verdicts`: parameterized over
  rights, hull identity, calibration drift, hysteresis, free equilibrium.
- `test_promote_fixture_refuses_rig_design_mismatch`.
- `test_promote_fixture_refuses_constrained_trace`.
- `test_accept_fit_refuses_unpromoted_fixture`.
- `test_accept_fit_refuses_evaluator_version_mismatch`.
- `test_accept_fit_refuses_heel_range_outside_fixture`.
- `test_accept_fit_refuses_default_metric_failures`: RMSE, MAPE, max error,
  coverage.
- `test_high_angle_gz_result_semantics_flips_with_indexed_accepted_fit`:
  integration test from accepted registry to `GeneratedBodyGZCurve`.
- `test_high_angle_gz_result_semantics_stays_unvalidated_outside_scope`.
- `test_generate_panel_first_class_requires_analytical_and_cfd_fit`.

## E. Operator Copy

`kayakgen calibration --help` additions:

```text
Commands:
  ingest-measured-stability   Validate an RFC 0056 measured-stability fixture and write canonical manifest JSON.
  accept-measured-stability   Apply a stability promotion review packet to a fixture manifest.
```

Failure copy examples:

- `accept-measured-stability refused: hysteresis_above_bound; rerun the sweep more slowly or keep the fixture as validation_candidate`
- `accept-fit refused: valid_heel_range_not_covered; choose a heel range covered by both the fixture and the analytical evaluator`

USER_GUIDE subsection:

````markdown
### Measured stability fixtures

Measured-stability fixtures are strain-gauged high-angle GZ rig runs for a
specific physical hull and loading configuration. Ingest validates the RFC 0056
manifest and stores a canonical candidate. Promotion requires a review packet
that accepts rights, hull identity, rig design, calibration drift, hysteresis,
and free-equilibrium evidence. An accepted fixture still does not change
generated-body GZ output until an accepted stability fit covers the evaluated
hull family and heel range.

```bash
kayakgen stability ingest-rig-run run.json --out data/stability/fixtures/msf-2026-001
kayakgen stability promote-fixture msf-2026-001 --packet promotion_packet.json
kayakgen stability accept-fit stability_fit.json --packet promotion_packet.json
kayakgen stability residual-plot data/stability/fits/stability-fit-001.json --out residuals.svg
```
````

## F. Open Questions

- Whether Stage 4 should formalize `kind` on `StabilityFitRecord` or keep it as
  index metadata until the CFD-in-loop fit record lands.
- Whether `StabilityFitRegistry` should tolerate missing `index.json` by
  scanning `data/stability/fits/*.json`; I prefer no fallback in library code
  and an explicit `kayakgen stability rebuild-fit-index` operator command.
- Whether `strict=false` should ever be accepted for Stage-4 promotion. I would
  allow it only for `acceptance_verdict="rejected"` records; accepted records
  should pass strict thresholds.
