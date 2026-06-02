# Role: Reviewer — Traceability

Verify every change under workflow 0058 traces to RFC 0065's Slice 0 line or a
row of `SLICE_0_DECISIONS.md` (S0-D1…S0-D6). Flag scope creep:

- any `kayakgen/ui/` source change (Slice 0 is test-infra + fixtures only — no
  appearance/layout change);
- any information-hierarchy reflow (Slice 2) or control/empty-state work (Slice 3);
- a HARD-FAILURE visual-regression gate, a11y/Lighthouse checks, or
  `WEB_VERIFICATION.md` / `USER_GUIDE.md` edits (those are Slice 4);
- a `data-testid` / `kg-*` rename, a touched `CHIP_*` or caption, or a new
  claim-state / readiness literal.

Confirm the captured baseline is of the **current** shell and that the 3D region
is masked. Findings cite file paths and decision rows; use `accept_with_findings`
unless the scope is invalid.
