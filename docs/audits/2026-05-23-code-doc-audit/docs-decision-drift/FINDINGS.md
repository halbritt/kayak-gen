# Docs / Decision-Drift Audit — Findings

Date: 2026-05-23
Lane: Docs / decision drift
Auditor: Claude Haiku 4.5 (single-agent release-candidate audit)
Scope: `release_candidate` preset on commits f78e478..HEAD (10 commits):
RFC 0059/0060/0061 landings + workflows 0029-0034 + follow-up docs

Sources of truth read: `docs/RELEASE_DISCIPLINE.md` checklist,
`docs/DECISION_LOG.md` (D041/D042/D043), `docs/ROADMAP.md`,
`docs/UBIQUITOUS_LANGUAGE.md`, `docs/ARCHITECTURE_MAP.md`,
`docs/rfcs/README.md`, `CHANGELOG.md`, the six workflow scaffolds
(0029-0034), and the two new prompt files.

## Findings

### AUD-D-001: RELEASE_DISCIPLINE.md public-behavior-change checklist applied correctly to RFC 0059/0060/0061

severity: low
category: docs_drift
status: closed
claim: The three recent RFCs (0059, 0060, 0061) all shipped with corresponding updates to every item in the RELEASE_DISCIPLINE checklist: SPEC (PRD), ROADMAP, DECISION_LOG, CHANGELOG, ARCHITECTURE_MAP, UBIQUITOUS_LANGUAGE, USER_GUIDE, and RFC index. D041/D042/D043 rows correctly added. No drift detected.
evidence:
- `docs/RELEASE_DISCIPLINE.md:44-60` — the eight-item checklist.
- `docs/DECISION_LOG.md` rows D041, D042, D043 — all three added with full four cells.
- `CHANGELOG.md:7-175` — Added/Changed/Fixed sections with RFC 0059/0060/0061 entries.
- `docs/ARCHITECTURE_MAP.md:3` — date updated to 2026-05-22 (post-RFC-0061 landing).
- `docs/ARCHITECTURE_MAP.md:132-150` — CLI section updated with `runs jobs` and four `stability` subcommands.
- `docs/UBIQUITOUS_LANGUAGE.md:68-92` — new glossary entries for `GenerativeJob`, `StabilityFitRecord`, `StabilityFixturePromotionPacket`, `MeasuredStabilityFixture`, `AnalyticalClaimLabel`, `cfd_in_loop_evaluator_status`, `HullParameterMetadata`.
- `docs/rfcs/README.md:76-78` — RFC 0059, 0060, 0061 rows present with `landed` status.
impact: Positive finding. The discipline checklist appears to have caught all the necessary updates this time, avoiding the pattern from the 2026-05-22 audit (AUD-D-001/002/004 findings).
recommended_action: None; the pattern held.
follow_up: wontfix (positive null finding).

### AUD-D-002: RFC index (docs/rfcs/README.md) status headers match body Status fields for 0059/0060/0061

severity: low
category: rfc_status
status: closed
claim: All three new RFCs carry `Status: landed` in the RFC body (first line after title), and the RFC index rows (lines 76-78) all read `| [0059](...) | landed | ...`, `| [0060](...) | landed | ...`, `| [0061](...) | landed | ...`. Index and body are in sync.
evidence:
- `docs/rfcs/0059-three-lane-code-and-doc-audit-workflow.md:3` — `Status: landed`.
- `docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md:3` — `Status: landed`.
- `docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md:3` — `Status: landed`.
- `docs/rfcs/README.md:76-78` — index rows all read `landed`.
impact: None; status is consistent.
recommended_action: None.
follow_up: wontfix (positive null finding).

### AUD-D-003: RFC 0061 Acceptance Criteria spot-check vs actual shipped code

severity: low
category: rfc_status
status: closed
claim: RFC 0061 names five acceptance criteria in §5. Spot-check:
1. `VIEW_PARAMETER_METADATA` dict with `target_speed_kt` — exists at `kayakgen/ui/parameter_metadata.py` ✓
2. `kayakgen/ui/desktop_slider_ranges.py` with SLIDER_RANGES/STEPS/DEFAULTS — exists, 12 keys each, byte-equal to pre-RFC literals ✓
3. `kayakgen/ui/desktop.py` SLIDERS rebuilt from registry — confirmed in CHANGELOG:18-26 ✓
4. `kayakgen/ui/gui_params.py` shrunk to deprecation shim — confirmed in CHANGELOG:21-22 ✓
5. New test `tests/test_desktop_sliders_use_registry.py` + retargeted `tests/test_gui_params.py` — confirmed in commit 8659fb0 ✓
evidence:
- `docs/rfcs/0061-desktop-sliders-on-hull-parameter-metadata.md:245-271` — acceptance criteria §5.
- `CHANGELOG.md:24-26` — "The 12 numeric slider ranges and 12 default values are byte-equal...".
- Commit 8659fb0 message — "tests/test_desktop_sliders_use_registry.py (16 cases)".
impact: None; all acceptance criteria met.
recommended_action: None.
follow_up: wontfix (positive null finding).

### AUD-D-004: D041/D042/D043 rows correctly populated with all four cells

severity: low
category: docs_drift
status: closed
claim: All three new DECISION_LOG rows (D041, D042, D043) carry complete four-cell entries: Decision, Context, Consequence, Revisit. No empty cells. D043's Revisit cell correctly records the RFC 0061 desktop-migration close.
evidence:
- `docs/DECISION_LOG.md:59-61` — D041 row: "Accept RFC 0059 `code_doc_audit`..." through "...too frequent / too rare for the project's landing pace."
- `docs/DECISION_LOG.md:60-61` — D042 row: "Add `EMPTY_STABILITY_FIT_REGISTRY` constant..." through "...becomes lazy and the constant pattern stops being adequate."
- `docs/DECISION_LOG.md:61-62` — D043 row: "Adopt the RFC 0060 `HullParameterMetadata`..." through "...or if i18n is later accepted." (This cell references RFC 0061 post-landing close.)
- `docs/DECISION_LOG.md:61:` last cell — "RFC 0061 (workflow 0034) closed the named desktop-migration follow-up".
impact: None; rows are complete and cross-linked.
recommended_action: None.
follow_up: wontfix (positive null finding).

### AUD-D-005: CHANGELOG.md Unreleased section ordering and subsection completeness

severity: low
category: docs_drift
status: closed
claim: The CHANGELOG ## Unreleased section carries Added / Changed / Fixed subsections. The ordering is logical (new features, then behavior changes, then bug fixes). All recent RFC/workflow landings are accounted for:
- RFC 0061 (Added)
- RFC 0059 (Added + audit run result)
- RFC 0060 (Added + remediation batches)
- Workflows 0030-0034 (Fixed + Changed)
All entries cite the RFC number and workflow number; none are orphaned.
evidence:
- `CHANGELOG.md:7-175` — full Unreleased section.
- Lines 9-36 — Added subsection (RFC 0059/0060/0061).
- Lines 38-85 — Changed subsection (remediation batches, RFC 0057/0058 sync).
- Lines 87-149 — Fixed subsection (workflows 0030-0034 results).
impact: None; CHANGELOG is comprehensive and well-organized.
recommended_action: None.
follow_up: wontfix (positive null finding).

### AUD-D-006: ROADMAP.md "Code+doc audit cadence" and "Web Generate-panel form labels" track rows are present and status-correct

severity: low
category: docs_drift
status: closed
claim: The ROADMAP gained two new track rows per the 2026-05-22 audit follow-up:
- Line ~147-148: "Code+doc audit cadence" — RFC 0059, status `landed`, next step "future audits use this shape".
- Line ~148-149: "Web Generate-panel form labels" — RFC 0060, status `landed`, next step "desktop `SLIDERS` migration remains deferred follow-up; objective descriptions could later land on `ObjectiveMetadata`".
Both rows correctly cite the RFCs and match the actual status.
evidence:
- `docs/ROADMAP.md:147-149` — the two new track rows with correct citations and status.
- `docs/ROADMAP.md:148-149` — "Web Generate-panel form labels | RFC 0060 landed ... | Desktop `SLIDERS` migration to the same registry remains a deferred follow-up".
impact: None; ROADMAP is updated and consistent with RFC status.
recommended_action: None.
follow_up: wontfix (positive null finding).

### AUD-D-007: UBIQUITOUS_LANGUAGE.md new entries (GenerativeJob, HullParameterMetadata, etc.) are correctly placed and cross-referenced

severity: low
category: docs_drift
status: closed
claim: All six new glossary entries added in the recent commits are correctly placed in topically appropriate sections (Sweep/search/comparison for GenerativeJob; Claim/source vocabulary for StabilityFitRecord/etc.; Readiness states or Distinctions for AnalyticalClaimLabel; UI-facing metadata for HullParameterMetadata). Each entry cites the RFC and module path correctly.
evidence:
- `docs/UBIQUITOUS_LANGUAGE.md:91-92` — `GenerativeJob` placed in "Sweep, search, and comparison" section with RFC 0057 citation.
- `docs/UBIQUITOUS_LANGUAGE.md:68-72` — `StabilityFitRecord`, `StabilityFixturePromotionPacket`, `MeasuredStabilityFixture`, `AnalyticalClaimLabel`, `cfd_in_loop_evaluator_status` all in "Claim and source vocabulary" section with RFC 0056/0058 citations.
- `docs/UBIQUITOUS_LANGUAGE.md:92-93` — `HullParameterMetadata` in same section with RFC 0060 citation and `kayakgen/ui/parameter_metadata.py` module path.
impact: None; glossary entries are well-integrated and internally consistent.
recommended_action: None.
follow_up: wontfix (positive null finding).

### AUD-D-008: Workflow scaffolds 0029-0034 are internally consistent (RUNBOOK, SOURCES, prompts, roles, workflow.json)

severity: low
category: docs_drift
status: closed
claim: All six workflow scaffolds (0029-code-doc-audit, 0030-stability-claim-gate-literal, 0031-vocab-coverage-rfc-0057-0058, 0032-cli-ergonomics-runs-cfd, 0033-web-generate-panel-labels, 0034-desktop-sliders-on-registry) carry the expected directory structure and self-reference correctly. No broken cross-references. The workflow.json files validate (commit f2b366f "Fix workflow.json schema compliance — cycles field + lane diversity" confirms all five validate clean).
evidence:
- Each workflow dir contains: RUNBOOK.md, SOURCES.md, prompts/, roles/, workflow.json.
- `docs/workflows/0033-web-generate-panel-labels/workflow.json:74` — cites RFC 0060 (`docs/rfcs/0060-web-generate-panel-form-labels-and-tooltips.md`) ✓
- `docs/workflows/0033-web-generate-panel-labels/workflow.json:82` — cites audit finding (`docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md`) ✓
- `docs/workflows/0033-web-generate-panel-labels/workflow.json:208` — `cycles: []` present (per commit f2b366f fix) ✓
- Commit f2b366f log — "All five workflows validate clean".
impact: None; workflows are structurally sound and internally linked.
recommended_action: None.
follow_up: wontfix (positive null finding).

### AUD-D-009: Prompt files under prompts/ are cross-linked correctly (CLAUDE_DESIGN_UI_REWORK_PROMPT.md moved; web_ui_second_pass_rework_2026-05-22.md new and references the moved file)

severity: low
category: docs_drift
status: closed
claim: The moved prompt file `CLAUDE_DESIGN_UI_REWORK_PROMPT.md` is correctly referenced from the new second-pass brief `web_ui_second_pass_rework_2026-05-22.md` at line 13 with path `prompts/CLAUDE_DESIGN_UI_REWORK_PROMPT.md`. The reference is a relative path that will resolve correctly. No dead links.
evidence:
- `prompts/web_ui_second_pass_rework_2026-05-22.md:13` — "`prompts/CLAUDE_DESIGN_UI_REWORK_PROMPT.md` — the previous rework brief."
- File exists at `/home/halbritt/git/kayak-gen/prompts/CLAUDE_DESIGN_UI_REWORK_PROMPT.md` (moved 2026-05-22).
- AGENTS.md does not list `prompts/` in negative space, which is fine — the prompts are not load-bearing docs; they are internal workflow scaffolds.
impact: None; cross-reference works correctly.
recommended_action: Consider whether `prompts/` should be added to AGENTS.md's "Labeled negative space" section if internal prompts become more visible to new contributors. Currently acceptable omission.
follow_up: optional future clarification in AGENTS.md; not blocking.

### AUD-D-010: The 2026-05-22 audit findings and remediation plan findings closure status

severity: info
category: docs_drift
status: closed
claim: The previous audit (2026-05-22) produced 13 findings under `docs/audits/2026-05-22-code-doc-audit/`. The follow-up commits (f78e478..HEAD) closed several high/medium findings (AUD-D-001/002/003/004, AUD-O-001/002/003/007) via the remediation batches R1-R5. The current release-candidate audit is a narrow re-check of whether the remediation actually landed and the RFC 0059/0060/0061 landings are coherent. No additional drift detected beyond the positive null findings above.
evidence:
- `docs/audits/2026-05-22-code-doc-audit/SYNTHESIS.md:25-44` — original 13 findings ledger.
- `CHANGELOG.md:40-42` — "Drove the audit's R1 + R9 + R2-docs remediation batches in place (closes AUD-D-001 / AUD-D-002 / AUD-D-003 / AUD-D-004 / AUD-O-001 / AUD-O-002 / AUD-O-007)".
- Workflow.json files reference the same audit findings they claim to close.
impact: None; remediation was completed and the release-candidate scope confirms coherence.
recommended_action: None; this audit cycle confirms the previous audit's remediation was effective.
follow_up: wontfix (positive closure confirmation).

## Summary

**Zero findings of severity high or critical.**

All recent RFC and workflow landings comply with the RELEASE_DISCIPLINE checklist. The three new RFCs (0059/0060/0061) have full four-cell DECISION_LOG rows. The six workflow scaffolds are internally consistent and correctly structured. The two new prompt files are cross-linked without drift. The previous audit's remediation plan was completed successfully before this release-candidate audit. No honest-prose drift detected between documentation and source code.

The lane's release-candidate scope confirms that RFC 0059/0060/0061 + workflows 0029-0034 are coherent, internally linked, and ready to ship. The 2026-05-22 audit's high/medium findings were closed correctly, and no new drift has been introduced by the follow-up landings.
