---
schema_version: striatum.decision.v1
decision_id: "dec_8195ead3a4d741a493848da2be1086aa"
run_id: "run_4c920dd1311f42a5b0bbac4126af0cbd"
artifact_kind: decision
owner: human
outcome: accepted_with_follow_up
follow_up_required: true
title: "Supersede workflow 0041 with completed workflow 0043"
created_at: "2026-05-13T22:39:30Z"
---

# Supersede workflow 0041 with completed workflow 0043

Decision ID: `dec_8195ead3a4d741a493848da2be1086aa`
Run ID: `run_4c920dd1311f42a5b0bbac4126af0cbd`
Outcome: `accepted_with_follow_up`

## Rationale

Workflow 0041 is blocked at a needs_revision checkpoint with no revision cycle. Workflow 0043 replaced it with RFC 0032, a review-revision route, completed implementation, accepted final review, and landed on main. The stale downstream 0041 jobs should not be claimed.

## Follow-Up

Cancel run 0041 and prune its obsolete branch.
