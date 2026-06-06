---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: author-claude-002
date: 2026-06-06
run: run_f090c84339d75237140b6b6f9a681260
job: job_run_f090c84339d75237140b6b6f9a681260_apply

# Summary — Workflow 0064: test-protection P1 contract decisions (apply)

## Review findings applied

The review (`review/REVIEW.md`, reviewer-codex-001) returned verdict
**accept with no findings**. There were no must-fix findings to apply,
so the apply job changed no production code and no test code. The two
decision slices stand as drafted; `CHANGELOG.md` already carries the
workflow 0064 entry (landed with slice 2) and needed no further update.

Apply-job changes: this summary,
`docs/workflows/0064-test-protection-p1-contract-decisions/OPERATOR_REPORT.md`
(slice shas, decisions implemented — D048/D049 — final gate output,
audit rows closed — R1/R2 — bug-ledger rows closed — BUG-001/BUG-026 —
and the workflow D / P2 routing of what remains), and the reviewer's
`REVIEW.md` committed for provenance.

## Final gate evidence (re-run in the apply worktree, 2026-06-06)

`.venv/bin/python -m pytest -q` → exit 0:

```text
1319 passed, 4 skipped, 1 warning in 517.97s (0:08:37)
```

0 failed; the 4 skips are exactly the documented OpenFOAM opt-ins
(`tests/test_cfd_run_stages.py:212`, `:255`;
`tests/test_openfoam_v2512_smoke.py:109`, `:213`) — the pinned
expectation from `docs/RELEASE_DISCIPLINE.md` gate 1. The single warning
is the pre-existing workflow-0063 corrupt-store-repair `UserWarning`
firing inside its own test, as documented in the draft.

`.venv/bin/python -m ruff check kayakgen tests` → exit 0,
"All checks passed!" (pre-existing invalid-`# noqa` warnings on
`kayakgen/ui/web/generate_frontier_view.py:60-65`, untouched).

## Merge-ready branch state

`striatum/0064-test-protection-p1-contract-decisions` carries, in order:

1. `ed651a8` workflow 0064 scaffold
2. `565a8cb` D048 / P1-COMPARE-GATE — `build_comparison_report` calls
   `ensure_objectives_claim_admissible_for_search`; inadmissible
   objectives refuse with the RFC 0044 token unless
   `--explicit-exploratory`; the labeled-exploratory behavior survives
   behind the opt-in with all prior assertions intact
3. `5a22788` D049 / P1-FIT-KIND — `StabilityFitRecord.kind`
   discriminator (additive, `"analytical"` default); graduation tests
   rebuilt on real factory records; `first_class` reachable in
   production (+ the workflow CHANGELOG entry)
4. `7795ac4` draft artifact
5. the apply commit (operator report + this summary + reviewer's
   REVIEW.md)

Decisions implemented: **D048**, **D049**. Audit rows closed: **R1**,
**R2**. Bug-ledger rows closed: **BUG-001** (critical), **BUG-026**
(high). Forbidden paths verified untouched by the reviewer
(`pareto.py`, `registry.py`, `test_stability_fit_registry.py` incl. the
0063 digest pin, `test_services_boundaries.py`,
`test_import_boundaries.py`). With 0064 landed, the remediation plan's
P0 and P1 tiers are complete; what remains is **workflow D** (P2
test-only top-ups, whenever idle). The slice stack is left on the run
branch per the packet; **merging to `main` is the operator's step**.
