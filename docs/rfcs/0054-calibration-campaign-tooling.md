# RFC 0054: Calibration-Campaign Tooling

Status: proposed
Date: 2026-05-16
Context: Phase 8 item 5 of
`ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`. RFCs 0042 / 0027
land the *acceptance* gates for a calibration fixture; D006 + D013
keep promotion blocked because no in-envelope measured kayak source
exists. The research finding 2026-05-16
(`docs/research/CALIBRATION_DATA_FINDINGS_2026-05-16.md`) names
"commissioned pool/tank inclining campaign" as the realistic next
action. This RFC scopes the on-disk schemas + ingestion tooling
that such a campaign would need.

## Problem

If kayakgen operators (or a partnering university lab) commission a
real campaign — towing-tank drag, inclining-experiment GZ, calibration
fits — there is no kayakgen-side schema today for the ingest. The
operator would have to invent the row shapes, the manifest format,
the rights checklist, and the uncertainty fields, and reverse-
engineer the validators against existing fixture conventions.

## Goals

- Land tank-test and inclining-test ingest schemas as Pydantic
  records under `kayakgen/eval/calibration/`.
- Land a raw-measurement ingester that produces a
  `ResistanceSourceReviewPacket`-compatible artifact from a CSV +
  hull-CAD pair.
- Land an "accepted-fit" record schema that satisfies the D006
  calibration_fixture gate (validity envelope, fit metrics,
  residuals, immutable model version).
- Land a residual plot artifact format (SVG; same writer family as
  RFC 0051).

## Non-Goals

- No actual measurement campaign (that's an operational decision).
- No new claim state.
- No remote ingest service.
- No real-time data acquisition wiring.
- No automatic promotion of any source to `calibration_fixture` from
  a CSV alone; the accepted-fit gate stays explicit (D006).

## Proposal

### Schemas

```python
class TankTestRun(BaseModel):
    schema_version: Literal["1"] = "1"
    source_id: str
    hull_design_hash: str  # RFC 0049 vocabulary
    speed_ms: float = Field(ge=0)
    total_drag_n: float
    drag_uncertainty_n: float | None
    trim_deg: float
    sink_mm: float
    water_temperature_c: float
    notes: list[str] = Field(default_factory=list)

class TankTestCampaign(BaseModel):
    schema_version: Literal["1"] = "1"
    source_id: str
    rights_checklist: RightsChecklist  # existing-style
    geometry_reference: GeometryReference  # CAD / offsets ref
    rows: list[TankTestRun]
    uncertainty_method: Literal["Type_A_repeatability", "Type_B_uncertainty_budget", "documented_caveat"]

class IncliningTestRun(BaseModel):
    schema_version: Literal["1"] = "1"
    source_id: str
    hull_design_hash: str
    heel_deg: float
    applied_moment_nm: float
    applied_moment_uncertainty_nm: float | None
    sealed_body: bool
    cockpit_flooded: bool
    paddler_state: Literal["absent", "rigid_manikin", "active_paddler"]
    notes: list[str] = Field(default_factory=list)
```

### Acceptance gate

A new `AcceptedFitRecord` schema:

```python
class AcceptedFitRecord(BaseModel):
    schema_version: Literal["1"] = "1"
    fit_id: str
    model_version: str  # immutable
    fit_metric: Literal["RMSE", "MAPE", "R2"]
    fit_value: float
    holdout_rms_n: float
    residuals: list[tuple[float, float]]  # (operating point, residual)
    validity_envelope: dict[str, tuple[float, float]]
    accepted_at: str  # ISO-8601
    accepted_by: str  # operator id
```

A `ResistanceSourceReviewPacket` with `review_verdict ==
"calibration_fixture"` requires `accepted_fit_ref` to match an
`AcceptedFitRecord` on disk; the validator (already partially in
`kayakgen.eval.calibration`) gains a strict-resolve check.

### CLI

```bash
kayakgen calibration ingest-tank-test campaign.csv \
    --hull hull.json \
    --rights-checklist rights.json \
    --out fixtures/tank-test/<source_id>/

kayakgen calibration ingest-inclining-test runs.csv \
    --hull hull.json --out fixtures/inclining/<source_id>/

kayakgen calibration accept-fit <fixture-id> \
    --fit fit.json --out fixtures/calibration/<fixture-id>/accepted_fit.json
```

Each writes the appropriate schema artifact + a checksum manifest.

### Residual plots

`kayakgen calibration residual-plot <accepted-fit> --out residuals.svg`
writes an SVG with the per-operating-point residual stems plus a
zero-line.

## Acceptance Criteria

- Tank-test and inclining-test ingest writes the documented schemas
  byte-stably across two invocations.
- `kayakgen calibration accept-fit` refuses to land an
  `AcceptedFitRecord` whose `fit_metric` is below the operator-
  configured threshold (default RMSE <= 5% of measured baseline).
- A `ResistanceSourceReviewPacket` with `review_verdict ==
  "calibration_fixture"` and a valid `accepted_fit_ref` passes the
  existing validator chain.
- Default `kayakgen evaluate`, `compare`, `search` outputs unchanged.

## Open Questions

- Does the `RightsChecklist` schema live alongside the campaign
  schema or in `kayakgen/eval/calibration/rights.py`?
- Should hull geometry binding be by hash, by CAD-file path, or both?
- Default `fit_metric`: `RMSE`, `MAPE`, or operator's choice?

## Implementation Path

1. Define the three new Pydantic schemas in
   `kayakgen/eval/calibration/campaigns.py`.
2. Land the four `kayakgen calibration ...` Typer subcommands.
3. Wire `AcceptedFitRecord` into the existing
   `_validate_calibration_fixture_metadata` chain.
4. Land residual-plot SVG writer in
   `kayakgen/services/calibration_artifacts.py`.
5. Update `docs/USER_GUIDE.md`.

## Domain Modeling

`TankTestCampaign`, `IncliningTestRun`, and `AcceptedFitRecord` are
new aggregate roots (each has identity, lifecycle, and invariants
distinct from the Hull). They live under
`kayakgen.eval.calibration.campaigns`. The existing
`ResistanceSourceReviewPacket` aggregate gains a binding to
`AcceptedFitRecord` via `accepted_fit_ref`.
