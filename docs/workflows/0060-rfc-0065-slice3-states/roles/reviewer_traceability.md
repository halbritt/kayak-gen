# Role: Reviewer — Traceability

Verify every change under workflow 0060 traces to RFC 0065 §3 or a row in
`SLICE_3_DECISIONS.md`. Flag any scope creep:

- a layout/hierarchy re-flow beyond control + state styling (Slice 2 boundary);
- a re-typed or removed existing `theme.py` token (Slice 1 additive boundary);
- a harness or `WEB_VERIFICATION.md` / `USER_GUIDE.md` change, or a D047
  ratification (Slice 4);
- a touched `CHIP_*` entry or persistent caption; a recoloured chip;
- a new REST route / `claim_state` / `Readiness` / `accepted_uses` literal.

Confirm control states derive from Slice 1 tokens and apply uniformly; the
focus-ring control state deferred from Slice 2 is reintroduced uniformly (not a
partial subset); honestly-disabled controls keep their copy; each panel renders an
explicit empty/loading/error state with a stable hook; state copy is byte-stable;
styling is token-only (orphan lint green); every hook change is reflected in
`tests/test_web_layout.py` + `tests/test_web_inline_help.py`; the forbidden-copy
scan was extended to every new rendered string; and the Slice 2 region/status/
collapse/first-viewport contract holds. Findings cite file paths and decision
rows. Use `accept_with_findings` unless the workflow's scope is itself invalid; in
that case use `needs_revision`.
