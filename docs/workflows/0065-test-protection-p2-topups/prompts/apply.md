# Apply Prompt — close out the remediation plan

Read the draft and review. Fix must-fix findings only (test-side; the
forbidden paths still apply). Then: update CHANGELOG.md if needed; write
docs/workflows/0065-test-protection-p2-topups/OPERATOR_REPORT.md including
the REMEDIATION PLAN CLOSE-OUT table (every plan item -> workflow/sha or
deferred-with-reason); re-run the full gate with heartbeats (0 failed / 4
documented skips; ruff clean); commit the reviewer's REVIEW.md; publish
SUMMARY.md. Leave the stack on the run branch; do not merge to main.
