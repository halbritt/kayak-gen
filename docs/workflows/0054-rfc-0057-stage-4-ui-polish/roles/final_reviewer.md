# Role: Final Reviewer

Final-review workflow 0054 for accepted scope, decision fidelity, and
no-claims boundaries.

The verdict is binary: `accept` only when every line in
`STAGE_4_DECISIONS.md` is reflected in the shipped behavior, every must-fix
ledger item is closed, and the full repo suite is green. Otherwise
`needs_revision` with a precise list of remaining work.

The revision cycle is bounded to one round (`max_iterations: 1` in
`workflow.json`); use it sparingly.
