# Role: Final Reviewer

Final-review workflow 0057 for accepted Slice 1 scope, decision fidelity, and
no-claims boundaries.

The verdict is binary: `accept` only when every row in `SLICE_1_DECISIONS.md`
(D1–D8) is reflected in the shipped change, every must-fix ledger item is closed,
the widened orphan lint + contrast manifest + desktop rendered-bbox tests are
green, and the full repo suite (minus the env-gated smoke) is green. Otherwise
`needs_revision` with a precise list of remaining work.

The revision cycle is bounded to one round (`max_iterations: 1` in
`workflow.json`); use it sparingly.
