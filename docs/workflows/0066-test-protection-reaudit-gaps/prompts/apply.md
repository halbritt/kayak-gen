# Apply Prompt — close out the re-audit gap queue

Read the draft and review. Fix must-fix findings only (write scope
unchanged; the forbidden paths still apply). Refresh the fast-gate.sh
header counts if fixes changed test totals. Write
docs/workflows/0066-test-protection-reaudit-gaps/OPERATOR_REPORT.md:
items landed (shas), gap rows G1-G6 + G8-G10 each with one-line closure
evidence, the G2 DECISION_LOG row id, the G5 open question, and the
standing-deferral table (G7 → 0065 SUMMARY NaN-sweep green-light; G11 →
externally-authored fixtures). Re-run scripts/full-gate.sh with heartbeats
(0 failed / exactly 4 documented skips; ruff clean); verify user-level
index.sqlite byte-identical. Commit the reviewer's REVIEW.md with the
close-out. Publish SUMMARY.md. Leave the stack on the run branch; do not
merge to main.
