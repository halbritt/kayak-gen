# RFC 0058 Stage 1 — Pinned Decisions

Stage 1 lands the Pydantic schemas and validators that RFC 0058 needs
to record stability-calibration fits. No fixture is promoted; no fit
is recorded; no claim label is changed. The schemas are docs-only
runtime: they exist so future stages can use them and so the test
suite can pin their shape.

| # | Decision | Implementing surface |
| --- | --- | --- |
| D-1 | Module path: `kayakgen/eval/stability/accepted_fit.py` (sibling to `measured_fixture.py` from RFC 0056). Tests at `tests/test_stability_accepted_fit.py`. | `implement_stability_fit_schemas` |
| D-2 | Five new Pydantic records, all `ConfigDict(extra="forbid")` and `schema_version: Literal["1"] = "1"`: `HullFamilyScope`, `StabilityFitMetrics`, `ReviewerSignature`, `StabilityFitRecord`, `StabilityFixturePromotionPacket`. | same |
| D-3 | `HullFamilyScope` carries `hull_class: str` (≥1 char) and an optional `design_hash_envelope: list[str]` of allowed `Hull.design_hash()` values. When the envelope is empty, the scope is rejected at validate time. | same |
| D-4 | `StabilityFitMetrics` carries `rmse_m: float ≥ 0`, `mape_fraction: float ≥ 0`, `max_error_m: float ≥ 0`, `coverage_fraction: float ∈ [0, 1]`. All four required. | same |
| D-5 | Default thresholds enforced at validation time on `StabilityFitRecord`: `rmse_m ≤ 0.005`, `mape_fraction ≤ 0.05`, `max_error_m ≤ 0.01`, `coverage_fraction ≥ 0.9`. Constants named `DEFAULT_STABILITY_FIT_RMSE_M`, `DEFAULT_STABILITY_FIT_MAPE_FRACTION`, `DEFAULT_STABILITY_FIT_MAX_ERROR_M`, `DEFAULT_STABILITY_FIT_COVERAGE_FRACTION`. A `--strict` boolean field on `StabilityFitRecord` (default `True`) gates threshold enforcement; setting it `False` skips the check (and records `strict_check_skipped` in `warnings`). | same |
| D-6 | `ReviewerSignature` carries `reviewer_label: str`, `reviewer_role: str`, `signed_at: datetime`. No personally-identifying info beyond what the reviewer chooses to put in the label. | same |
| D-7 | `StabilityFitRecord` carries: `fit_id: str`, `analytical_evaluator_version: str`, `hull_family_scope: HullFamilyScope`, `valid_heel_range_deg: tuple[float, float]` (low<high), `fixtures: list[FixtureRef]` (≥1, see D-8), `fit_metrics: StabilityFitMetrics`, `acceptance_verdict: Literal["accepted", "rejected"]`, `rejection_reasons: list[str]` (must be empty when verdict=accepted), `reviewer_signature: ReviewerSignature`, `accepted_at: datetime \| None` (must be set when verdict=accepted), `notes: list[str]`, `warnings: list[str]`. | same |
| D-8 | `FixtureRef` is a new value object on the module: `fixture_id: str`, `fixture_path: str`, `fixture_sha256: str` (64 lowercase-hex chars). Validators check the SHA-256 shape; existence-on-disk is NOT checked here (defer to a later stage when fixture promotion lands). | same |
| D-9 | `StabilityFixturePromotionPacket` carries: `fixture_ref: FixtureRef`, four review verdicts (`rights_review`, `hull_identity_review`, `calibration_drift_review`, `hysteresis_review`, `free_equilibrium_review`) each `Literal["accepted", "rejected", "deferred"]`, `rig_design_match: bool`, `promotion_target: Literal["measured_stability_fixture", "validation_candidate", "rejected"]`, `rejection_reasons: list[str]`, `reviewer_signature: ReviewerSignature`. A validator refuses `promotion_target=measured_stability_fixture` unless every review verdict is `"accepted"` AND `rig_design_match=True` AND `rejection_reasons=[]`. | same |
| D-10 | No fixture or fit is promoted by this RFC. The first concrete promotion happens in a later workflow once a real measured dataset arrives. The schemas exist only so the test surface can pin them. | same |
| D-11 | `resolve_analytical_claim_label(hull, fit_registry)` and `cfd_in_loop_evaluator_status(...)` are **stage 2** scope (not in this stage). This stage is pure data records. | same |
| D-12 | Docs sync updates: `CHANGELOG.md`, `docs/DECISION_LOG.md` (new D038 row), `docs/ROADMAP.md` (add a "Stability calibration acceptance" track row), `docs/rfcs/0058-stability-calibration-acceptance.md` (status: `landed (schemas only)`), `docs/rfcs/README.md` (status update). | `synchronize_docs` |

## Out of scope (deferred)

- The `kayakgen stability` CLI sub-app (stage 2).
- The analytical-claim upgrade contract (`resolve_analytical_claim_label`) — stage 2.
- The CFD-in-loop graduation contract (`cfd_in_loop_evaluator_status`) — stage 2.
- Frontier-view colour-mapping for validated points — stage 3.
- Form-builder evaluator-block hiding the CFD-in-loop ack when graduated — stage 3.

## Blocked items (remain blocked)

- Real fixture/fit promotion: gated on physical rig data (D007/D014).
- RFC 0043's analytical `GZCurve` claim label: stays
  `unvalidated_hydrostatic_comparison` until a `StabilityFitRecord` exists for
  the hull family.
- Safety, seaworthiness, calibrated, final-prediction, design-fitness
  claims: forbidden as always; the schemas explicitly cannot upgrade
  to these labels.
