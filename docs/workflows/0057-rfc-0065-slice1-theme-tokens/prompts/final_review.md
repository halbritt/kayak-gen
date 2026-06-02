# Final Review Prompt

Read the runbook, RFC 0065 §1 + the "Slice 1 observable" Acceptance Criteria,
`SLICE_1_DECISIONS.md`, the implementer and remediation patch summaries, the
review artifacts, the findings ledger, the changed files, and the validation
evidence.

Verify:

- every Slice 1 decision (D1–D8) is reflected in the shipped change, byte-for-byte
  where the decision is a byte-stability gate;
- the token extension is additive; both palettes resolve; the focus-ring + state
  contrast pairs clear their thresholds; the widened orphan lint fails on a
  planted literal and passes on the clean tree; the desktop rendered-bbox tests
  are green;
- the claim line is untouched and the RFC 0032 web-analysis boundary is intact
  (no new route / claim-state / readiness literal; no recoloured chip);
- `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` were not touched and
  DECISION_LOG D047 was not ratified;
- `git diff --check` passes and the full repo suite (minus the env-gated smoke)
  is green.

Publish a final finding artifact and verdict.
