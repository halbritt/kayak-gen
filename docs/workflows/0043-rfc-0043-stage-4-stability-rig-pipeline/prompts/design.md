# Design prompt — workflow 0043 (panel design)

You are one of two designers (claude / codex) producing an
independent design for the RFC 0043 stage-4 + RFC 0056 stage-4
promotion pipeline. **Do not coordinate with the other two designers.**
Write only to your own lane's `artifacts/design/<lane>/DESIGN.md`.
Your work will be synthesized with the other two designs in a
downstream `synth_design` job.

Read first:

- `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/SOURCES.md`
- `docs/rfcs/0043-high-angle-gz-successor.md` (stage 4 acceptance criteria)
- `docs/rfcs/0056-strain-gauged-gz-rig.md` (fixture schema, already landed)
- `kayakgen/eval/stability/measured_fixture.py` (the schema you consume)
- `kayakgen/eval/claims.py` (claim-state vocabulary)
- `docs/rfcs/0054-calibration-campaign-tooling.md` (`accept-fit` pattern to mirror)

## What you are designing

The pipeline that takes a `MeasuredStabilityFixture` (RFC 0056
schema) from JSON-on-disk through acceptance into the claim_state
resolution path. Four pieces, end to end:

1. **Ingestion** — A new CLI command, probably
   `kayakgen calibration ingest-measured-stability <fixture.json>`,
   that validates the fixture against the RFC 0056 schema and
   produces a structured record under
   `data/stability/fixtures/<fixture_id>.json` (this is the path the
   .gitignore already protects).
2. **Acceptance gate** — A new CLI command, probably
   `kayakgen calibration accept-measured-stability <fixture_id>
   --rig-source-review <path>`, that runs the RFC 0056 +
   RFC 0027 / 0025 acceptance gates against the fixture and writes an
   `AcceptedStabilityFixtureRecord` to
   `data/stability/fits/<accepted_id>.json`.
3. **Claim-state resolution** — The path in `kayakgen/eval/claims.py`
   that consults the accepted-fixture registry and flips the
   high-angle GZ output's `claim_state` from
   `analytical_only` (or whatever the current literal is) to
   `measured_validated` (or whatever literal RFC 0043 specifies for
   stage 4).
4. **Operator surfacing** — Where does the operator see the flip?
   In `kayakgen evaluate` output? In the web Generate panel? In the
   desktop chip? Define which surfaces update and which do not.

## Required design content

Your `DESIGN.md` must answer:

### A. CLI shape

- What are the exact command names + flag signatures? (e.g.
  `kayakgen calibration ingest-measured-stability <path> --out <dir>`).
- What is the JSON shape of the structured ingestion output? Cite
  the RFC 0056 schema fields you carry forward verbatim.
- What is the JSON shape of the `AcceptedStabilityFixtureRecord`?
  How does it differ from RFC 0054's `AcceptedFitRecord`?

### B. Acceptance-gate criteria

- What criteria must a fixture pass to be accepted? Cite RFC 0056
  Stage-4 + RFC 0027 / 0025 gates explicitly.
- What is the structured refusal shape when a fixture fails? Name
  the rejection-code constants.
- Are there partial-acceptance states (e.g. accepted-but-bounded-to-
  heel-range)? If yes, how does the claim_state reflect them?

### C. Claim-state resolution

- What is the new `ClaimState` literal (if any)? Reuse existing
  literals if possible.
- What is the lookup rule? Does it scan `data/stability/fits/` at
  evaluation time, or is there an index?
- How does the claim_state flip propagate to the existing high-angle
  GZ readiness chip in the UI? (Read RFC 0058 for the
  `cfd_in_loop_evaluator_status` pattern — your shape should mirror
  it.)

### D. Test surface

- List the tests you would add. For each, name the function and
  one-line objective.
- Include at least: one happy-path ingestion test, one rejection
  test per acceptance criterion, one claim_state-flip integration
  test.

### E. Operator-facing copy

- The `kayakgen calibration --help` text after your additions.
- The USER_GUIDE.md subsection text (one-paragraph + a fenced
  example invocation).

### F. Open questions

- Anything you considered and explicitly deferred or where you saw
  a load-bearing decision your design doesn't fully resolve. Flag
  it here; the synthesizer will pick a disposition.

## What you are NOT doing

- Not implementing anything. The implement job is downstream.
- Not extending the RFC 0056 schema. It is landed; you consume it.
- Not touching `docs/rfcs/`, `kayakgen/`, or `tests/`. Your
  `allowed_paths` is your design artifact dir only.
- Not coordinating with the other two designers.

## Output

One file: `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/design/<lane>/DESIGN.md`.

Under 2500 words. Density over coverage. Use headings + bullet
lists; avoid prose-padding.
