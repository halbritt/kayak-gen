# Remediation Prompt — workflow 0056

Read every implementation summary, the integration summary, the
docs-sync summary, and the findings ledger. Fix the **must-fix**
items only.

Keep fixes scoped:
- Preserve every settled decision in `STAGE_2_3_DECISIONS.md`.
- Preserve the byte-stable default for empty registry.
- Preserve the forbidden-claim scrub list and the existing theme
  tokens.
- Update `CHANGELOG.md` only if a remediation changes user-visible
  behavior.

Run focused validation + the full repo suite (minus the env-gated
OpenFOAM smoke) before publishing your patch summary.

Publish the patch summary artifact with proper front matter.
