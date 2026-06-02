# Role: Final Reviewer

Final-review workflow 0059 for accepted Slice 2 scope, decision fidelity, and
no-claims boundaries.

The verdict is binary: `accept` only when every row in `SLICE_2_DECISIONS.md`
(D1–D8) is reflected in the shipped change, every must-fix ledger item is closed,
the widened orphan lint + the layout/inline-help tests + the desktop rendered-bbox
tests are green, the region/status/collapse contract and the 1440×900
first-viewport contract hold, the claim line and RFC 0032 boundary are intact,
`docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` are untouched, D047 is not
ratified, and the full repo suite (minus the env-gated smoke) is green. Otherwise
`needs_revision` with a precise list of remaining work.

The revision cycle is bounded to one round (`max_iterations: 1` in
`workflow.json`); use it sparingly.
