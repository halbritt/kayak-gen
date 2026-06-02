# Remediation Prompt

Read the implementer patch summary and the findings ledger. Fix the must-fix
items only.

Keep fixes scoped; preserve every `SLICE_0_DECISIONS.md` decision: no
`kayakgen/ui/` source / appearance / layout / claim change; the compare stays
advisory (the hard gate is Slice 4); `USER_GUIDE.md` / `WEB_VERIFICATION.md`
untouched. Update `CHANGELOG.md` where appropriate, run the browser-acceptance
profile and the full repo suite (minus the env-gated smoke), and heartbeat the
lease during long Playwright runs before publishing the patch summary.
