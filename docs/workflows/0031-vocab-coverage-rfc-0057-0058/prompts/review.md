# Review — vocab coverage test extensions

Review the implement job's patch to `tests/test_vocabulary_coverage.py`
against the rules in `roles/reviewer.md` and the source-of-truth pin
requirement in `SOURCES.md`.

Concretely, confirm:

1. **Glossary coverage parametric** iterates a list containing the six
   RFC 0057/0058 aggregate terms (`GenerativeJob`,
   `StabilityFitRecord`, `StabilityFixturePromotionPacket`,
   `MeasuredStabilityFixture`, `cfd_in_loop_evaluator_status`,
   `AnalyticalClaimLabel`) and each appears verbatim in
   `docs/UBIQUITOUS_LANGUAGE.md`.
2. **State-vocabulary test** derives its source set from
   `typing.get_args` on `kayakgen.services.generative_jobs.JobState`,
   not from a hand-typed copy.
3. **State-vocabulary test** reads the documented `--state` line out
   of `docs/USER_GUIDE.md` and asserts the parsed set equals the
   runtime set. A hardcoded expected list is a finding.
4. **Failure modes**: if the source enum lost a member, the test
   fails loudly. If the docs line drifted, the test fails loudly.
5. **Write scope discipline**: the patch touched only the test file
   and the run's artifact directory. Confirm via `git status` /
   patch summary.
6. **Gating**: `.venv/bin/pytest tests/test_vocabulary_coverage.py -v`
   is green and reported counts in `PATCH_SUMMARY.md` match.

Write the review to
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0031/review/REVIEW.md`
with `verdict: accepted` / `verdict: needs_revision`, a `must_fix:`
list, and a `non_blocking_successors:` list. If nothing is wrong, say
"None." Do not edit the test file from inside this job — your write
scope is review-only.
