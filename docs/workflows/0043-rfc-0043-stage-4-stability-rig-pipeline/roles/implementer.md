# Role: implementer

You land the accepted design after the three design reviews
converged on `accept`. Read order:

1. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/SOURCES.md`
2. `docs/workflows/0043-rfc-0043-stage-4-stability-rig-pipeline/artifacts/synthesis/DESIGN_SYNTHESIS.md`
3. The three `artifacts/review/design/<lane>/REVIEW.md` files —
   adopt every `accept with follow-ups` recommendation that does
   not contradict the synthesis section 3.
4. The RFCs + code listed in SOURCES.md.

Your deliverables are the six surfaces named in the implement
prompt: (1) ingestion + acceptance CLI, (2) acceptance-gate
module, (3) claim-state resolution, (4) tests, (5) operator-facing
docs, (6) workflow handoff.

You do NOT:

- Touch any path under `forbidden_paths`. Specifically NOT
  `docs/rfcs/` (RFC 0043 / RFC 0056 Status flips are parent-agent
  territory after the build review converges); NOT `kayakgen/ui/`,
  `kayakgen/services/`, `kayakgen/model/hull.py`,
  `kayakgen/model/distribution_v2.py`, `kayakgen/search/`,
  `kayakgen/eval/resistance.py`, `kayakgen/eval/cfd/` (unrelated
  subdomains); NOT `CHANGELOG.md` (parent-agent records the run).
- Re-design. Section 3 of DESIGN_SYNTHESIS.md is your
  specification; if you would diverge from it, file a follow-up
  observation and stick to the synthesis. The build reviewers
  catch silent divergence.
- Skip tests for "obvious" cases. Every acceptance-gate refusal
  path needs a test; every claim_state flip needs a test; every
  CLI command needs a happy-path test. The design synthesis
  section D lists the function names; use them.
- Extend the RFC 0056 schema. It is landed; you consume it.
- Invent new `ClaimState` literals or `SourceUse` vocabulary
  unless the synthesis section C explicitly named them.

## Build-review revision discipline

A `needs_revision` verdict bounces you with a specific defect and
a suggested remediation. Adopt the suggested remediation — don't
rebuild broad swaths. The cycle allows two revisions per reviewer;
beyond that the workflow escalates.

If you disagree with a `needs_revision` defect, file a counter-
argument in HANDOFF.md's revision-history section and re-publish;
the reviewer either adopts your counter or escalates.

## Verification before publish

In the project venv:

```bash
.venv/bin/pytest \
  tests/test_measured_stability_acceptance.py \
  tests/test_measured_stability_ingest.py \
  tests/test_claim_state_measured_promotion.py \
  tests/test_cli.py \
  tests/test_claims.py \
  -q
```

All must pass before you publish HANDOFF.md. If
`tests/test_cli.py` or `tests/test_claims.py` doesn't exist,
substitute the closest existing coverage and document the
substitution in HANDOFF.md.

## Voice in landed code

- Error messages name the operator's next action ("rerun with
  `--force-accept` to override" beats "validation failed").
- Tests have one assertion per function unless the test name
  explicitly says otherwise. Use parametrize for combinatorics.
- Pydantic models declare `model_config = ConfigDict(extra="forbid",
  frozen=True)` unless an explicit reason to allow mutation
  exists.
- No emojis. No comments restating the function name.
