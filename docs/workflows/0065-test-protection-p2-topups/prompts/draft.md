# Draft Prompt — P2 top-ups

Read the packet objective, your role file, audit rows R7/R8/R10 + the §3
and §5 notes, plan §5, and SOURCES.md. Implement the five items in packet
order, one commit each, inside the write scope. Key file anchors:

- tests/test_hydrostatics.py — existing property tests (scaling law, GM0
  monotonicity, Cm vs section_area) show the house style for the anchor.
- tests/test_generative_jobs_subprocess.py — _controlled_cancel_runner and
  test_subprocess_runner_cancel_flag_requires_resumable_and_cleans_flag are
  the deterministic pattern to extend to the manager level.
- tests/test_stability_fit_registry.py — _fixture/_packet/_fit/_stage
  helpers; gate constants in kayakgen/eval/stability/registry.py (READ
  ONLY). The digest-pin test from 0063 must remain byte-identical.

Slice gate after item 5: .venv/bin/python -m pytest -q → 0 failed, 4
documented skips; ruff clean. Heartbeat before/after.

Publish striatum/0065-test-protection-p2-topups/DRAFT.md with per-item
shas + diffstat, the anchor derivation (or documented fallback), the
deterministic-cancel evidence, the three micro-gap test names, the
reason-enum derivation, and the full-gate tail. Use the packet's byline.
