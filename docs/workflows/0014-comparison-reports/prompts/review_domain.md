Read `docs/workflows/0014-comparison-reports/SOURCES.md`, especially RFC 0013,
current `kayakgen/search/pareto.py`, resistance metadata, stability result
models, and sweep records.

Produce `striatum/0014-comparison-reports/domain/REVIEW_DOMAIN.md` with:

- author line: `author: operator [self-declared: operator-domain-review]`
- verdict intent: `accept`, `accept_with_findings`, or `needs_revision`
- concrete findings with IDs `D-001`, `D-002`, ...
- required action for each finding

Focus on domain semantics:

- Pareto dominance over mixed minimize/maximize objectives;
- handling missing metrics and invalid candidates;
- keeping uncertainty and warnings attached to candidate summaries;
- requiring calibrated accepted-use before resistance can be a default
  objective;
- labeling any user-requested raw-resistance frontier as exploratory.
