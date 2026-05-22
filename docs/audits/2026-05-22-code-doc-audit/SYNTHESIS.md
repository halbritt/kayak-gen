# Audit Synthesis — 2026-05-22 code+doc audit

Date: 2026-05-22
Workflow shape: `code_doc_audit` (proposed in RFC 0059)
Preset: `full_repo`
Source-of-truth commit: f78e478 on `main`

## Lane-diversity caveat

This run was executed by a single agent (Claude Opus 4.7) using one main
session plus two parallel `Explore` subagents (one for Lane 2, one for
Lane 3). The provider-diversity that the existing
`docs/workflows/0009-multi-lane-review` precedent achieved
(claude / codex / gemini across three lanes) was NOT achieved here. Reading
postures were kept distinct (pipeline-integrity vs docs-drift vs
operator-adoption) and the lane outputs were cross-verified against source
before promotion, but the synthesis honestly reflects one-agent provenance.
A future re-run via `docs/workflows/0029-code-doc-audit/` (scaffolded as
part of this remediation) should dispatch three providers.

## Findings rolled up

13 findings across three lanes.

| ID | Lane | Severity | Category | Follow-up path |
|---|---|---|---|---|
| AUD-P-001 | pipeline-integrity | high | claim_gate | source/test work |
| AUD-P-002 | pipeline-integrity | low | claim_gate | source clarity |
| AUD-P-003 | pipeline-integrity | medium | test_gap | source/test + docs |
| AUD-P-004 | pipeline-integrity | low | test_gap | test coverage |
| AUD-P-005 | pipeline-integrity | info | claim_gate | wontfix (null) |
| AUD-D-001 | docs-decision-drift | high | docs_drift | docs fix |
| AUD-D-002 | docs-decision-drift | high | docs_drift | docs fix |
| AUD-D-003 | docs-decision-drift | medium | docs_drift | docs fix + paired with AUD-P-003 |
| AUD-D-004 | docs-decision-drift | low | docs_drift | docs fix |
| AUD-D-005 | docs-decision-drift | info | rfc_status | wontfix (null) |
| AUD-O-001 | operator-adoption | high | docs_drift | docs fix |
| AUD-O-002 | operator-adoption | high | docs_drift | docs fix |
| AUD-O-003 | operator-adoption | medium | operator_ergonomics | new RFC |
| AUD-O-004 | operator-adoption | medium | operator_ergonomics | small workflow |
| AUD-O-005 | operator-adoption | medium | operator_ergonomics | source change |
| AUD-O-006 | operator-adoption | low | operator_ergonomics | source change |
| AUD-O-007 | operator-adoption | low | operator_ergonomics | docs fix |
| AUD-O-008 | operator-adoption | info | operator_ergonomics | wontfix (null) |

Severity totals: 5 high · 5 medium · 4 low · 3 info / null findings.

## Cross-lane duplicates and overlap

- **AUD-D-001 / AUD-D-002 / AUD-O-001 / AUD-O-002 cluster around the same
  root cause**: the `RELEASE_DISCIPLINE.md` public-behavior-change checklist
  was not applied when RFC 0057 stage 4 (2026-05-18) and RFC 0058 stages 2-3
  (2026-05-21) landed. Four downstream docs (USER_GUIDE for two surfaces,
  ARCHITECTURE_MAP, the `mesh-evidence` section) were skipped. Treat as one
  remediation batch (R1 below).
- **AUD-D-003 / AUD-P-003 are paired**: glossary terms missing (AUD-D-003)
  and the vocabulary-coverage test not enforcing them (AUD-P-003). Land
  together so the test catches future regressions of the docs fix. Treat as
  one remediation batch (R2).
- **AUD-O-005 / AUD-O-006 are both `cfd` CLI ergonomics**: same author
  surface (`kayakgen/cli/main.py`), same operator audience. Treat as one
  remediation batch (R5).

## Conflicts between lanes

None. Lane 2 originally reported a `kayakgen runs jobs` documentation gap
that main-thread verification proved false (`docs/USER_GUIDE.md:477`
documents it). That finding was dropped before this synthesis rather than
escalated as a conflict.

## Priority order

Highest-leverage first (driven by the remediation plan):

1. **R1 — Discipline-checklist catch-up** (AUD-D-001 + AUD-D-002 +
   AUD-O-001 + AUD-O-002): one docs batch closes four high-severity
   findings. Zero code risk.
2. **R2 — Glossary + vocab-coverage test extension** (AUD-D-003 + AUD-P-003):
   one combined docs + test slice; restores the regression net that the
   project already invested in.
3. **R3 — Stability-fit literal widening + round-trip test** (AUD-P-001):
   small contract slice that removes the only latent claim-gate bug found
   this audit. Needs its own striatum workflow per project memory
   "Striatum workflow is required for code changes".
4. **R4 — CLI ergonomics: runs header + filter docs** (AUD-O-004): one
   small workflow.
5. **R5 — CFD error-message + prepare-success polish** (AUD-O-005 +
   AUD-O-006): one small workflow.
6. **R6 — Generate-panel form-builder labels and tooltips** (AUD-O-003):
   UX-scope; warrants its own RFC.
7. **R7 — fit_registry shared constant** (AUD-P-002): docs-clarity slice,
   defer or bundle with R3.
8. **R8 — GenerativeJob state-vocabulary regression test** (AUD-P-004):
   small test slice; bundle with R2 if convenient.
9. **R9 — PRD high-angle GZ wording** (AUD-D-004): one-sentence docs fix.

Severity-info / null findings (AUD-P-005, AUD-D-005, AUD-O-008) need no
action; they are recorded so a future audit does not re-derive them.

## Notes for the workflow scaffold

- The `docs/workflows/0029-code-doc-audit/` scaffold this audit produces
  should mirror `0009-multi-lane-review` lane assignment (claude / codex /
  gemini) but with the three audit lanes from RFC 0059 (pipeline-integrity,
  docs-decision-drift, operator-adoption). The synthesis + remediation-plan
  jobs are single-lane downstream.
- Use this audit's findings + remediation plan as the dogfood reference
  RFC 0059 Step 4 asks for; CHANGELOG entry referencing the run lands as
  part of the R1 remediation batch.
