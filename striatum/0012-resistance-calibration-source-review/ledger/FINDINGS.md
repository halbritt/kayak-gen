# Findings ledger - 0012

author: operator [self-declared: operator-ledger-temp]
run: run_b8d2bd2b94f345c1a30521671cf0ba67
job: findings_ledger
date: 2026-05-13

## Gate result

No candidate source is accepted as canonical calibration data for
`calibrated_kayak_v1`.

The workflow should proceed with the fallback implementation: keep resistance
curves raw/uncalibrated, add explicit source/provenance structures, register
candidate sources as citation-only or validation candidates, and preserve the
RFC 0005 expected failures.

## Stats

- Source findings: 10
- Deduplicated findings: 7
- By severity: blocker 3 / high 3 / medium 1
- Actionable now: 4
- Blocks numeric calibration: 3

## Findings

### F-001 - No reviewed source is safe to vendor as calibration fixture data

- Sources: P-001, source inventory
- Severity: blocker
- Classification: blocks-calibration
- File(s): future source registry/docs
- Statement: Sea Kayaker-derived tables, review PDFs, Gomes papers, and K1
  tow/passive-drag sources are copyrighted or lack explicit redistribution
  permission for checked-in numeric fixtures.
- Required remediation: Do not check extracted numeric tables into this repo
  without explicit permission or an open license. Implement a citation-only
  registry instead.

### F-002 - Sea Kayaker data are class-relevant but model-derived

- Sources: P-002, D-002
- Severity: high
- Classification: blocks-calibration
- File(s): `docs/rfcs/0012-resistance-model-calibration.md`
- Statement: Sea Kayaker/KAPER/Broze-Taylor tables cover the right hull class
  but are not primary measured resistance data.
- Required remediation: Treat these sources as model-to-model sanity context,
  not a canonical calibration target.

### F-003 - Sprint K1 measured data are too narrow for general sea-kayak calibration

- Sources: D-001, source inventory
- Severity: high
- Classification: blocks-calibration
- File(s): `docs/rfcs/0012-resistance-model-calibration.md`
- Statement: Gomes and Tzabiras provide measured kayak data, but they are
  sprint K1 cases with different geometry/load/speed regimes from touring sea
  kayaks.
- Required remediation: Treat these sources as validation/holdout candidates,
  not as general `calibrated_kayak_v1` calibration sources.

### F-004 - RFC 0012 needs explicit source acceptance requirements

- Sources: D-003
- Severity: high
- Classification: actionable-now
- File(s): `docs/rfcs/0012-resistance-model-calibration.md`
- Statement: The RFC says "published kayak/canoe data" but does not yet define
  enough acceptance criteria for source/provenance review.
- Required remediation: Add a checklist for measured resistance, geometry/load
  context, validity range, source rights, and extraction reproducibility.

### F-005 - Resistance metadata needs calibration/provenance fields

- Sources: I-001
- Severity: high
- Classification: actionable-now
- File(s): `kayakgen/eval/contract.py`, `kayakgen/eval/resistance.py`,
  `tests/test_resistance.py`
- Statement: `ResistanceMetadata` lacks optional fields for calibration name,
  version, source citation/license, extraction method, and validity ranges.
- Required remediation: Add optional fields without changing current raw
  behavior.

### F-006 - Candidate sources should be structured, not buried in prose

- Sources: I-003
- Severity: medium
- Classification: actionable-now
- File(s): new `kayakgen/eval/calibration.py` or equivalent,
  `tests/test_resistance.py`
- Statement: A structured citation/validation registry would make the no-go
  decision machine-readable and safer for future workflows.
- Required remediation: Add Pydantic models for calibration source records and
  a default candidate-source registry. Mark all current candidates as
  `citation_only` or `validation_candidate`, not `calibration_fixture`.

### F-007 - RFC 0005 xfails must remain until calibration or RFC revision

- Sources: I-004
- Severity: blocker
- Classification: actionable-now
- File(s): `tests/test_resistance.py`, `docs/rfcs/0005-cfd-resistance.md`
- Statement: No accepted dataset exists to honestly satisfy the low-Froude and
  200 ms full-curve acceptance tests.
- Required remediation: Preserve the expected failures and make RFC 0012 clear
  that resistance closure is blocked on accepted data or RFC 0005 revision.

## Implementation guidance

Safe now:

- Update RFC 0012 with source acceptance criteria and the no-accepted-source
  gate result.
- Add optional provenance/calibration fields to `ResistanceMetadata`.
- Add a structured source registry with candidate source categories and URLs.
- Add tests for metadata serialization and registry categories.
- Preserve raw resistance behavior and RFC 0005 xfails.
- Fix stale workflow bookkeeping in the 0011 operator report while touching
  reports.

Do not implement in this workflow:

- Numeric calibration coefficients.
- `calibrated_kayak_v1`.
- Default Pareto use of resistance.
- Checked-in extracted tables from copyrighted sources.
