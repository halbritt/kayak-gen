# Implement — extend `tests/test_vocabulary_coverage.py`

Read:

- `docs/audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md` (batches
  **R2 test slice** and **R8**).
- `docs/audits/2026-05-22-code-doc-audit/pipeline-integrity/FINDINGS.md`
  (`AUD-P-003`, `AUD-P-004`).
- `tests/test_vocabulary_coverage.py` (existing pattern).
- `docs/UBIQUITOUS_LANGUAGE.md` (must already contain the six terms).
- `docs/USER_GUIDE.md` near `### runs` for the `kayakgen runs jobs --state`
  line.
- `kayakgen/services/generative_jobs.py` (the `JobState` Literal).

## (a) RFC 0057/0058 glossary coverage — closes AUD-P-003

Extend `tests/test_vocabulary_coverage.py` with a parametric test that
asserts each of the following terms appears verbatim in
`docs/UBIQUITOUS_LANGUAGE.md`:

- `GenerativeJob`
- `StabilityFitRecord`
- `StabilityFixturePromotionPacket`
- `MeasuredStabilityFixture`
- `cfd_in_loop_evaluator_status`
- `AnalyticalClaimLabel`

You may extend the existing `_DECISION_TOKENS` parametric or add a new
`_RFC_0057_0058_AGGREGATE_TERMS` tuple — match the surrounding style.
If any term is missing from the glossary, **stop and report**; do not
edit the glossary yourself.

## (b) `runs jobs --state` regression — closes AUD-P-004

Add a new test (e.g. `test_runs_jobs_state_vocabulary_matches_source_and_docs`)
that:

1. Imports `JobState` from `kayakgen.services.generative_jobs`.
2. Computes the runtime set with `set(get_args(JobState))`.
3. Asserts the runtime set equals
   `{"queued", "running", "succeeded", "failed", "cancelled", "resumable"}`.
4. Reads `docs/USER_GUIDE.md`, locates the `kayakgen runs jobs
   [--state ...]` line, extracts the pipe-separated state list, and
   asserts that parsed set equals the runtime set.

The contract is bidirectional: if the source enum and the user guide
disagree, the test fails. Do not "fix" docs to match source or vice
versa — the parent agent owns wording fixes.

## Verify

```bash
.venv/bin/pytest tests/test_vocabulary_coverage.py -v
```

All cases must pass.

## Write scope

- `tests/test_vocabulary_coverage.py`
- `docs/audits/2026-05-22-code-doc-audit/follow-ups/0031/`

## Forbidden

- `docs/UBIQUITOUS_LANGUAGE.md`
- `docs/USER_GUIDE.md`
- `CHANGELOG.md`
- `docs/audits/2026-05-22-code-doc-audit/pipeline-integrity/FINDINGS.md`
- anything under `kayakgen/`

Publish `PATCH_SUMMARY.md` under the follow-ups directory naming the
touched file, the new test names, the test-count delta, and the
runtime state set the new test enforces.
