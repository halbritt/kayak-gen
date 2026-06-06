---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: author-claude-002
date: 2026-06-06
run: run_2198d739c43270edeb3ee93f93160b97
job: job_run_2198d739c43270edeb3ee93f93160b97_apply

# Summary — Workflow 0063: test-protection P1 durable-state hardening (apply)

## Review findings applied

The review (`review/REVIEW.md`, reviewer-codex-001) returned verdict
**accept with no findings**. There were no must-fix findings to apply,
so the apply job changed no production code and no test code. The three
P1 slices stand as drafted; `CHANGELOG.md` already carries the workflow
0063 entry (landed with slice 3, the 0062 convention) and needed no
further update.

Apply-job changes: this summary,
`docs/workflows/0063-test-protection-p1-durable-state/OPERATOR_REPORT.md`
(slice shas, final gate output, audit rows closed — R5, R6, R9, §6
sha-pin — documented residuals, and the workflow C / D routing of what
remains), and the reviewer's `REVIEW.md` committed for provenance.

## Final gate evidence (re-run in the apply worktree, 2026-06-06)

`.venv/bin/python -m pytest -q -ra` → exit 0:

```text
1315 passed, 4 skipped, 1 warning in 528.97s (0:08:48)
```

0 failed; the 4 skips are exactly the documented OpenFOAM opt-ins
(`tests/test_cfd_run_stages.py:212`, `:255`;
`tests/test_openfoam_v2512_smoke.py:109`, `:213`) — the pinned
expectation from `docs/RELEASE_DISCIPLINE.md` gate 1. The single warning
is the slice-1 repair path firing on the staged-stale CFD rerun test, as
documented in the draft.

`.venv/bin/python -m ruff check kayakgen tests` → exit 0,
"All checks passed!" (pre-existing invalid-`# noqa` warnings on
`kayakgen/ui/web/generate_frontier_view.py:60-65`, untouched).

R3 isolation held during the run: the operator's
`~/.local/share/kayakgen/index.sqlite` was byte-identical before and
after (`mtime_ns=1780730948 size=90112`).

## Merge-ready branch state

`striatum/0063-test-protection-p1-durable-state` carries, in order:

1. `0a87838` workflow 0063 scaffold
2. `347f706` P1-STORE-ATOMIC — atomic content-address writes +
   corrupt-dedupe repair (+ atomic utf-8 `io/json.py` writes, audit R9)
3. `83ad15b` P1-SQLITE-VERSION — `PRAGMA user_version` stamp,
   rebuild-not-migrate on bump
4. `77be4e5` P1-SHA-PIN — literal-digest tamper-evidence tripwire
   (test-only; registry untouched) + the workflow CHANGELOG entry
5. `d953d1c` draft artifact
6. the apply commit (operator report + this summary + reviewer's
   REVIEW.md)

Audit rows closed: **R5**, **R6**, **R9**, **§6 sha-pin**. What remains
is routed per the remediation plan: **workflow C** (FIT-KIND,
COMPARE-GATE contract decisions) and **workflow D** (P2 test-only
top-ups). The slice stack is left on the run branch per the packet;
**merging to `main` is the operator's step**.
