Final-review workflow 0050.

Read all research, vote, and integration artifacts, plus the changed
`docs/DECISION_LOG.md`, `docs/ROADMAP.md`, `CHANGELOG.md`, and workflow report.

Verify:

- every decision question had a research artifact with external citations;
- every decision question had three independent panel votes;
- every recorded decision has a two-of-three majority;
- dissent and unresolved risks are preserved;
- unresolved or split decisions remain blocking and are not presented as
  accepted decisions;
- roadmap and changelog wording is documentation-only and does not claim
  implementation;
- no runtime, test, packaging, or `.striatum/` tracked files changed;
- `git diff --check` passes.

Publish a final finding artifact at
`striatum/0050-decision-panel-research/final/FINAL_REVIEW.md` with Striatum
`finding` front matter and submit a verdict.
