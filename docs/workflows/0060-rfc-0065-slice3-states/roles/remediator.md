# Role: Remediator

Fix every must-fix finding in the ledger. Keep fixes scoped; introduce no new
design scope. Preserve all `SLICE_3_DECISIONS.md` decisions and the no-claims
boundaries: styling stays token-only (orphan lint green); the claim line and state
copy stay byte-stable; honestly-disabled controls stay disabled with their copy;
every hook change stays reflected in `tests/test_web_layout.py` /
`tests/test_web_inline_help.py`; the forbidden-copy scan stays extended and green;
the Slice 2 region/status/collapse/first-viewport contract stays intact; and
`docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` stay untouched (D047 not
ratified).

Update `CHANGELOG.md` and this workflow's `OPERATOR_REPORT.md`. Use the maximal
useful number of Codex sub-agents for disjoint remediation tasks. Run
`tests/test_web_layout.py`, `tests/test_web_inline_help.py`, `tests/test_ui_theme.py`,
the desktop rendered-bbox tests, and the full repo suite (minus the env-gated
smoke; the known NB-2 services-import-boundary failure is pre-existing and out of
scope) before publishing the patch summary.
