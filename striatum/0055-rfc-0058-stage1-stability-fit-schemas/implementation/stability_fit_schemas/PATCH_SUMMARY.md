author: implementer-codex-gpt-5.5-001

# Patch Summary

Implemented RFC 0058 stage 1 stability-fit schemas under
`kayakgen/eval/stability/accepted_fit.py`.

## Changes

- Added threshold constants:
  `DEFAULT_STABILITY_FIT_RMSE_M`,
  `DEFAULT_STABILITY_FIT_MAPE_FRACTION`,
  `DEFAULT_STABILITY_FIT_MAX_ERROR_M`, and
  `DEFAULT_STABILITY_FIT_COVERAGE_FRACTION`.
- Added `FixtureRef` with a strict 64-character lowercase SHA-256 validator.
- Added the five stage-1 Pydantic records:
  `HullFamilyScope`, `StabilityFitMetrics`, `ReviewerSignature`,
  `StabilityFitRecord`, and `StabilityFixturePromotionPacket`.
- Added validators for non-empty hull-family design-hash envelopes,
  ordered heel ranges, accepted-fit metadata, strict metric thresholds,
  `strict=False` warning recording, and promotion-packet refusal when
  any review verdict is not accepted.
- Added focused tests in `tests/test_stability_accepted_fit.py` covering
  canonical JSON round-trip, threshold enforcement with `strict=True` and
  `strict=False`, promotion-packet refusal paths, and FixtureRef SHA-256
  shape validation.

## Verification

- `.venv/bin/python -m pytest tests/test_stability_accepted_fit.py tests/test_measured_stability_fixture.py -q`
- `.venv/bin/python -m ruff check kayakgen tests`
