# Remediation Prompt

Read the implementer patch summary and the findings ledger. Fix the must-fix
items only.

Use the maximal useful number of Codex sub-agents for disjoint remediation
tasks. Keep fixes scoped, preserve all `SLICE_1_DECISIONS.md` decisions and the
accepted no-claims boundaries (token values stay equal to the literals they
replace; the claim line stays byte-stable; `USER_GUIDE.md` /
`WEB_VERIFICATION.md` stay untouched), update `CHANGELOG.md` where appropriate,
and run `tests/test_ui_theme.py`, the desktop rendered-bbox tests, and the full
repo suite (minus the env-gated smoke) before publishing.

Publish the patch summary artifact.
