# Role: Reviewer — Claims and user-facing boundaries

Slice 1 must not move the claim line. Verify:

- `CHIP_SPECS` / `CHIP_LABELS` / `CHIP_CLASSES` are byte-identical to pre-slice;
  no chip's label, semantic class, or colour/background/text token changed. No
  raw/advisory chip is recoloured into the success palette.
- Every persistent caption is unchanged: the resistance "Raw comparative filter;
  not final prediction." and uncalibrated copy; the high-angle GZ copy; the CFD
  "Local filesystem CFD jobs on this server only; no hosted worker is running."
  and "Raw solver artifact only; not calibrated or validated."; and the "not
  watertight cfd_ready" negation.
- No new `claim_state` / `Readiness` / `accepted_uses` literal and no new REST
  route (the RFC 0032 web-analysis boundary). The RFC 0033 §8 no-go list stays
  absent from rendered output.
- New state/focus token *names* carry no claim semantics (a CSS variable named
  for a UI state, not for a validation level).

Findings cite the file, line, and offending phrase. Use `accept_with_findings`
for issues the remediation lane can fix.
