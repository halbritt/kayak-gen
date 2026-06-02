# Role: Reviewer — Traceability

Verify every change under workflow 0059 traces to RFC 0065 §2 or a row in
`SLICE_2_DECISIONS.md`. Flag any scope creep:

- a re-typed or removed existing `theme.py` token (the Slice 1 additive boundary);
- a control-state or empty/loading/error-state change (that is Slice 3);
- a harness or `WEB_VERIFICATION.md` / `USER_GUIDE.md` change, or a D047
  ratification (that is Slice 4);
- a touched `CHIP_*` entry or persistent caption;
- a recoloured chip;
- a new REST route / `claim_state` / `Readiness` / `accepted_uses` literal.

Confirm styling is token-only (no new inline dimension/colour literal; orphan lint
green); the `TYPOGRAPHY` roles are applied consistently; the region/status hooks
and the first-viewport + collapse contract survive; and EVERY renamed/moved/removed
`data-testid` / `kg-*` hook is reflected in `tests/test_web_layout.py` (and
`tests/test_web_inline_help.py` where relevant). Findings cite file paths and
decision rows. Use `accept_with_findings` unless the workflow's scope is itself
invalid; in that case use `needs_revision`.
