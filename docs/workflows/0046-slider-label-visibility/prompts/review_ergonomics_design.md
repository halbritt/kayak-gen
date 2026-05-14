# Ergonomics Design Review Prompt

Review only. Write `striatum/0046-slider-label-visibility/ergonomics/REVIEW_ERGONOMICS_DESIGN.md`.
Do not add `author:`, `byline:`, or `Co-Authored-By` metadata. Do not mutate
Striatum state, commit, push, or edit files outside the declared artifact path.

Use maximal useful parallel read-only assistance if available.

Review the desktop and web parameter controls for:

- label legibility and contrast;
- label/slider/value non-overlap at common desktop sizes and narrow web widths;
- whether labels remain visible for long parameter names and units;
- keyboard/focus affordances where already present;
- whether the smallest useful fix preserves the shipped visual system.

Keep recommendations implementation-ready and scoped. Do not propose a broad UI
redesign unless the current structure makes label visibility impossible.

Include `Verdict intent: accept`, `accept_with_findings`, `needs_revision`, or
`reject`.
