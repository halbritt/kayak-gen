# Role: Reviewer

You review the implement job's patch for *string-typing drift* and
*silent skip drift*.

Adversarial checks:

- **Source-of-truth pin.** The new glossary-coverage parametrize must
  iterate a list whose entries appear verbatim in
  `docs/UBIQUITOUS_LANGUAGE.md`. The new state-vocabulary test must
  derive its source set from `typing.get_args` on the `JobState`
  Literal in `kayakgen.services.generative_jobs`, not from a typed
  copy of the six tokens.
- **Doc-line parse.** The state-vocabulary test must read the
  documented six-state list out of `docs/USER_GUIDE.md` (the line
  near the `kayakgen runs jobs [--state ...]` block) and assert it
  equals the runtime set. A hand-typed expected list defeats the
  drift check.
- **Empty-enum failure mode.** If the source `JobState` Literal lost
  a member tomorrow, the test must fail loudly — not pass with zero
  cases. Confirm the assertion is on the set, not just on each member.
- **Scope discipline.** Confirm the patch touched only
  `tests/test_vocabulary_coverage.py` and the run's artifact
  directory. No edits to the glossary, the user guide, the CHANGELOG,
  the audit FINDINGS.md, or any `kayakgen/` source file.
- **Gating green.** `.venv/bin/pytest tests/test_vocabulary_coverage.py -v`
  passes locally; the patch summary's reported counts match.

Write `REVIEW.md` under
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0031/review/`. Use
the same `verdict:` / `must_fix:` / `non_blocking_successors:` shape
the project's review artifacts use elsewhere. Flag any drift findings
explicitly; if none, say "None." Do not edit the test file from inside
this job.
