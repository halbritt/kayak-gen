# Remediation Prompt

Read the implementer patch summary and the findings ledger. Fix the must-fix
items only.

Use the maximal useful number of Codex sub-agents for disjoint remediation
tasks. Keep fixes scoped, preserve all `SLICE_4_DECISIONS.md` decisions and the
accepted no-claims boundaries (byte-stable claim line; regenerated baselines as an
explained diff; the hard gate + documented tolerance + VTK mask; the SKIP-vs-HARD
a11y posture; the retained behavioural checks; D047 ratified; `WEB_VERIFICATION.md`
+ `USER_GUIDE.md` describing only polish + the gate; the RFC 0032 boundary text
unchanged), update `CHANGELOG.md` and this workflow's `OPERATOR_REPORT.md`, and
re-run the `CONTRAST_MANIFEST` gate, the desktop rendered-bbox tests, the
visual-baseline compare on the canonical env, and the full repo suite (minus the
env-gated smoke; the known NB-2 services-import-boundary failure is pre-existing
and out of scope) before publishing.

If baselines must be re-regenerated, do it on the canonical env and keep the diff
explained. Publish the patch summary artifact.
