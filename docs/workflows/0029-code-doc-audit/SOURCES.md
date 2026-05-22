# Sources for audit run

> Operator: fill this in before validating the workflow. Each lane reads
> this file as required context. Keep entries short and link to the canonical
> source rather than duplicating it.

## Preset

`full_repo` | `rfc_cluster` | `release_candidate` | `subsystem` | `adoption_path`

## Run scope

| Lane | Inputs |
|---|---|
| pipeline-integrity | TODO — paths under `kayakgen/eval/`, `kayakgen/services/`, the relevant tests, and any landed RFCs whose claim-gate or readiness contracts touched recently. |
| docs-decision-drift | TODO — the nine files named in `docs/RELEASE_DISCIPLINE.md` public-behavior-change checklist, plus the RFC index. |
| operator-adoption | TODO — `README.md`, `docs/USER_GUIDE.md`, `kayakgen/cli/`, `kayakgen/ui/web/`, `kayakgen/ui/desktop.py`, the env-knob declarations under `kayakgen/eval/cfd/`. |

## RFCs in scope (if `rfc_cluster` preset)

- TODO — RFC NNNN
- TODO — RFC NNNN

## Subsystem paths (if `subsystem` preset)

- TODO — `kayakgen/<subpackage>/`

## Adversary framing per lane

- pipeline-integrity → look for *claim-state drift*: somewhere code admits
  a stronger claim than the evidence supports.
- docs-decision-drift → look for *honest-prose drift*: a doc claim that no
  longer matches source or accepted decisions.
- operator-adoption → look for *invisible-mechanism drift*: a useful
  control surface that exists in code but is undiscoverable from docs.

## Where the audit run artifacts will land

`docs/audits/<YYYY-MM-DD>-code-doc-audit/`:

```
pipeline-integrity/FINDINGS.md
docs-decision-drift/FINDINGS.md
operator-adoption/FINDINGS.md
SYNTHESIS.md
REMEDIATION_PLAN.md
```

The runner sets `RUN_DATE` in the workflow.json variable substitution.
