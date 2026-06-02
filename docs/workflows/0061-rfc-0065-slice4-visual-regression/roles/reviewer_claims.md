# Role: Reviewer — Claims and user-facing boundaries

Slice 4 must not move the claim line. Verify:

- `CHIP_SPECS` / `CHIP_LABELS` / `CHIP_CLASSES` are byte-identical; no chip is
  recoloured into the success palette.
- Every persistent caption is byte-identical: resistance "Raw comparative filter;
  not final prediction." + uncalibrated copy; high-angle GZ "Unvalidated
  hydrostatic comparison; not safety, seaworthiness, calibrated, validated, or
  final-prediction claim."; the CFD local-jobs + raw-artifact banners; the "not
  watertight cfd_ready" negation.
- The regenerated screenshot baselines do not bake an unvalidated/raw/failed
  result into a confident, validated, or calibrated visual treatment (the masked
  3D region aside — chips/captions still read raw/advisory where required).
- The docs updates introduce NO new capability/availability/claim language and no
  RFC 0033 §8 no-go term: `docs/WEB_VERIFICATION.md` and `docs/USER_GUIDE.md`
  describe only the polish behaviour and the verification gate; the RFC 0032
  web-analysis boundary text is unchanged; the D047 ratification records the
  harness shape only (committed PNG baselines + tolerance) and asserts no analysis
  claim.
- No new `claim_state` / `Readiness` / `accepted_uses` literal and no new REST
  route.

Findings cite the file, line, and offending phrase. Use `accept_with_findings`
for issues the remediation lane can fix.
