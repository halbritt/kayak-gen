# Apply Prompt — finalize the durable-state landing

Read the draft artifact and the review. Fix every must-fix finding, scoped
to the three slices. Then:

1. Update `CHANGELOG.md` if fixes changed anything user-visible.
2. Write `docs/workflows/0063-test-protection-p1-durable-state/OPERATOR_REPORT.md`:
   slices landed (shas), audit rows closed (R5, R6, R9, §6 sha-pin), gate
   evidence, what remains (workflows C and D per the plan routing).
3. Re-run the full gate with heartbeats (0 failed / 4 documented skips;
   ruff clean).
4. Commit the reviewer's REVIEW.md alongside the close-out, publish
   `striatum/0063-test-protection-p1-durable-state/SUMMARY.md`, and leave
   the slice stack on the run branch; do not merge to `main`.
