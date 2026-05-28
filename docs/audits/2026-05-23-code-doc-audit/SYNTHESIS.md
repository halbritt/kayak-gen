# Audit Synthesis — 2026-05-23 code+doc audit (release_candidate)

Date: 2026-05-23
Workflow shape: `code_doc_audit` (RFC 0059)
Preset: `release_candidate`
Source-of-truth scope: 10 commits `f78e478..HEAD` on `main` (RFC 0059 / 0060 / 0061 + workflows 0029-0034)

## Lane-diversity caveat

Single-agent run (Claude Opus 4.7 main thread dispatched three parallel
`Explore` subagents). The provider-diversity that `0009-multi-lane-review`
achieved (claude / codex / gemini) was not achieved here. Each lane kept
a distinct reading posture and reported independently. The synthesis
trusts the lane outputs but flags this provenance.

## Findings rolled up

| ID | Lane | Severity | Category | Status |
|---|---|---|---|---|
| (none) | pipeline-integrity | — | claim_gate | null finding — code is internally consistent |
| AUD-D-001 | docs-decision-drift | low | docs_drift | closed (verified pass) |
| AUD-D-002 | docs-decision-drift | low | rfc_status | closed (verified pass) |
| AUD-D-003 | docs-decision-drift | low | docs_drift | closed (verified pass) |
| AUD-D-004 | docs-decision-drift | low | docs_drift | closed (verified pass) |
| AUD-D-005 | docs-decision-drift | low | docs_drift | closed (verified pass) |
| AUD-D-006 | docs-decision-drift | low | docs_drift | closed (verified pass) |
| AUD-D-007 | docs-decision-drift | low | docs_drift | closed (verified pass) |
| AUD-D-008+ | docs-decision-drift | low | docs_drift | closed (verified pass) |
| AUD-O-009 | operator-adoption | medium | test_gap | closed by 0035 — `tests/test_generate_panel_label_rendering.py` lands the VTextField hint render-verification (commit `2d14cff`) |
| AUD-O-010 | operator-adoption | medium | test_gap | closed by 0035 — `tests/test_desktop_slider_labels.py` lands the matplotlib Slider label render-verification (commit `2d14cff`) |
| AUD-O-011 | operator-adoption | low | operator_ergonomics | closed by 0036 — `runs list --kind` help text now enumerates `sweep | search | cfd | comparison` (commit `2d14cff`) |
| AUD-O-012 | operator-adoption | low | operator_ergonomics | closed by 0036 — `gui_params.py` deprecation warning gained the RFC 0061 path pointer (commit `2d14cff`) |
| AUD-O-013 | operator-adoption | info | — | open — positive null finding on the rework brief (recorded as baseline; no action) |
| AUD-O-014 | operator-adoption | low | operator_ergonomics | closed by R1 — `docs/audits/README.md` was created in audit commit `fcb8040` |
| AUD-O-015 | operator-adoption | low | operator_ergonomics | closed by R1 — `docs/workflows/0029-code-doc-audit/SOURCES.md` is now the canonical template with prose pointing at past runs as worked examples (commit `fcb8040`) |

**Severity totals**: 0 critical, 0 high, 2 medium, 5 low, 1 info, 1 partial-closed.
Lane 2 returned positive null findings (8 entries, all `closed (verified pass)`)
— the discipline-checklist applied to the RFC 0059/0060/0061 landings is clean.

## Cross-lane duplicates and overlap

No cross-lane duplicates. The three lanes investigated disjoint surfaces
(Lane 1: Pydantic invariants; Lane 2: docs/code consistency; Lane 3: did
operators actually see the changes) and produced disjoint findings.

## Conflicts between lanes

None. Lane 2's positive findings on RFC 0060/0061 documentation align with
Lane 3's positive findings on the underlying registry wiring; Lane 3's
"code is wired but untested for render" finding (AUD-O-009 / AUD-O-010) is
adjacent to, not in conflict with, Lane 1's "Pydantic round-trip is sound"
positive finding.

## Priority order

Highest-leverage first:

1. **R1 — Audit index README** (AUD-O-014). One docs-only file. Future
   audit operators land here and see "which audit is canonical?" answered
   in one read.
2. **R2 — Workflow 0029 SOURCES.md fill-in** (AUD-O-015). The 2026-05-22
   dogfood run already happened; back-populate SOURCES.md with the real
   inputs so the file documents the canonical first run rather than
   reading as an unfilled template.
3. **R3 — Deprecation warning URL** (AUD-O-012). One line in
   `kayakgen/ui/gui_params.py`. Tiny code change but goes through striatum
   per `feedback_striatum_required` — defer to a follow-up workflow OR
   bundle with R4.
4. **R4 — Render tests for RFC 0060 / 0061 surfaces** (AUD-O-009 +
   AUD-O-010). Two new render-verification tests. Code+test work; needs
   its own striatum workflow.
5. **R5 — `runs list` help-text symmetry** (AUD-O-011). Already partially
   closed by workflow 0032; tiny help-text addition. Bundle with R3 or R4.

Info / null findings (AUD-O-013 + AUD-D-001..008 + Lane 1 null) need no
action; they record the positive state for the next audit's baseline.

## Notes for the workflow scaffold

The release_candidate preset worked as intended on this scope. The three
lanes converged in well under an hour and produced disjoint, evidence-backed
findings. The single-agent caveat is the only methodological gap; future
release-candidate runs should still attempt cross-provider lane assignment
where the providers are available.
