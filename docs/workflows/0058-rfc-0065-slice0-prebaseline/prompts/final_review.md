# Final Review Prompt

Read the runbook, the RFC 0065 Slice 0 line + §5, `SLICE_0_DECISIONS.md`, the
implementer and remediation patch summaries, the review artifacts, the findings
ledger, the changed files, and the validation evidence.

Verify:

- capture at the three viewports with the 3D `VtkRemoteView` region masked;
- committed in-repo baselines of the current shell + a canonical-env README + a
  `--update-visual-baselines` regeneration path;
- the compare is advisory in Slice 0 (not yet a hard failure);
- no `kayakgen/ui/` source / layout / hook / claim change; `USER_GUIDE.md` /
  `WEB_VERIFICATION.md` untouched; DECISION_LOG D047 not ratified;
- the behavioural browser-acceptance checks and the full repo suite (minus the
  env-gated smoke) are green; `git diff --check` passes.

Note any env-fragility as a Slice 4 successor concern. Publish a final finding
artifact and verdict.
