# Remediation Prompt

Read the implementer patch summary and the findings ledger. Fix the must-fix
items only.

Use the maximal useful number of Codex sub-agents for disjoint remediation
tasks. Keep fixes scoped, preserve all `SLICE_2_DECISIONS.md` decisions and the
accepted no-claims boundaries (token-only styling; byte-stable claim line; the
region/status/collapse contract intact; every hook change reflected in
`tests/test_web_layout.py` / `tests/test_web_inline_help.py`; `USER_GUIDE.md` /
`WEB_VERIFICATION.md` untouched; D047 not ratified), update `CHANGELOG.md` and
this workflow's `OPERATOR_REPORT.md`, and run `tests/test_web_layout.py`,
`tests/test_web_inline_help.py`, `tests/test_ui_theme.py`, the desktop
rendered-bbox tests, and the full repo suite (minus the env-gated smoke) before
publishing.

Publish the patch summary artifact.
