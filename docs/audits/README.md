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
| [2026-05-23](2026-05-23-code-doc-audit/) | `release_candidate` | Commits `f78e478..3a7f2de` (RFC 0059/0060/0061 + workflows 0029-0034) | 0 critical · 0 high · 2 medium · 5 low · 1 info | Second run. Lane 1 zero-findings; Lane 2 eight verified-pass null findings; Lane 3 surfaced render-test gaps and discoverability nits. |
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

~/git/striatum/.venv/bin/striatum --repo "$TARGET" workflow validate "$WF" --json
~/git/striatum/.venv/bin/striatum --repo "$TARGET" run prepare       --workflow "$WF" --json
~/git/striatum/.venv/bin/striatum --repo "$TARGET" run start --run-id <run_id> --json
```

The runner lands artifacts under
`docs/audits/<YYYY-MM-DD>-code-doc-audit/`. Update this README's index
table after the run completes.
