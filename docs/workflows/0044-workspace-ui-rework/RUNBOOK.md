# Runbook - workflow 0044 workspace UI rework

## Purpose

Implement RFC 0033 as the conservative successor to the ad-hoc UI
surfaces in `kayakgen/ui/web/app.py` and `kayakgen/ui/desktop.py`. The
run should land a single three-region workspace shell, a semantic
theme module, claim/readiness/status chips wired to the existing
backend literals, structured advisory records, and a status bar — all
while preserving every existing REST route, CLI behaviour, and share
URL round-trip.

## Review and revision route

The workflow starts with `review_remediation`, which prepares the
first review packet. If any first-pass review returns
`needs_revision`, Striatum cycles that review back through
`review_remediation` once before re-running the review.

After all three review lanes accept or accept with findings, the run
proceeds through `findings_ledger`, `implement_findings`, and
`final_review`. A final review `needs_revision` cycles once back to
`implement_findings`.

## Commands

```bash
WF=docs/workflows/0044-workspace-ui-rework/workflow.json

STRIATUM_DAEMON_REQUIRED=0 STRIATUM_TEST_HARNESS=1 \
  /home/halbritt/git/kayak-gen/.venv/bin/striatum --repo . workflow validate "$WF"

/home/halbritt/git/kayak-gen/.venv/bin/striatum --repo . run prepare --workflow "$WF" --json
```

## Boundaries

Keep implementation conservative.

- No new backend capabilities. No hosted CFD worker. No multi-user
  share. No calibrated-model resistance. No high-angle GZ
  visualisation. No web-side mesh-package authoring API.
- The single permitted backend touch is the structured `Advisory`
  record on `DesignAdvisory`. Keep `warnings: tuple[str, ...]`
  unchanged for backward compatibility.
- All existing REST routes (`/api/evaluate`, `/api/stl`,
  `/api/cfd/*`, `/api/hulls/*`) must keep their JSON shape.
- All existing controller helpers must keep their signatures; new
  view models are additive.
- The shared theme module is the only authorised home for hex colour
  literals and named colours under `kayakgen/ui/`. Enforce via a lint
  test.
- Every forbidden-claim string from RFC 0033 §8 must be covered by an
  automated regression test.
