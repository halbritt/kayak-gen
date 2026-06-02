# Role: Remediator

Fix every must-fix finding in the ledger. Keep fixes scoped; introduce no new
design scope. Preserve all `SLICE_4_DECISIONS.md` decisions and the no-claims
boundaries: byte-stable claim line; regenerated baselines as an explained diff
(re-regenerate on the canonical env if needed, keeping the diff explained); the
hard gate + documented tolerance + VTK mask; the SKIP-vs-HARD a11y posture; the
retained behavioural checks; D047 ratified; `docs/WEB_VERIFICATION.md` +
`docs/USER_GUIDE.md` describing only polish + the gate; the RFC 0032 boundary text
unchanged.

Update `CHANGELOG.md` and this workflow's `OPERATOR_REPORT.md`. Use the maximal
useful number of Codex sub-agents for disjoint remediation tasks. Re-run the
`CONTRAST_MANIFEST` gate, the desktop rendered-bbox tests, the visual-baseline
compare on the canonical env, the browser-acceptance profile, and the full repo
suite (minus the env-gated smoke; the known NB-2 services-import-boundary failure
is pre-existing and out of scope) before publishing the patch summary.
