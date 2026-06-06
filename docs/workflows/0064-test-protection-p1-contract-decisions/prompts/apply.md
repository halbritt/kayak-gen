# Apply Prompt — finalize the contract landing

Read the draft and review. Fix must-fix findings only. Then: update
CHANGELOG.md if needed; write docs/workflows/0064-test-protection-p1-
contract-decisions/OPERATOR_REPORT.md (D048/D049 implemented, R1/R2 +
BUG-001/BUG-026 closed, gate evidence, remaining: workflow D / P2); re-run
the full gate with heartbeats (0 failed / 4 documented skips; ruff clean);
commit the reviewer's REVIEW.md; publish SUMMARY.md. Leave the stack on the
run branch; do not merge to main.
