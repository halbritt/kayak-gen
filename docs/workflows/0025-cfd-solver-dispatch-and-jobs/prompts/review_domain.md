Read `docs/workflows/0025-cfd-solver-dispatch-and-jobs/SOURCES.md`,
especially RFC 0012 and RFC 0015.

Produce `striatum/0025-cfd-solver-dispatch-and-jobs/domain/REVIEW_DOMAIN.md`
with:

- author line: `author: operator [self-declared: operator-domain-review]`
- verdict intent
- findings `D-001`, `D-002`, ...
- required action for each finding

Focus on:

- raw/unvalidated CFD result wording;
- solver profile readiness requirements and speed/fluid inputs;
- artifact provenance and reproducibility;
- why unavailable/mock adapters must not imply physical validation;
- what result normalization, if any, is safe before real solver output exists.
