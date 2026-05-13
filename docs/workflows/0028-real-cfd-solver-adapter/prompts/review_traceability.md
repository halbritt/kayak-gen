Read `docs/workflows/0028-real-cfd-solver-adapter/SOURCES.md`, especially RFC
0015, proposed or accepted RFC 0017, workflow 0025's report, and workflow 0027
if a watertight solver input is selected.

Produce
`striatum/0028-real-cfd-solver-adapter/traceability/REVIEW_TRACEABILITY.md`
with:

- author line: `author: operator [self-declared: operator-traceability-review]`
- verdict intent
- findings `T-001`, `T-002`, ...
- required action for each finding

Focus on:

- RFC 0015 real-solver deferrals that workflow 0028 may close;
- proposed or accepted RFC 0017 acceptance criteria and any amendment needed
  before implementation;
- whether workflow 0027 closed-volume geometry is required by the selected
  solver profile;
- documentation/status wording needed to keep outputs raw and unvalidated;
- future slices that must remain deferred.
