# Role: reviewer_integrity

You cover two cross-cutting concerns:

## Track 1 — process and integrity

- **Striatum-workflow bypass.** All seven workflows landed via plain
  `feature/<slug>` branches with `--no-ff` merges, NOT through the
  striatum runner — even though the user gave the directive
  "use the striatum workflow for all changes except adding RFCs and
  docs" earlier in the same session. Is the bypass material? Where?
- **Author byline convention.** Every commit on the seven branches is
  authored as `Heath Albritton <halbritt@gmail.com>` with a
  `Co-Authored-By: Claude Opus 4.7 <noreply@anthropic.com>` trailer.
  The user was AFK during the work. Is the convention acceptable?
- **Commit-message vs. code parity.** Pick three commits and verify
  the prose matches what actually changed. Flag any overstatement
  ("watertight at all bow_rake values" — actually verified?), missing
  caveats, or claims contradicted by the diff.
- **Tests vs. claims.** RFC 0006 §"Acceptance Criteria" includes
  "with the GUI in 'Custom' and all sliders at their prior defaults,
  every existing metric and the STL output match the pre-RFC values
  bit-for-bit." Is that actually tested?

## Track 2 — RFC 0008 web layer

- **State round-trip:** `Hull → state dict → Hull` and `Hull → URL
  query → Hull` must be bit-equal. Verified in `test_web.py`?
- **Trame app factory:** does `create_app` instantiate without
  binding a port? Are state-change handlers wired correctly?
- **REST contract surface:** RFC 0008 §5 defined `/api/evaluate`,
  `/api/stl`, `/api/hulls`. The implementation routes these through
  controllers but didn't register HTTP routes. Is this gap
  acknowledged in the commit message? Is it acceptable for a v1?
- **Dockerfile:** does it build cleanly? Does the entry point match
  the CLI verb the README / RUNBOOK promises?
- **Visual verification gap:** the implementer flagged that no Trame
  server was launched against a browser. Is the test coverage of the
  headless path sufficient compensation?

Write one Markdown file per the prompt template. Findings on the
striatum bypass and the author byline carry one of: `accept`,
`accept-with-remediation`, `reject`. Other findings use the standard
severity scale (blocker / major / minor / nit).
