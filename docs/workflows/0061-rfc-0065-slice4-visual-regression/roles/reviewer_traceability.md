# Role: Reviewer — Traceability

Verify every change under workflow 0061 traces to RFC 0065 §5 or a row in
`SLICE_4_DECISIONS.md`. Confirm in particular:

- baselines regenerated on the canonical env with an explained diff, BEFORE the
  compare was flipped to hard (D1);
- the visual compare is a HARD gate with a documented per-viewport tolerance + the
  VTK mask + the SKIP/HARD posture (D2, D3);
- the a11y checks (focus order, visible ring from the Slice 1 token, hit-target,
  contrast) are present; `CONTRAST_MANIFEST`/`theme.py` changes are additive; a11y
  code fixes are minimal + token-sourced (D4);
- Lighthouse ≥ 90 recorded, not a mandatory pytest gate (D5);
- the retained behavioural checks remain (D6);
- `docs/WEB_VERIFICATION.md` (procedure + table), `docs/USER_GUIDE.md`, and the
  D047 ratification (`proposed` → `accepted`) landed (D8).

Flag scope creep: a new analysis surface / REST route / claim-state / readiness /
accepted_uses literal; a `CHIP_*` or persistent-caption change; a recoloured chip;
a layout re-flow beyond minimal a11y fixes; a non-additive `CONTRAST_MANIFEST` /
`theme.py` change; or new capability/availability language in the docs. Findings
cite file paths and decision rows. Use `accept_with_findings` unless the workflow's
scope is itself invalid; in that case `needs_revision`.
