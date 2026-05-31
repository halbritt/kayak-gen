# SOURCES — 0043 RFC 0043 stage 4 stability-rig pipeline

Per-run context manifest. Required reading for every lane.

## RFCs

- `docs/rfcs/0043-high-angle-gz-successor.md` — stage-4 goal: flip
  the high-angle GZ claim_state from analytical-only to measured-or-
  better once an accepted `measured_stability_fixture` exists. Read
  the stage-4 acceptance criteria first.
- `docs/rfcs/0056-strain-gauged-gz-rig.md` — defines
  `MeasuredStabilityFixture` schema (already landed schemas-only at
  `kayakgen/eval/stability/measured_fixture.py`). The pipeline this
  workflow builds consumes that schema; it does NOT redefine it.
- `docs/rfcs/0054-calibration-campaign-tooling.md` — the
  `kayakgen calibration` sub-app pattern your ingestion CLI extends.
  Read its `accept-fit` shape to understand the acceptance-gate
  vocabulary.
- `docs/rfcs/0027-resistance-calibration-acceptance.md` — the
  RFC 0027 `SourceUse` acceptance pattern. The measured-stability
  acceptance gate mirrors this. Cross-reference required.
- `docs/rfcs/0025-cfd-calibration-claim-gates.md` — the claim-gate
  enforcement layer. Your claim-state resolution must respect this
  shape; do not invent a parallel gate.

## Code

### Already landed (read-only for this workflow)

- `kayakgen/eval/stability/measured_fixture.py` — `MeasuredStabilityFixture`
  Pydantic model + validators per RFC 0056. The pipeline consumes
  this; do NOT extend the schema in this workflow.
- `kayakgen/eval/claims.py` — `ClaimState` literals, `SourceUse`
  vocabulary, claim-resolution helpers. You add a measured-stability
  accepted-fixture path here; do not refactor the existing literals.
- `kayakgen/eval/calibration/` — existing calibration ingestion +
  acceptance code. The new measured-stability ingestion lives
  alongside this in a sibling module.
- `kayakgen/cli/main.py` — Typer sub-app registry. You wire the new
  `kayakgen calibration ingest-measured-stability` +
  `accept-measured-stability` commands here (or as additions under
  an existing calibration_cli.py if one exists).

### To add or extend

- `kayakgen/cli/calibration_cli.py` — if it exists, extend; if not,
  create. Hosts the new ingestion + acceptance CLI subcommands.
- `kayakgen/eval/stability/measured_acceptance.py` — new module.
  Acceptance-gate logic. Mirrors RFC 0027 `accept-fit` shape from
  RFC 0054.
- `tests/test_measured_stability_acceptance.py` — new. Covers the
  acceptance gate happy path + every refusal path.
- `tests/test_measured_stability_ingest.py` — new. Covers the
  ingestion CLI from a sample `MeasuredStabilityFixture` JSON
  fixture (build a deterministic in-test fixture; do not require
  physical rig data).
- `tests/test_claim_state_measured_promotion.py` — new. Covers the
  claim-state flip from analytical to measured-or-better when an
  accepted fixture exists.

## Decision log rows

- `docs/DECISION_LOG.md` — read the D006 / D007 / D014 rows for
  context on the physical rig + measurement campaign that gates
  acceptance. The pipeline you build does NOT depend on those
  rows being closed; it depends on the RFC 0056 schema, which is
  landed.

## User-facing docs

- `docs/USER_GUIDE.md` — the implementer adds a `### Measured
  stability fixtures` subsection under the existing
  `## Calibration` heading. The subsection documents the new CLI
  commands + when they are appropriate to run.

## Out-of-scope reminders

- **No physical rig acquisition.** This workflow does not require
  measured rig data; it lands the pipeline that consumes such data
  when it arrives.
- **No flip of RFC 0043 / RFC 0056 Status.** Doc-only flip is a
  parent-agent commit after the full workflow converges.
- **No CFD or resistance subsystem touches.** This is the stability
  subdomain only.
- **No new `ClaimState` literal or `SourceUse` vocabulary.** Reuse
  the existing acceptance grammar.
