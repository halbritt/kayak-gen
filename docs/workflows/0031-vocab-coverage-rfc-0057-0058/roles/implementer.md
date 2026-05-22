# Role: Implementer

You extend `tests/test_vocabulary_coverage.py` so that the six
RFC 0057/0058 aggregate-root glossary terms and the six-state
`kayakgen runs jobs --state` vocabulary become covered regressions.

Your scope is intentionally narrow: one test file plus the run's
artifact directory under `docs/audits/2026-05-22-code-doc-audit/follow-ups/0031/`.
You do not touch the glossary, the user guide, the CHANGELOG, the
audit FINDINGS.md, or any source file under `kayakgen/`.

Rules:

- Pull both vocabularies from a source-of-truth artifact. The state
  literal must come from `kayakgen.services.generative_jobs.JobState`
  via `typing.get_args`, not a hand-typed mirror.
- The documented `--state` line is parsed out of `docs/USER_GUIDE.md`,
  not hand-typed. If you cannot find the line, fail the test loudly.
- Match the existing parametric pattern in the file. Keep the glossary
  expansion parallel with `_DECISION_TOKENS` / `_READINESS_LITERALS`.
- If a glossary term is missing from `docs/UBIQUITOUS_LANGUAGE.md`,
  stop and report which one — never silently add it. The glossary
  surface is owned by the parent audit's R1 batch.
- Run `.venv/bin/pytest tests/test_vocabulary_coverage.py -v` and
  confirm every case passes before publishing.

Publish a `PATCH_SUMMARY.md` artifact in the run's follow-ups
directory naming the touched file, the new test names, the test count
delta, and the runtime state set the new test enforces.
