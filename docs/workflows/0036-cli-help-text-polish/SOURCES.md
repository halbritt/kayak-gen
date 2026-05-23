# Sources for workflow 0036 — CLI help-text polish

> Operator: this file is the per-run context manifest. Each job reads
> it as required context. Keep entries short and link to the canonical
> source rather than duplicating it.

## Audit findings in scope

- **AUD-O-011 (low, partial-closed)** —
  `kayakgen runs list --kind` help text does not enumerate the valid
  kinds the way `runs jobs` enumerates `--state` and `--kind`. See
  [`docs/audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md`](../../audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md)
  AUD-O-011 row, and the remediation plan
  [`R5`](../../audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md)
  batch.

- **AUD-O-012 (low)** —
  `kayakgen.ui.gui_params.hull_from_gui_params` DeprecationWarning
  names "RFC 0061" but provides no on-disk path. A downstream consumer
  hitting the warning has no breadcrumb. See
  [`docs/audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md`](../../audits/2026-05-23-code-doc-audit/operator-adoption/FINDINGS.md)
  AUD-O-012 row, and remediation plan
  [`R3`](../../audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md)
  batch.

## Antecedent RFC (context only)

- [`docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md`](../../rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md)
  is the RFC the deprecation warning points to. The workflow does not
  edit it — it only names the path in the warning text.

## Source files touched

| Surface | Paths |
|---|---|
| CLI help text | `kayakgen/cli/runs_cli.py` |
| Deprecation warning text | `kayakgen/ui/gui_params.py` |
| Test match string update | `tests/test_gui_params.py` |

## Files NOT touched by this workflow

The parent agent or sibling workflows own these surfaces:

- `CHANGELOG.md` — parent agent
- `docs/audits/2026-05-23-code-doc-audit/*/FINDINGS.md` — parent agent
  flips the AUD-O-011 / AUD-O-012 statuses
- `docs/audits/2026-05-23-code-doc-audit/REMEDIATION_PLAN.md`,
  `SYNTHESIS.md` — read-only context
- `docs/rfcs/` — RFC source is read-only here; the workflow only
  references the existing path
- `docs/DECISION_LOG.md` — parent agent
- `kayakgen/ui/web/` — workflow 0035 owns the web side (R4)
- `kayakgen/ui/desktop.py` — workflow 0035 owns the desktop slider
  test surface (R4)

## Where the artifacts land

`docs/audits/2026-05-23-code-doc-audit/follow-ups/0036/`:

```
PATCH_SUMMARY.md   # written by `implement`
REVIEW.md          # written by `review`
```
