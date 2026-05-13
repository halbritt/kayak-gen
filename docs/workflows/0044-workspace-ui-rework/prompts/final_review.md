Operator parallelism instruction: use the maximal number of useful sub-agents
or parallel workers available for independent verification. Keep scopes
disjoint, preserve this assigned Striatum role, and state what sub-agent help
was used in the artifact.

Read RFC 0033, the findings ledger, the implementation patch summary, and the
changed files.

Produce
`striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md`.

Verdict must be `accept` or `needs_revision`. Verify that:

- The three-region workspace shell renders with the expected region test
  ids on web, and that the desktop GUI uses the same regions.
- Ergonomics/design ledger findings are resolved or explicitly deferred:
  first-viewport scan path, parameter editing, warning triage, responsive
  collapse, focus/keyboard behavior, and desktop/web conceptual parity.
- Every chip, persistent banner, and status-bar segment renders the exact
  copy quoted in RFC 0033 §4–§6 and its acceptance criteria. RFC 0033 is the
  canonical source for scope, copy, and acceptance criteria.
- The forbidden-claim regression tests cover every no-go string in RFC 0033
  §8 and pass.
- `kayakgen/ui/theme.py` is the only home for hex colour literals and named
  colours under `kayakgen/ui/`, enforced by an automated lint test.
- The structured `Advisory` record is additive: `DesignAdvisory.warnings`
  remains a `tuple[str, ...]` and existing callers continue to work.
- Every existing REST route keeps its JSON shape, the share URL round-trip
  is unchanged, and the desktop STL export still writes
  `<stem>_hull.stl` / `<stem>_deck.stl`.

If `needs_revision`, name the exact findings that must return to
`implement_findings`. Do not include any byline or any line beginning with
`author:`.
