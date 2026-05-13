# Patch summary - 0012

author: operator [self-declared: operator-implementer-temp]
run: run_b8d2bd2b94f345c1a30521671cf0ba67
job: implement_findings

## Scope

Implemented the safe fallback from the 0012 ledger. No numeric calibration was
added and no source was promoted to `calibrated_kayak_v1`.

## Findings addressed

- F-001: no extracted published tables were checked into the repo.
- F-002/F-003: RFC 0012 now records that Sea Kayaker-derived tables are
  citation-only/model-to-model context and Gomes/Tzabiras K1 studies are
  validation candidates, not general sea-kayak calibration anchors.
- F-004: RFC 0012 now requires explicit source/provenance acceptance before a
  dataset can become a calibration fixture.
- F-005: `ResistanceMetadata` now has optional calibration/provenance fields:
  name, version, Froude/slenderness validity ranges, source citation, source
  license, and extraction method.
- F-006: added `kayakgen.eval.calibration` with structured
  `ResistanceSourceRecord` records and a default candidate registry. All current
  records are `citation_only` or `validation_candidate`.
- F-007: RFC 0005 xfails remain expected. `resistance_curve()` still returns raw
  `raw_ittc_michell` output accepted only for comparative filtering.

## Files changed

- `kayakgen/eval/calibration.py`
- `kayakgen/eval/contract.py`
- `kayakgen/eval/resistance.py`
- `kayakgen/eval/__init__.py`
- `tests/test_resistance.py`
- `docs/rfcs/0012-resistance-model-calibration.md`
- `docs/workflows/0012-resistance-calibration-source-review/QUEUE.md`
- `docs/workflows/0012-resistance-calibration-source-review/OPERATOR_REPORT.md`

## Verification

- `.venv/bin/python -m pytest tests/test_resistance.py -q` -> 12 passed,
  2 xfailed.
- `.venv/bin/python -m pytest -q` -> 100 passed, 2 xfailed.
- `git diff --check` -> clean.
