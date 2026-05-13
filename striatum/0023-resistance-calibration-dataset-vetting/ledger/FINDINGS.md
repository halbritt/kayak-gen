# Findings ledger - resistance calibration dataset vetting

author: operator [self-declared: operator-ledger]
run: run_6ca2095f019345e199943d5f46f0676f
job: findings_ledger
date: 2026-05-13

## Gate result

No dataset is accepted as a `calibration_fixture`.

The University of Edinburgh DataShare dataset "Hydrodynamics of Three Slender
Models Resembling Pacific Canoe Hulls" is accepted as a
`validation_candidate` source record only. It has reusable CC BY 4.0 dataset
rights and measured slender-hull towing-tank data, but its hull class and test
setup do not support calibrating a general kayak resistance model.

Current resistance output must remain `raw_ittc_michell`, `uncalibrated`, and
`comparative_filter_only`.

## Deduplicated findings

### F1 - Add Edinburgh as a validation candidate

Source lanes: source inventory, provenance P1, domain D1, implementation I1.

Type: actionable-now.

Add a `ResistanceSourceRecord` for the Edinburgh DataShare dataset:

- `source_id`: `edinburgh_pacific_canoe_hydrodynamics`
- `intended_use`: `validation_candidate`
- `measured_data`: `True`
- rights: CC BY 4.0 dataset license, DOI `10.7488/ds/3785`
- warnings: `pacific_canoe_not_sea_kayak`, `fixed_sink_trim`,
  `validation_not_calibration`

Do not add it as a calibration fixture.

### F2 - Update RFC 0012 with the validation-only result

Source lanes: domain D2, implementation I2.

Type: actionable-now.

Record that an open measured slender-hull validation dataset has been found,
but that calibrated sea-kayak prediction remains blocked. RFC 0012 should stay
proposed; current curves remain uncalibrated.

### F3 - Do not ingest numeric rows in this workflow

Source lanes: provenance P1/P2, implementation I3.

Type: deferred.

The workbook is CC BY 4.0 and inspectable, but fixture ingestion requires a
schema for attribution, source-file metadata, sheet/row filters, units, scale,
and extraction method. Do not check in extracted rows until that contract exists.

### F4 - Keep prior candidate classifications unchanged

Source lanes: source inventory, provenance P3, domain D3.

Type: no-go for calibration.

Sea Kayaker/KAPER-derived tables stay citation-only; Gomes and Tzabiras K1
studies stay validation candidates by citation only; MDPI/open physics articles
stay citation-only context.

## Implementation instructions

Implement only:

- source registry update for Edinburgh;
- focused registry tests;
- RFC/workflow status updates;
- patch summary artifact.

Do not implement:

- calibrated resistance metadata;
- numeric fixture extraction or ingestion;
- changed sweep/Pareto defaults;
- changes to `ResistanceCurve.metadata.calibration_status` or
  `accepted_use`.

## Next workflow status

If implementation and final review pass, the next queued workflow remains
0024 watertight solid mesh profile. RFC 0012 remains proposed and blocked for
calibration by the lack of a class-relevant measured kayak calibration dataset.
