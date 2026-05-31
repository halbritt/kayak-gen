# Implement prompt — workflow 0043

You land the accepted design from
`docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`
after the three design reviews converged on `accept`.

Read first, in order:

1. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/SOURCES.md`
2. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`
   — the **accepted design**. Section 3 is your specification.
3. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/review/design/{claude,codex,gemini}/REVIEW.md`
   — adopt every `accept with follow-ups` recommendation that does
   not contradict section 3.
4. `docs/rfcs/0043-high-angle-gz-successor.md` and
   `docs/rfcs/0056-strain-gauged-gz-rig.md` — the load-bearing
   RFCs.
5. `kayakgen/eval/stability/measured_fixture.py` (the schema you
   consume), `kayakgen/eval/claims.py` (the claim-state vocabulary
   you extend), and the existing
   `kayakgen/eval/calibration/` modules.

## Deliverables

Land each of the following per the accepted design:

### 1. Ingestion + acceptance CLI

Under `kayakgen/cli/calibration_cli.py` (extend if exists, create
if not), register Typer subcommands per the synthesis section A:

- `kayakgen calibration ingest-measured-stability <path>`
- `kayakgen calibration accept-measured-stability <fixture_id>`
  (with flags per the accepted design)

Wire registrations into `kayakgen/cli/main.py` if the calibration
sub-app isn't already imported there.

### 2. Acceptance-gate module

Add `kayakgen/eval/stability/measured_acceptance.py` with the
acceptance-gate logic per the synthesis section B. Each gate is
its own function returning a structured `Accept` / `Reject(code,
reason)` shape. Cite the RFC 0027 / 0025 rejection-code constants
and reuse them when applicable.

### 3. Claim-state resolution

Extend `kayakgen/eval/claims.py` per the synthesis section C. Add
the new `ClaimState` literal (if the design called for one) and
the resolution helper. Honor RFC 0025 claim-gate enforcement —
do NOT introduce a parallel gate.

### 4. Tests

Add the three test files per the synthesis section D, using its
exact function names:

- `tests/test_measured_stability_acceptance.py`
- `tests/test_measured_stability_ingest.py`
- `tests/test_claim_state_measured_promotion.py`

Use a deterministic in-test fixture (no physical rig data
required). Cover every acceptance-gate refusal path.

### 5. Operator-facing docs

Update `docs/USER_GUIDE.md` per the synthesis section E. Place the
new `### Measured stability fixtures` subsection under the
existing `## Calibration` heading (or whatever heading the file
already uses for calibration content).

Update `docs/DECISION_LOG.md` with a D-series row recording the
decision to land this pipeline. Use the same structure the other
recent D-rows use (date, decision, rationale, follow-ups).

### 6. Workflow handoff

Write `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/build/HANDOFF.md`
with:

- Files changed (path + line counts)
- Pytest output summary (collected / passed / failed / skipped)
- Section-by-section verification: A / B / C / D / E from the
  accepted design — for each, cite the file:line where it
  landed and quote one line of evidence
- Open Questions adjudication summary (which OQ-N you landed
  which way, and why)
- Any review recommendations you did NOT adopt and why

## Verification

Before closing, in the project venv:

```bash
.venv/bin/pytest \
  tests/test_measured_stability_acceptance.py \
  tests/test_measured_stability_ingest.py \
  tests/test_claim_state_measured_promotion.py \
  tests/test_cli.py \
  tests/test_claims.py \
  -q
```

The existing `tests/test_cli.py` and `tests/test_claims.py` must
continue to pass without modification — that's the proof you
didn't regress the existing claim-state grammar or CLI surface.
If either of those files doesn't exist, substitute the closest
existing coverage and document the substitution in
HANDOFF.md.

## Scope discipline

You may write only to paths under your `write_scope.allowed_paths`.
The `forbidden_paths` list explicitly bars:

- `docs/rfcs/` — RFC 0043 / RFC 0056 status flips are parent-agent
  territory after the build review converges.
- `kayakgen/ui/`, `kayakgen/services/` — presentation + service
  layers are out of scope.
- `kayakgen/model/hull.py`, `kayakgen/model/distribution_v2.py` —
  geometry aggregate is read-only.
- `kayakgen/search/`, `kayakgen/eval/resistance.py`,
  `kayakgen/eval/cfd/` — unrelated subdomains.
- `CHANGELOG.md` — parent-agent records the workflow run.

Do not work around these by editing through an allowed path.

## When the implement job ends

The three build-review lanes will fan out against your
implementation. A `needs_revision` verdict bounces the implement
job back to you (max 2 revisions per reviewer); adopt the
review's specific suggested remediation rather than rebuilding
broad swaths.
