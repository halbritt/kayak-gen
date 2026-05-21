# Implementation Prompt

Read the packet objective, write scope, and:

- `docs/workflows/0055-rfc-0058-stage1-stability-fit-schemas/STAGE_1_DECISIONS.md`
- `docs/rfcs/0058-stability-calibration-acceptance.md`
- `kayakgen/eval/stability/measured_fixture.py` (RFC 0056 sibling pattern)

Implement only the assigned slice. The schemas + validators are pure
Pydantic — no I/O, no fixture promotion, no claim-state changes.

Requirements:

- Stay strictly inside the allowed paths.
- All five new Pydantic records use `ConfigDict(extra="forbid")` and
  `schema_version: Literal["1"] = "1"`.
- Default thresholds (D-5) are module-level constants, prefixed
  `DEFAULT_STABILITY_FIT_*`, and enforced via a `model_validator(mode="after")`
  on `StabilityFitRecord` that respects the `strict: bool` field.
- `StabilityFixturePromotionPacket`'s validator refuses
  `promotion_target="measured_stability_fixture"` unless every review
  verdict is `"accepted"`, `rig_design_match=True`, and
  `rejection_reasons=[]`.
- `FixtureRef.fixture_sha256` regex-checks for 64 lowercase-hex chars.
- Tests in `tests/test_stability_accepted_fit.py` cover: schema
  round-trip for every record; threshold enforcement (each metric
  above and below bound, strict=True vs False); promotion-packet
  refusal paths (one per review-verdict field); FixtureRef SHA-256
  shape rejection.
- Run `.venv/bin/python -m ruff check kayakgen/eval/stability/accepted_fit.py
  tests/test_stability_accepted_fit.py` and `.venv/bin/python -m pytest
  tests/test_stability_accepted_fit.py -q` before publishing the patch
  summary. Both must be clean.
- Do not start real fixture promotion, fit acceptance, or any change to
  RFC 0043's `result_semantics` literal. The label stays
  `unvalidated_hydrostatic_comparison` for analytical `GZCurve` output.

Publish the required patch summary artifact (see `expected_artifacts`)
with the exact Striatum front matter and byline.
