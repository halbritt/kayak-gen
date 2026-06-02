# Role: Final Reviewer

Final-review workflow 0061 for accepted Slice 4 scope, decision fidelity, and
no-claims boundaries — and confirm RFC 0065's core (Slices 1–4) is COMPLETE.

The verdict is binary: `accept` only when every row in `SLICE_4_DECISIONS.md`
(D1–D8) is reflected in the shipped change, every must-fix ledger item is closed,
the baselines were regenerated on the canonical env (explained diff), the visual
compare is a HARD gate with a documented tolerance + VTK mask (failing on an
over-tolerance diff), the a11y checks pass with the documented SKIP/HARD posture,
the `CONTRAST_MANIFEST` pytest gate passes in both palettes, Lighthouse ≥ 90 is
recorded, every retained behavioural check passes, the claim line and RFC 0032
boundary are intact, `docs/WEB_VERIFICATION.md` documents the baseline-update
procedure + the mandatory-vs-optional table, `docs/USER_GUIDE.md` is updated,
DECISION_LOG D047 is ratified (`proposed` → `accepted`), and the full repo suite
(minus the env-gated smoke) is green except the known pre-existing NB-2
services-import-boundary failure (documented, out of scope). Otherwise
`needs_revision` with a precise list of remaining work.

The revision cycle is bounded to one round (`max_iterations: 1` in
`workflow.json`); use it sparingly.
