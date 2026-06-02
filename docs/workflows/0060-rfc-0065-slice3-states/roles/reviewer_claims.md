# Role: Reviewer — Claims and user-facing boundaries

Slice 3 must not move the claim line. Verify:

- `CHIP_SPECS` / `CHIP_LABELS` / `CHIP_CLASSES` are byte-identical; no chip —
  including any failed/empty-state chip — is recoloured into the success palette.
- Every persistent caption is byte-identical: resistance "Raw comparative filter;
  not final prediction." + uncalibrated copy; high-angle GZ "Unvalidated
  hydrostatic comparison; not safety, seaworthiness, calibrated, validated, or
  final-prediction claim."; CFD "Local filesystem CFD jobs on this server only; no
  hosted worker is running." + "Raw solver artifact only; not calibrated or
  validated."; the "not watertight cfd_ready" negation.
- Honestly-disabled controls stay disabled and keep their explanatory copy
  verbatim (watertight-solid, disabled `EXPORT_MENU_ROWS`, Cm reserved-preset,
  `generative_submit_disabled` blocking-reason copy). Disabling is a truthfulness
  affordance — it must not be silently enabled or have its copy softened/dropped.
- Every NEW rendered string introduced by the empty/loading/error states (state
  messages, ARIA labels, tooltips) carries no claim/validation semantics and is
  covered by the extended forbidden-copy scan. No empty/loading/error/failed
  treatment makes an unvalidated/raw/failed result read as a confident, validated,
  or successful claim.
- No new `claim_state` / `Readiness` / `accepted_uses` literal and no new REST
  route (RFC 0032 boundary). The RFC 0033 §8 no-go list stays absent.

Findings cite the file, line, and offending phrase. Use `accept_with_findings`
for issues the remediation lane can fix.
