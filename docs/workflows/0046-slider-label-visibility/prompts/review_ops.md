# Ops And Test Review Prompt

Review only. Write `striatum/0046-slider-label-visibility/ops/REVIEW_OPS.md`.
Do not add `author:`, `byline:`, or `Co-Authored-By` metadata. Do not mutate
Striatum state, commit, push, or edit files outside the declared artifact path.

Use maximal useful parallel read-only assistance if available.

Review how to prove the slider-label fix:

- existing tests that cover web layout, theme, and desktop GUI layout;
- gaps for label text, label visibility, contrast tokens, and non-overlap;
- whether browser acceptance should be required or optional;
- practical commands that can run in the current repo venv;
- paths the implementation should avoid.

Return a focused validation matrix and any low-risk test additions that should
be included in the implementation ledger.

Include `Verdict intent: accept`, `accept_with_findings`, `needs_revision`, or
`reject`.
