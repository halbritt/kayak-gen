---
schema_version: striatum.synthesis.v1
artifact_kind: synthesis
inputs:
  - striatum/0066-test-protection-reaudit-gaps/DRAFT.md
  - striatum/0066-test-protection-reaudit-gaps/review/REVIEW.md
author: operator
---

# Summary — workflow 0066 (re-audit gap remediation)

All nine actionable gaps from the 2026-06-06 post-remediation re-audit
are closed (G1–G6, G8–G10); G7 and G11 remain deferred by documented
decision. The two SERIOUS rows that held the audit verdict at MIXED are
both landed with executed proof:

- **G1**: the skip-count pin exists and FIRES — sabotage run
  (`EXPECTED_SKIPS=5`) exited 1 on the real subset; both gates carry the
  pin; `scripts/full-gate.sh` is the mechanical pre-merge gate cited by
  RELEASE_DISCIPLINE.md.
- **G2**: `ArtifactStore` reads are SERVE-ONLY-VERIFIED (D050), with the
  review's MF-1 escape (`get_json` second read) fixed in apply and
  pinned by a deny-`read_text` regression test.

Review verdict: **accept_with_findings** (REVIEW.md). MF-1 fixed
(e9e5e27); SF-1 accepted as tripwire; SF-2 documented non-goal.

Final gate (apply, post-MF-1): `scripts/full-gate.sh` exit 0 —
**1348 passed, 4 skipped** in 9:18, `OK (4 skipped == expected 4)`,
ruff clean. User-level `index.sqlite`: 0 rows in all six tables.

Commits on `striatum/0066-test-protection-reaudit-gaps`:
63b0fcd…b0cc086 (draft, one per item), 6abee0a (draft artifact),
e9e5e27 (MF-1 fix), b7e6711 (review + operator report), plus this
summary. Stack left on the run branch; merge to main is the operator's
step. Full closure evidence:
`docs/workflows/0066-test-protection-reaudit-gaps/OPERATOR_REPORT.md`.

Process readout for striatum (the harness this repo exists to test):
mid-run lane-sandbox adoption broke supervised spawn (operator drove
review/apply via the claim loop; codex engine run locally); per-job
worktree release left draft commits dangling (recovered via #184-style
fast-forward); striatum issues #192–#194 filed from this session's
friction.
