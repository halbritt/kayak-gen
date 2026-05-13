Read `docs/workflows/0021-web-plots-comparison-ui/SOURCES.md`, especially
RFC 0013, `kayakgen/search/compare.py`, `kayakgen/search/pareto.py`,
`kayakgen/ui/web/app.py`, `kayakgen/ui/web/controllers.py`, and comparison
tests.

Produce `striatum/0021-web-plots-comparison-ui/domain/REVIEW_DOMAIN.md` with:

- author line: `author: operator [self-declared: operator-domain-review]`
- verdict intent
- findings `D-001`, `D-002`, ...
- required action for each finding

Focus on:

- which hydrostatics/resistance values are safe to plot and with what units;
- whether Pareto axes and candidate table wording preserve RFC 0012 resistance
  uncertainty and exploratory labels;
- whether failed/skipped/invalid candidates remain visible with warnings;
- which comparison actions are safe now versus larger future UI work;
- whether candidate reload into the editor can be done without corrupting web
  state semantics.
