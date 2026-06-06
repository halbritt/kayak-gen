# Review Prompt — P1 durable-state slices

Read the draft artifact, the run branch diff, your role file, and audit
rows R5/R6/R9. Check, in order:

- Forbidden paths untouched (`git diff main...HEAD --stat`), especially
  `kayakgen/eval/stability/registry.py`.
- Atomic write mechanics (temp + os.replace, same dir); corruption repair
  proven by test; the correct-length-corruption edge addressed or
  explicitly documented out of scope.
- Payload bytes unchanged (design-hash + round-trip tests untouched,
  green).
- SqliteIndex rebuild only on version mismatch; current-version DB
  preserved; warning informative; `kayakgen runs list` healthy after
  rebuild.
- SHA pin present, literal digest, evaluator-version-event comment.
- FULL gate green (run it yourself: 0 failed / 4 documented skips; ruff
  clean). Findings file written BEFORE the long run; heartbeat around it.

Publish `striatum/0063-test-protection-p1-durable-state/review/REVIEW.md`
with file-path-grounded findings and verdict. `accept` /
`accept_with_findings` for apply-fixable issues; `needs_revision` for scope
violations or a red gate; never terminal `reject`.
