# Role: Implementer (workflow 0030)

You land the patch that closes audit findings `AUD-P-001` (high) and
`AUD-P-002` (low) from the 2026-05-22 code+doc audit, as scoped by
[`docs/audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md`](../../../audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md)
batches R3 and R7.

Stay strictly inside the `write_scope.allowed_paths` declared in
`workflow.json`. Do not touch:

- `CHANGELOG.md` — the parent agent records the `### Fixed` entry.
- Any audit `FINDINGS.md` — the parent agent flips status fields.
- Any file outside the allowlist.

Preserve every no-claims boundary. The two valid claim labels are
`unvalidated_hydrostatic_comparison` and
`validated_hydrostatic_comparison`; introduce no third literal. The
empty-registry default must remain byte-stable — replacing
`fit_registry=()` / `registry=()` with the named constant is a
clarity rename, not a behavior change.

Publish `PATCH_SUMMARY.md` to
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0030/` with:

1. The two findings closed (`AUD-P-001`, `AUD-P-002`).
2. The exact file:line locations changed.
3. The verification command and its output (pass counts per file).
4. An explicit confirmation that `CHANGELOG.md` and the audit
   `FINDINGS.md` were NOT touched.
