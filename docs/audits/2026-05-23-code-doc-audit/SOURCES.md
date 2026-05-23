# Sources for audit run — 2026-05-23

## Preset

`release_candidate` — the recently-landed RFC 0059 / 0060 / 0061 set is the
next coherent shippable batch. This audit is a release-candidate sanity pass
on that work before any external consumer relies on it.

## Run scope

The 10 commits `f78e478..HEAD` on `main`:

```
3a7f2de Move CLAUDE_DESIGN_UI_REWORK_PROMPT.md into prompts/ + add second-pass brief
8659fb0 Add RFC 0061 + land workflow 0034 — desktop sliders on registry
c052ddd Untrack .claude/skills/* — already gitignored, were tracked legacy
f2b366f Fix workflow.json schema compliance — cycles field + lane diversity
8769124 Promote RFC 0059 + add D041-D043 + ROADMAP entries
b4a494e Add RFC 0060 + land workflow 0033 — close audit AUD-O-003 (panel labels)
5c658ea Land workflow 0032 — close audit AUD-O-004/005/006 (CLI ergonomics)
2a260bd Land workflow 0031 — close audit AUD-P-003 + AUD-P-004 (vocab coverage)
bf4179f Land workflow 0030 — close audit AUD-P-001 + AUD-P-002 (R3 + R7)
130a42e Add RFC 0059 + workflow 0029 + run dogfood audit + R1 docs remediation
```

This is the second `code_doc_audit` run; the first
(`docs/audits/2026-05-22-code-doc-audit/`) was a `full_repo` dogfood that
produced 13 findings, all closed. This `release_candidate` run is narrower:
it audits whether the 2026-05-22 audit's outputs and follow-up workflows
themselves are internally consistent and ready to ship.

## Lane inputs

| Lane | Inputs |
|---|---|
| pipeline-integrity | New code: `kayakgen/ui/parameter_metadata.py`, `kayakgen/ui/desktop_slider_ranges.py`. Modified Pydantic schemas: `kayakgen/eval/contract.py` (GZCurve.result_semantics Literal widening), `kayakgen/eval/stability/accepted_fit.py` (EMPTY_STABILITY_FIT_REGISTRY constant). Three call sites that now consume the constant. The new round-trip + registry tests under `tests/`. The deprecation-shim path in `kayakgen/ui/gui_params.py`. |
| docs-decision-drift | RELEASE_DISCIPLINE.md checklist applied to the 10 commits: SPEC, PRD, ROADMAP, DECISION_LOG (D041/D042/D043), CHANGELOG, ARCHITECTURE_MAP, UBIQUITOUS_LANGUAGE, USER_GUIDE, rfcs/README. The three new RFCs (0059, 0060, 0061) — index status must match the body's Status field. The six workflow scaffolds (0029-0034) — workflow.json must validate and the prompts/roles must be coherent. |
| operator-adoption | Did the labels actually improve the surfaces they were supposed to? Run `kayakgen serve` in the head — does the Generate panel actually render the new tooltips? Cross-check the prompts/web_ui_second_pass_rework_2026-05-22.md against the live state. Check operator-facing CHANGELOG / USER_GUIDE additions for clarity. The `kayakgen runs jobs --header` flag and the `cfd prepare` next-step message. |

## RFCs in scope

- RFC 0059 (three-lane audit workflow shape; `landed`)
- RFC 0060 (web Generate-panel form labels and tooltips; `landed`)
- RFC 0061 (desktop sliders on HullParameterMetadata; `landed`)

## Decision rows in scope

- D041 (audit cadence)
- D042 (EMPTY_STABILITY_FIT_REGISTRY constant)
- D043 (HullParameterMetadata presentation-layer pattern)

## Adversary framing per lane

- pipeline-integrity → look for *claim-state drift* in the new Pydantic
  widening + the deprecation shim + the registry consumers.
- docs-decision-drift → look for *honest-prose drift* in the new
  CHANGELOG / RFCs / DECISION_LOG / ROADMAP entries against what
  actually landed in code.
- operator-adoption → look for *invisible-mechanism drift*: did the
  RFC 0060/0061 labels actually surface, or just sit in the registry?

## Where the audit run artifacts will land

`docs/audits/2026-05-23-code-doc-audit/`:

```
pipeline-integrity/FINDINGS.md
docs-decision-drift/FINDINGS.md
operator-adoption/FINDINGS.md
SYNTHESIS.md
REMEDIATION_PLAN.md
```
