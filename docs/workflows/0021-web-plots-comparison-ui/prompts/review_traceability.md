Read `docs/workflows/0021-web-plots-comparison-ui/SOURCES.md`, especially RFC
0008, RFC 0013, the web app, comparison report code, CLI compare command, and
tests.

Produce `striatum/0021-web-plots-comparison-ui/traceability/REVIEW_TRACEABILITY.md`
with:

- author line: `author: operator [self-declared: operator-traceability-review]`
- verdict intent
- findings `T-001`, `T-002`, ...
- required action for each finding

Focus on:

- RFC 0008 plot-tab acceptance and RFC 0013 web follow-up requirements;
- what comparison/report views can land as the smallest coherent slice;
- whether candidate reload into the editor is required for this workflow or can
  be explicitly deferred;
- RFC/readme status updates needed after implementation;
- which browser/Lighthouse/hosted-demo items from workflow 0020 remain separate.
