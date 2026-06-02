# Final Review Prompt

Read the runbook, RFC 0065 §2 + the "Slice 2 observable" Acceptance Criteria,
`SLICE_2_DECISIONS.md`, the implementer and remediation patch summaries, the
review artifacts, the findings ledger, the changed files, and the validation
evidence.

Verify:

- every Slice 2 decision (D1–D8) is reflected in the shipped change, byte-for-byte
  where the decision is a byte-stability gate;
- the shell, toolbar, four status segments, and Generate panel are re-flowed onto
  the Slice 1 tokens and one `TYPOGRAPHY` hierarchy; styling is token-only (the
  widened orphan lint is green); any new `theme.py` token is additive and
  both-palette/contrast-covered;
- the region (`region-params`/`-geometry`/`-review`) and status (four `status-*`
  segments + `workspace-status-bar`) hooks survive; the 1440×900 first-viewport
  contract and the ≤960 px collapse hold and are restyled, not removed;
- every renamed/moved/removed `data-testid` / `kg-*` hook is reflected in
  `tests/test_web_layout.py` (and `tests/test_web_inline_help.py`); no orphaned
  assertion remains;
- the claim line is untouched and the RFC 0032 web-analysis boundary is intact
  (no new route / claim-state / readiness literal; no recoloured chip; the §8
  no-go list absent);
- `docs/USER_GUIDE.md` / `docs/WEB_VERIFICATION.md` were not touched and
  DECISION_LOG D047 was not ratified;
- `git diff --check` passes and the full repo suite (minus the env-gated smoke)
  is green.

Publish a final finding artifact and verdict.
