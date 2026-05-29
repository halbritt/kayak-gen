# Audits

This directory holds runs of the `code_doc_audit` workflow shape
defined by [RFC 0059](../rfcs/0059-three-lane-code-and-doc-audit-workflow.md).
Each run lands as a date-stamped subdirectory containing three lane
findings (`pipeline-integrity/`, `docs-decision-drift/`,
`operator-adoption/`), a `SYNTHESIS.md`, a `REMEDIATION_PLAN.md`, and
(optionally) a `follow-ups/<workflow-id>/` directory for per-batch
landing receipts.

## Index

| Date | Preset | Scope | Findings | Notes |
|---|---|---|---|---|
| [2026-05-25 full_repo](2026-05-25-full-repo-code-doc-audit/) | `full_repo` | Whole repo at HEAD `313dfdd` | 0 critical · 0 high · 1 medium · 3 low · 27 info (+ 3 hallucinated findings discarded) | Fourth run, second `full_repo`. Lane 1 returned 12 positive null findings verifying claim-gate invariants. Lane 2 returned 1 hallucinated finding (RFC files claimed missing; parent thread verified they exist). Lane 3 returned 2 hallucinated findings (mesh labels claimed raw keys but workflow 0037 already landed threshold guidance; stability stage-4 docs claim was contradicted by USER_GUIDE.md:209-210). R1 docs catch-up landed in the audit commit closing AUD-D-001 (ROADMAP date) + AUD-D-004 (WEB_VERIFICATION test cite) + half of AUD-O-003 (USER_GUIDE note about hydrostatics descriptions). R2 (hydro-tab description rendering for AUD-O-003) deferred to follow-up striatum workflow `0039-hydro-tab-description-rendering`. |
| [2026-05-25](2026-05-25-code-doc-audit/) | `release_candidate` | Single upstream commit `b82b544` (second-pass web UI rework; range `fcb8040..b82b544`) | 0 critical · 0 high · 5 medium · 9 low · 18 info | Third run. Lane 1 returned 7 positive null findings (presentation-only claim verified). Lane 2 + Lane 3 surfaced central-docs catch-up + inline-help gaps. R1 docs catch-up landed in the audit commit closing AUD-D-001/002/004 and AUD-O-007/008/009/010/012/013/014/015. AUD-D-003 wontfix. R2 (inline-help / tooltip code batch for AUD-O-001/002/003/004/006) and R3 (hydrostatics row metadata registry for AUD-O-005) deferred to follow-up striatum workflows. |
| [2026-05-23](2026-05-23-code-doc-audit/) | `release_candidate` | Commits `f78e478..3a7f2de` (RFC 0059/0060/0061 + workflows 0029-0034) | 0 critical · 0 high · 2 medium · 5 low · 1 info | Second run. Lane 1 zero-findings; Lane 2 eight verified-pass null findings; Lane 3 surfaced render-test gaps and discoverability nits. R1 + R2 landed in the audit commit; R3/R4/R5 closed by follow-up workflows 0035 + 0036. |
| [2026-05-22](2026-05-22-code-doc-audit/) | `full_repo` | Repo at `f78e478` | 5 high · 5 medium · 4 low · 3 info / null | First dogfood run. All high/medium findings closed by follow-up workflows 0030 (AUD-P-001 + AUD-P-002), 0031 (AUD-P-003 + AUD-P-004), 0032 (AUD-O-004 + AUD-O-005 + AUD-O-006), 0033 (AUD-O-003). Info / null findings remain `open` by intent. |

The latest run is always the most-recent date. Older runs are kept as
provenance per RFC 0059 §2 ("Preserve historical fixtures and dogfood
records as provenance. The audit should flag stale current claims
without rewriting history.").

## Cadence

Per [D041](../DECISION_LOG.md): `full_repo` quarterly + `release_candidate`
before any `CHANGELOG.md` entry that touches a public CLI or schema.
Other presets (`rfc_cluster`, `subsystem`, `adoption_path`) are
operator-triggered as needed.

## How to read a run

1. Start with `<date>/SYNTHESIS.md` — has the lane-diversity caveat,
   the roll-up table, cross-lane duplicates, conflicts, and the
   priority order.
2. `<date>/REMEDIATION_PLAN.md` — the actionable batches (R1, R2, ...)
   and the in-place vs follow-up split.
3. The per-lane `FINDINGS.md` files for evidence and recommended
   actions on individual findings.

## How to run a new one

```bash
TARGET=/home/halbritt/git/kayak-gen
WF=$TARGET/docs/workflows/0029-code-doc-audit/workflow.json

# Fill in SOURCES.md for the new run's preset and scope.
${EDITOR:-vi} $TARGET/docs/workflows/0029-code-doc-audit/SOURCES.md

striatum --repo "$TARGET" workflow validate "$WF" --json
striatum --repo "$TARGET" run prepare       --workflow "$WF" --json
striatum --repo "$TARGET" run start --run-id <run_id> --json
```

The runner lands artifacts under
`docs/audits/<YYYY-MM-DD>-code-doc-audit/`. Update this README's index
table after the run completes.
