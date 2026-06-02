# Role: Reviewer — Traceability

Verify every change under workflow 0057 traces to RFC 0065 §1 or a row in
`SLICE_1_DECISIONS.md`. Flag any scope creep:

- a layout / information-hierarchy change (that is Slice 2);
- a control or empty/loading/error-state change (Slice 3);
- a harness or `WEB_VERIFICATION.md` / `USER_GUIDE.md` change (Slice 4);
- a `data-testid` / `kg-*` hook rename or move;
- a touched `CHIP_*` entry or persistent caption;
- a re-typed or removed existing token (the extension must be additive).

Confirm the token extension is additive and that the inline-literal migration is
a literal→token substitution, not a value change. Findings cite file paths and
decision rows. Use `accept_with_findings` unless the workflow's scope is itself
invalid; in that case use `needs_revision`.
