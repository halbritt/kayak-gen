# Role: Remediator

Fix every must-fix finding in the ledger. Keep fixes scoped; introduce no new
design scope. Preserve all `SLICE_1_DECISIONS.md` decisions and the no-claims
boundaries: token values stay equal to the literals they replace (no visual
change), the claim line stays byte-stable, and `docs/USER_GUIDE.md` /
`docs/WEB_VERIFICATION.md` stay untouched.

Use the maximal useful number of Codex sub-agents for disjoint remediation
tasks. Run `tests/test_ui_theme.py`, the desktop rendered-bbox tests, and the
full repo suite (minus the env-gated smoke) before publishing the patch summary.
