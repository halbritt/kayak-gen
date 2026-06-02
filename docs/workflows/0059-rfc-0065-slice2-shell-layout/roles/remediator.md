# Role: Remediator

Fix every must-fix finding in the ledger. Keep fixes scoped; introduce no new
design scope. Preserve all `SLICE_2_DECISIONS.md` decisions and the no-claims
boundaries: styling stays token-only (no new inline literal; the orphan lint stays
green); the claim line stays byte-stable; the region/status/collapse contract
stays intact; every hook change stays reflected in `tests/test_web_layout.py` /
`tests/test_web_inline_help.py`; and `docs/USER_GUIDE.md` /
`docs/WEB_VERIFICATION.md` stay untouched (D047 not ratified).

Update `CHANGELOG.md` and this workflow's `OPERATOR_REPORT.md`. Use the maximal
useful number of Codex sub-agents for disjoint remediation tasks. Run
`tests/test_web_layout.py`, `tests/test_web_inline_help.py`,
`tests/test_ui_theme.py`, the desktop rendered-bbox tests, and the full repo suite
(minus the env-gated smoke) before publishing the patch summary.
