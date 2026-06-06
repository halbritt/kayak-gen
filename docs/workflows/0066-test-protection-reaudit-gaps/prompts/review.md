# Review Prompt — re-audit gap remediation

Read the draft artifact, the run branch diff, your role file, and audit §4
rows G1-G10. Apply the checks in your role file in order: scope first, then
G1's break-the-pin proof, then the G2 read-path trace, then the per-item
assertion-honesty checks, then the full gate via scripts/full-gate.sh.
Findings cite file paths and gap ids.

Publish striatum/0066-test-protection-reaudit-gaps/review/REVIEW.md with
verdict: accept / accept_with_findings / needs_revision; never reject.
