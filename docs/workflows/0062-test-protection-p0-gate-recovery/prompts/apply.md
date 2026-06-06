# Apply Prompt — finalize the P0 landing

Read the draft artifact and the review. Fix every must-fix finding, scoped
to the P0 slices — no new design scope. Then:

1. Update `CHANGELOG.md` if the fixes changed anything user-visible.
2. Write `docs/workflows/0062-test-protection-p0-gate-recovery/OPERATOR_REPORT.md`:
   what landed (slice shas), the measured fast-gate runtime + deselect list,
   the final full-gate output, audit rows closed (R0 code half, R3, R4), and
   what remains operator action (installing the pre-push hook via
   `scripts/install-hooks.sh`; merging the run branch to `main`).
3. Re-run the full gate with heartbeats: `.venv/bin/python -m pytest -q`
   (0 failed / 4 documented skips) and `.venv/bin/python -m ruff check
   kayakgen tests` (clean).
4. Publish `striatum/0062-test-protection-p0-gate-recovery/SUMMARY.md`
   enumerating findings applied, final gate evidence, and the merge-ready
   branch state. Leave the slice stack on the run branch; do not merge to
   `main` yourself.
