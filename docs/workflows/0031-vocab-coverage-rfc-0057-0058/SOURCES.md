# Sources for workflow 0031 — vocab coverage for RFC 0057/0058

> Operator: this workflow's scope is fixed by the audit findings
> `AUD-P-003` and `AUD-P-004`. No per-run scope editing is needed; the
> entries below are the canonical inputs every run reads.

## Source RFCs / audit references

- `docs/audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md` — batches
  **R2 (test slice)** and **R8**.
- `docs/audits/2026-05-22-code-doc-audit/pipeline-integrity/FINDINGS.md`
  — findings `AUD-P-003` (medium, RFC 0057/0058 glossary terms not
  pinned) and `AUD-P-004` (low, `runs jobs --state` vocabulary not
  pinned).
- `docs/rfcs/0057-generative-search-jobs.md` — defines `GenerativeJob`
  and the six-state lifecycle (`queued|running|succeeded|failed|cancelled|resumable`).
- `docs/rfcs/0058-stability-calibration-acceptance.md` — defines
  `StabilityFitRecord`, `StabilityFixturePromotionPacket`,
  `MeasuredStabilityFixture`, `cfd_in_loop_evaluator_status`,
  `AnalyticalClaimLabel`.

## Code surfaces under test

- `tests/test_vocabulary_coverage.py` — the test surface this workflow
  extends.
- `kayakgen/services/generative_jobs.py` — defines `JobState` (the
  source of truth for `kayakgen runs jobs --state`).
- `docs/UBIQUITOUS_LANGUAGE.md` — glossary; read-only here.
- `docs/USER_GUIDE.md` — documents the six-state vocabulary near
  `### runs`; read-only here.

## Vocabularies pinned by this run

### Glossary terms (must appear verbatim in `docs/UBIQUITOUS_LANGUAGE.md`)

- `GenerativeJob`
- `StabilityFitRecord`
- `StabilityFixturePromotionPacket`
- `MeasuredStabilityFixture`
- `cfd_in_loop_evaluator_status`
- `AnalyticalClaimLabel`

### `kayakgen runs jobs --state` enum (must equal the source `JobState` Literal)

- `queued`
- `running`
- `succeeded`
- `failed`
- `cancelled`
- `resumable`

## Where the run artifacts will land

`docs/audits/2026-05-22-code-doc-audit/follow-ups/0031/`:

```
PATCH_SUMMARY.md         # implement job
review/REVIEW.md         # review job
```

## Adversary framing

- implement → look for *string-typing drift*: a test that hand-copies a
  literal instead of importing it from source. Both new test surfaces
  must read source-of-truth artifacts (`get_args` on the Literal; a
  parsed line out of `USER_GUIDE.md`) rather than hardcoded mirrors.
- review → look for *silent skip drift*: a parametric test that would
  pass with zero cases if the source enum were emptied. Confirm the
  test asserts on the set, not just on individual membership.
