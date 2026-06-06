---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: author-claude-002
date: 2026-06-06
run: run_e06f2ba0dacd3251d26bdd7365a1575e
job: job_run_e06f2ba0dacd3251d26bdd7365a1575e_apply

# Summary — Workflow 0065: test-protection P2 top-ups (apply)

## Review findings applied

The review (`review/REVIEW.md`, reviewer-codex-001) returned verdict
**accept with no findings**. There were no must-fix findings to apply,
so the apply job changed no test code and no config. The five P2 slices
stand as drafted; `CHANGELOG.md` already carries the workflow 0065
entry (landed with the P2-MYPY-DECIDE slice) and needed no further
update.

Apply-job changes: this summary,
`docs/workflows/0065-test-protection-p2-topups/OPERATOR_REPORT.md`
(item shas, final gate output, audit rows closed — R7/R8/R10 plus the
§3 and §5 notes — and the REMEDIATION PLAN CLOSE-OUT table giving every
plan item's final disposition), and the reviewer's `REVIEW.md`
committed for provenance.

## Final gate evidence (re-run in the apply worktree, 2026-06-06)

`.venv/bin/python -m pytest -q` → exit 0:

```text
1324 passed, 4 skipped, 1 warning in 520.14s (0:08:40)
```

0 failed; the 4 skips are exactly the documented OpenFOAM opt-ins
(`tests/test_cfd_run_stages.py:212`, `:255`;
`tests/test_openfoam_v2512_smoke.py:109`, `:213`) — the pinned
expectation from `docs/RELEASE_DISCIPLINE.md` gate 1. The single
warning is the pre-existing workflow-0063 corrupt-store-repair
`UserWarning` firing inside its own test, as documented in the draft.

`.venv/bin/python -m ruff check kayakgen tests` → exit 0,
"All checks passed!" (pre-existing invalid-`# noqa` warnings on
`kayakgen/ui/web/generate_frontier_view.py:60-65`, untouched).

## Merge-ready branch state

`striatum/0065-test-protection-p2-topups` carries, in order:

1. `61a88b1` workflow 0065 scaffold
2. `5268757` P2-HYDRO-ANCHOR — closed-form external anchor (parabolic
   `distribution_v2` body; volume + LCB vs analytic values, rtol 1e-2,
   derivation in the test comment) — audit R7
3. `891c3c8` P2-CANCEL-DETERMINISTIC — manager-level cancel contract
   runs unconditionally; racy variants demoted to labeled smoke —
   audit R8
4. `7ad3256` P2-REGISTRY-MICROGAPS — ANY-pass, hysteresis branch of
   gate 3a, touching heel-range boundary of gate 9; 0063 digest pin
   byte-identical — audit R10
5. `5069c26` P2-REASON-ENUM — reason-code set derived from the module
   namespace with a count floor — audit §5 note
6. `6095b48` P2-MYPY-DECIDE — vestigial `mypy` removed from `[dev]`
   extras, rationale in CHANGELOG — audit §3 note
7. `8a949a4` draft artifact
8. the apply commit (operator report + this summary + reviewer's
   REVIEW.md)

Audit rows closed: **R7**, **R8**, **R10**, **§3 note**, **§5 note**.
No successor findings: no new test exposed a product bug. Forbidden
paths verified untouched by the reviewer (`kayakgen/`, `scripts/`, the
boundary tests, the 0063 digest pin).

**This run closes out the 2026-06-06 test-protection remediation
plan**: P0 trio → workflow 0062; P1 durable trio → 0063; P1 contract
decisions (D048/D049) → 0064; P2 top-ups → this run.
P2-CLI-NEGATIVES stays deferred pending the bug-hunt NaN-validator
family green-light (plan §5/§6), and the four §7
deferred-indefinitely items are unchanged — full disposition table in
the OPERATOR_REPORT. The slice stack is left on the run branch per the
packet; **merging to `main` is the operator's step**.
