# Task — review integrity, process, and the RFC 0008 web layer

Read `SOURCES.md`, `docs/rfcs/0008-web-frontend.md`, and (for the
process track) the seven feature-branch merge commits on `main`. Use
`git log --first-parent --oneline -20` and `git show <merge-sha>` to
inspect each.

Write your review at `striatum/0009-multi-lane-review/claude/REVIEW_INTEGRITY.md`.

Use the same template as the other reviewers; IDs use the prefix
`F-INT-NNN`. Findings on the striatum-bypass and author-byline
tracks carry one of `accept / accept-with-remediation / reject`
instead of severity.

## Track 1 — process and integrity

Investigate:

- **Striatum bypass.** All seven feature branches landed without using
  the striatum runner. The user's earlier directive
  ("use the striatum workflow for all changes except adding RFCs and
  docs") was not honoured. The implementer surfaced this on
  2026-05-10 and saved a feedback memory. Decide whether the work
  needs retroactive workflow records, a `DECISION_LOG.md` row, both,
  or nothing.
- **Author byline.** Every commit on the seven branches is authored
  as `Heath Albritton <halbritt@gmail.com>` with `Co-Authored-By:
  Claude Opus 4.7 <noreply@anthropic.com>`. Heath was AFK during the
  work. Decide whether this attribution stands, or whether the
  branch should be rewritten with a different convention. Note the
  trade-off (rewriting attribution rewrites public history).
- **Commit-message vs. code parity.** Pick at least three commits
  and verify the prose matches the diff. Especially check claims
  like "STL watertight at all `bow_rake` values" (was this actually
  *verified* in the bow_rake=0.5 case?). Flag overstatements.
- **Tests vs. claims.** RFC 0006 §"Acceptance Criteria" mandates
  bit-equal STL and metric output in "Custom" mode. Is this asserted
  by a test? If not, is it covered by transitivity (default Hull →
  golden), or is there a real gap?

## Track 2 — RFC 0008 web layer

Verify:

- `tests/test_web.py` — state round-trip, URL query round-trip,
  unknown-key drop, metrics parity, STL byte structure, factory
  smoke, `load_from_query`. Are these the right tests? Anything
  missing?
- **REST contract (RFC 0008 §5).** The implementer wired controllers
  for `/api/evaluate`, `/api/stl`, `/api/hulls` but did NOT register
  HTTP routes on the Trame aiohttp app. Is this gap acknowledged in
  the commit message? Acceptable for v1?
- **Dockerfile.** Read it. Does it build cleanly conceptually? Does
  `ENV TRAME_HOST=0.0.0.0` interact correctly with the `--host`
  argument the CMD passes?
- **Visual verification gap.** The implementer did not launch a
  Trame server against a browser. Is the headless test coverage a
  reasonable substitute for v1? Or should final acceptance require
  a manual visual sign-off?

## Be candid

Where the implementer overstated, say so. Where caveats are missing
from a commit message but the code is correct, say that too. The
remediation plan in the next job will weigh your findings against
those of the math and architecture reviewers.
