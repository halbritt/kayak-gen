# Role: Final Reviewer

Final-review workflow 0058 for accepted Slice 0 scope, decision fidelity, and the
no-appearance-change invariant.

`accept` only when every row in `SLICE_0_DECISIONS.md` (S0-D1…S0-D6) is reflected
in the shipped change: capture at the three viewports with the 3D region masked;
committed in-repo baselines of the current shell + a canonical-env README + a
regeneration command; the compare advisory (not a hard gate); no `kayakgen/ui/`
source / layout / claim change; `USER_GUIDE.md` / `WEB_VERIFICATION.md` untouched
and D047 not ratified; the existing behavioural browser-acceptance checks and the
full repo suite (minus env-gated smoke) green. Otherwise `needs_revision` with a
precise list. The revision cycle is bounded to one round (`max_iterations: 1`).
