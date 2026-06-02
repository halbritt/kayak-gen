# Role: Final Reviewer

Final-review workflow 0060 for accepted Slice 3 scope, decision fidelity, and
no-claims boundaries.

The verdict is binary: `accept` only when every row in `SLICE_3_DECISIONS.md`
(D1–D8) is reflected in the shipped change, every must-fix ledger item is closed,
control states derive from Slice 1 tokens and honestly-disabled controls keep
their copy, every panel renders an explicit tested empty/loading/error state, the
forbidden-copy scan was extended and is green, styling is token-only, the Slice 2
region/status/collapse/first-viewport contract holds, every hook change is
reflected in the layout/inline-help tests, the claim line and RFC 0032 boundary
are intact, `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` are untouched, D047
is not ratified, and the full repo suite (minus the env-gated smoke) is green
except the known pre-existing NB-2 services-import-boundary failure (documented,
out of scope). Otherwise `needs_revision` with a precise list of remaining work.

The revision cycle is bounded to one round (`max_iterations: 1` in
`workflow.json`); use it sparingly.
