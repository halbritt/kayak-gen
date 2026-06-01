---
kind: operator_report
workflow: 0043-rfc-0043-stage-4-stability-rig-pipeline
operator: operator-claude-opus-4.8
date: 2026-06-01
---

# OPERATOR REPORT — RFC 0043 stage 4 CLI-completion

## Assignment
Drive RFC 0043 stage 4 to completion. The claim-integrity **core** is already
landed + green on `main` (commit `8e5c68e`): `registry.py` 13-gate loader,
`ANALYTICAL_EVALUATOR_VERSION`, evaluator site-1 swap, `test_stability_fit_registry.py`
(19/19). Remaining surface = `CLI_COMPLETION_HANDOFF.md` §1–§8 (CLI + 2 web
swaps + 3 test files + docs) **plus** end-to-end `hull_class` plumbing
(operator-confirmed scope expansion this session).

## Mode / branch policy
- Run mode: **prepare + start a new focused completion run** (not a resume —
  all prior 0043 runs are terminal).
- Branch: `striatum/0043-rfc-0043-stage-4-stability-rig-pipeline-cli-completion`
  (workflow `branch.mode: confirm`).
- Land policy (operator-confirmed): merge to `main` **and push to `origin/main`**
  after both build reviews `accept` + §7 gate green.

## Approach (operator-confirmed)
Focused completion workflow: `implement` (root, claude) → `review_build_claude`
(ergonomics_dx) + `review_build_codex` (threat_model), `needs_revision` cycles
back to `implement` (max 2). The parent `workflow.json` `implement` write_scope
is stale/pre-pivot (forbids `kayakgen/ui/`, omits `stability_cli.py`/`registry.py`/
`conftest.py`/`SOURCES.md`), so a new completion workflow with the correct
write_scope is authored rather than re-running the parent graph.

## Scope decisions
- **hull_class plumbed now** (was a flagged gap): `Hull` carries no `hull_class`,
  so `resolve_analytical_claim_label` always reads `None` and the label never
  flips for a real hull. Implement lane adds `hull_class` to `Hull` (reusing the
  existing calibration-envelope vocabulary) + a real-`Hull` production-flip
  integration test. Gated by the codex threat_model reviewer (wrong/over-broad
  class could flip a hull it should not cover).
- Out of scope (recorded as DECISION_LOG follow-ups by the implement lane): the
  two synthesis §5 resistance-side findings (opaque-token bypass;
  `AcceptedFitRecord` fixture-binding).

## Daemon state
- striatum 2.8.0; daemon + codex MCP live; `doctor ok: true` after cleanup.
- No live runs; 21 prior runs all terminal.

## Friction log
- **F1 (resolved):** `doctor ok:false` from 4 orphaned supervisors
  (`tmux_session_missing`) left by dead runs. Stopped via `supervise stop
  <session-id> --reason`; doctor now `ok:true`, problems=[].
- **F2 (open, cosmetic):** `striatum list workflows` errors
  `column "snapshot_sha256" does not exist (SQLSTATE 42703)` — DB migration
  drift. Does not block `run prepare`/`start`. Follow-up: striatum-side migration.
- **F3 (history / risk):** stop-reasons on prior runs show repeated wedges
  ("daemon run wedged on codex terminal reject", "synth env-block, no unwedge
  verb", "agy folder-trust"). The previous operator ended up **hand-driving**
  implement+build-review and landing the core directly. Supervised lanes are
  flaky on this host → Phase 2 must watch for wedges and be ready to
  hand-drive / `supervise stop --replace` / fall back to the claim loop.
- **F4 (stale):** open blocker `blk_e2e5575a` from a failed run (write_scope
  violation on a synth/design job) — tied to a dead run; not acted on.

## Next action
Author + validate `completion/workflow.json` + the implement task prompt
(Phase 1), then prepare/start/drive (Phase 2).

## Log
- 2026-06-01: Operator session start. Loaded handoff + synthesis + operator
  skill. Confirmed core green (19/19). Cleaned 4 orphaned supervisors →
  `doctor ok:true`. Confirmed scope decisions with principal (focused workflow;
  plumb hull_class; merge+push). Report created.
