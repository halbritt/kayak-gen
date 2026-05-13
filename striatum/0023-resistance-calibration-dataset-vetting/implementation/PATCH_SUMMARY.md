# Patch summary - resistance dataset vetting

author: operator [self-declared: operator-implementer]
run: run_6ca2095f019345e199943d5f46f0676f
job: implement_findings
date: 2026-05-13

## Scope implemented

- Added `edinburgh_pacific_canoe_hydrodynamics` to
  `default_resistance_source_registry()` as a `validation_candidate`.
- Recorded CC BY 4.0 DataShare provenance, DOI-derived rights status, and
  explicit warnings that the dataset is not a sea-kayak calibration fixture.
- Extended focused resistance tests to assert the Edinburgh record is measured,
  validation-only, and not a `calibration_fixture`.
- Updated RFC 0012 and the RFC index to state that an open measured validation
  source exists, while calibrated kayak resistance remains blocked.

## Scope intentionally not implemented

- No numeric rows were extracted from the workbook.
- No fixture ingestion schema was added.
- No current resistance curve metadata was changed.
- No sweep, comparison, or Pareto defaults were changed.

## Sub-agent use

No implementation sub-agents were spawned for this patch. The useful write
scope was one registry record, one focused test, and two docs updates; splitting
that would have added coordination without a disjoint implementation surface.

## Verification

- `.venv/bin/python -m pytest tests/test_resistance.py -q` -> 12 passed.
- `.venv/bin/python -m pytest -q` -> 147 passed.
- `striatum --repo . doctor` -> clean.
- `git diff --check` -> clean.
