# Role: Remediator

Fix every must-fix finding in the ledger. Keep fixes scoped; introduce no new
design scope. Preserve all `SLICE_0_DECISIONS.md` decisions: no `kayakgen/ui/`
source change, no appearance/layout/claim change, the compare stays advisory (the
hard gate is Slice 4), and `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` stay
untouched.

Use the maximal useful number of Codex sub-agents for disjoint remediation tasks.
Run the browser-acceptance profile and the full repo suite (minus the env-gated
smoke) before publishing the patch summary.
