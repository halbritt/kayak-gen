---
schema_version: striatum.decision.v1
decision_id: "dec_dc5ce467f37b48f295b73ed29477efa6"
run_id: "run_48d834656e604d66aa430eb5f60ea643"
artifact_kind: decision
owner: human
outcome: accepted_with_follow_up
follow_up_required: true
title: "Supersede workflow 0040 with completed workflow 0042"
created_at: "2026-05-13T22:39:24Z"
---

# Supersede workflow 0040 with completed workflow 0042

Decision ID: `dec_dc5ce467f37b48f295b73ed29477efa6`
Run ID: `run_48d834656e604d66aa430eb5f60ea643`
Outcome: `accepted_with_follow_up`

## Rationale

Workflow 0040 is blocked at a needs_revision checkpoint with no revision cycle. Workflow 0042 replaced it with RFC 0031, a review-remediation route, completed implementation, accepted final review, and landed on main. The stale downstream 0040 jobs should not be claimed.

## Follow-Up

Cancel run 0040 and prune its obsolete branch.
