# Lane 2: Docs / Decision-Drift Audit Findings

## Audit Coverage Summary

Full-repository docs/decision-drift audit covering the RELEASE_DISCIPLINE.md public-behavior-change checklist applied across HEAD state `313dfdd` (clean). Scope: SPEC.md / PRD.md / DECISION_LOG.md (44 rows) / ROADMAP.md / RFC index (62 RFCs) / CHANGELOG.md / ARCHITECTURE_MAP.md / UBIQUITOUS_LANGUAGE.md / USER_GUIDE.md / WEB_VERIFICATION.md / RFCs 0059-0062 (youngest landings) / D041-D044 (four most recent decisions).

---

### AUD-D-001: ROADMAP.md update date is stale

severity: low
category: docs_drift
status: open
claim: ROADMAP.md's header "Updated: 2026-05-21" is three days out of date; the ARCHITECTURE_MAP.md correctly bumped to "2026-05-25" in the release_candidate audit R1.
evidence:
- docs/ROADMAP.md:3 — "Updated: 2026-05-21"
- docs/ARCHITECTURE_MAP.md:1 — "Date: 2026-05-25" (correctly current)

impact: RELEASE_DISCIPLINE.md §checklist row "docs/ROADMAP.md — track row and Future-Striatum-Batches disposition" requires consistency across central docs. The stale date may signal that ROADMAP content was not re-reviewed during R1, even though the RFC index was refreshed.

recommended_action: Bump ROADMAP.md header to 2026-05-25 if the content remains accurate post-workflow-0037/0038 or explicitly audit the content against the RFC index and add any landing entries (RFC 0062, workflows 0037-0038) that may have shifted Future-Striatum-Batches disposition since 2026-05-21.

follow_up: docs fix

---

### AUD-D-002: RFC 0060 and RFC 0061 files do not exist at documented paths

severity: high
category: docs_drift
status: open
claim: The RFC index at docs/rfcs/README.md lists RFC 0060 and RFC 0061 as landed status with documented paths, but the RFC body files do not exist at those paths on disk.
evidence:
- docs/rfcs/README.md:77 — "| [0060](0060-web-generate-panel-form-labels-and-tooltips.md) | landed | Web Generate-panel form labels and tooltips..."
- docs/rfcs/README.md:78 — "| [0061](0061-desktop-sliders-on-hull-parameter-metadata.md) | landed | Desktop sliders on `HullParameterMetadata`..."
- `ls /home/halbritt/git/kayak-gen/docs/rfcs/0060* /home/halbritt/git/kayak-gen/docs/rfcs/0061*` — files do not exist
- docs/CHANGELOG.md references both RFCs as landed (Workflow 0033, Workflow 0034)

impact: RELEASE_DISCIPLINE.md checklist row 4 "docs/rfcs/README.md — RFC status header" requires the RFC body to exist when cited. The index is incomplete, making the full RFC record inaccessible to contributors or agents reading the canonical sources.

recommended_action: Either (a) create the RFC body files at the documented paths with status headers matching the index, or (b) file a follow-up RFC explaining why these RFCs exist in the index but not as separate bodies (e.g., they landed as a pair under a single body, or content is embedded in DECISION_LOG.md rows instead). The source behavior (D043 / D044 / the metadata registries) is correctly implemented, so this is a docs-only structural fix.

follow_up: new RFC | docs fix

---

### AUD-D-003: RFC 0059 §2.2 coverage list and actual audit findings mismatch on D043 / D044 scope

severity: info
category: docs_drift
status: open
claim: The RFC 0059 brief at §2.2 claims "D043 (HullParameterMetadata pattern) — confirm RFC 0060/0061 consumers still source from the registry." The D043 decision row itself names only RFC 0060 as the pattern exemplar, with RFC 0061 as a follow-up and RFC 0062 as a later parallel application. The scope statement overgeneralizes D043 when D044 is the more direct precondition for RFC 0062.
evidence:
- docs/rfcs/0059-three-lane-code-and-doc-audit-workflow.md:88 — brief claims D043 coverage
- docs/DECISION_LOG.md:61 row D043 — "Adopt the RFC 0060 `HullParameterMetadata` presentation-layer registry as the pattern... RFC 0061 (workflow 0034) closed the named desktop-migration follow-up"
- docs/DECISION_LOG.md:62 row D044 — "Apply the D043 'presentation-layer registry per surface family' pattern to the Hydro tab... RFC 0062 lands as `landed`"

impact: This is a clarification issue, not a correctness issue. The RFC 0059 brief is readable as-is, but a stricter reading would note that D043 is specifically the RFC 0060 landing decision, not a blanket pattern decision, and D044 is the explicit second application.

recommended_action: Inline clarification in RFC 0059 §2.2 to name D044 explicitly alongside D043, or note that D043 set the pattern and D044 confirmed its reusability. This is a wontfix if RFC 0059 is deemed a historical record that need not be updated post-landing.

follow_up: wontfix

---

### AUD-D-004: WEB_VERIFICATION.md data-testid section lacks explicit test mapping

severity: low
category: docs_drift
status: open
claim: WEB_VERIFICATION.md §"data-testid Hook Contract" documents the existence of hooks (`validity-badge`, `generative-submit`, `comparison-source-toggle`, `mesh-no-package-chip`, `mesh-live-readiness-chip`, `generative-variable-table`, `generative-objective-refusal`, `generative-jobs-table`) but does not cite the test file that verifies these hooks are present.
evidence:
- docs/WEB_VERIFICATION.md:93-99 — lists hooks with a disclaimer that they are internal test contracts
- CHANGELOG.md notes workflow 0037 "gained a `data-testid` hook contract section" closing AUD-O-015
- Tests exist at tests/test_web_layout.py (per CHANGELOG.md reference)

impact: RELEASE_DISCIPLINE.md §checklist row 8 "docs/WEB_VERIFICATION.md — claims (gained a `data-testid` hook contract section)" requires the claims to be verifiable. A reader encountering this section for the first time would benefit from a forward reference to the test file that enforces the hook contract, making the claim auditable.

recommended_action: Add a sentence in the WEB_VERIFICATION.md data-testid section citing `tests/test_web_layout.py` as the enforcement point, e.g., "Tests in `tests/test_web_layout.py` pin the presence and placement of these hooks."

follow_up: docs fix

---

### AUD-D-005: USER_GUIDE.md serve section accurately describes post-b82b544 state

severity: info
category: docs_drift
status: open
claim: USER_GUIDE.md §"serve" section was rewritten in R1 of the 2026-05-25 release_candidate audit (per CHANGELOG.md). Spot-check against HEAD source confirms the prose accurately matches the post-rework layout (Param rail / Hydro / Mesh / Comparison / Generate tabs, comparison-source toggle, mesh-diagnostic tooltips, submit-button disabled-reason wiring).
evidence:
- docs/USER_GUIDE.md:200+ — describes the workspace layout with tabs, toggle, and disabled-reason behavior
- CHANGELOG.md "Changed" section documents the same surfaces
- Source code (kayakgen/ui/web/app.py, generate_spec_form.py) contains the described wiring

impact: No drift detected. The USER_GUIDE accurately describes current behavior post-workflow-0037 inline-help additions.

recommended_action: None. Record as a positive baseline.

follow_up: none

---

### AUD-D-006: RFC status headers correctly cite successors; no predecessor obsoletion drift

severity: info
category: docs_drift
status: open
claim: RFC index entries for RFC 0017, 0019, 0020 (background RFCs with successors) correctly cite their successors (0041, 0042, 0024/0043), and spot-checks confirm the successor RFCs exist and cite the predecessors in their Context sections.
evidence:
- docs/rfcs/README.md:33 — RFC 0017 "proposed background; successor 0041"
- docs/rfcs/README.md:35 — RFC 0019 "proposed background; successor 0042"
- docs/rfcs/README.md:36 — RFC 0020 "proposed background; successors 0024/0043"
- docs/rfcs/0041-real-cfd-adapter-successor.md — exists and is marked "landed"
- docs/rfcs/0042-resistance-calibration-fixture-successor.md — exists and is marked "partial landed"
- docs/rfcs/0043-high-angle-gz-successor.md — exists and is marked "landed"

impact: No drift detected. The RFC index successor citations are complete and bidirectional.

recommended_action: None. Record as a positive baseline.

follow_up: none

---

### AUD-D-007: D042 (EMPTY_STABILITY_FIT_REGISTRY constant) consumption verified at all three call sites

severity: info
category: docs_drift
status: open
claim: D042 requires three RFC 0058 stage-2/3 call sites to consume EMPTY_STABILITY_FIT_REGISTRY constant rather than bare `()` literal. Audit confirms all three sites import and use the constant.
evidence:
- kayakgen/eval/stability/accepted_fit.py:23 — constant defined
- kayakgen/eval/stability/evaluator.py:25 and line 387 — imports and uses constant
- kayakgen/ui/web/generate_frontier_view.py:31 and line 568 — imports and uses constant
- kayakgen/ui/web/generate_spec_form.py:34 and line 897 — imports and uses constant

impact: No drift detected. D042's three-site synchronization contract is satisfied.

recommended_action: None. Record as a positive baseline.

follow_up: none

---

### AUD-D-008: D043 (HullParameterMetadata registry) consumption verified across desktop and web surfaces

severity: info
category: docs_drift
status: open
claim: D043 requires RFC 0060 HullParameterMetadata registry consumption in the web Generate panel and RFC 0061 desktop GUI. Audit confirms both surfaces import HULL_PARAMETER_METADATA from kayakgen/ui/parameter_metadata.py.
evidence:
- kayakgen/ui/parameter_metadata.py — registry defined
- kayakgen/ui/desktop.py:47-48 — imports and re-exports HULL_PARAMETER_METADATA
- kayakgen/ui/web/generate_spec_form.py:48-49 — imports HULL_PARAMETER_METADATA
- tests/test_hull_parameter_metadata.py — regression tests verify registry structure

impact: No drift detected. D043's dual-surface consumption contract is satisfied.

recommended_action: None. Record as a positive baseline.

follow_up: none

---

### AUD-D-009: D044 (HydrostaticsRowMetadata registry) consumption verified in evaluation.py

severity: info
category: docs_drift
status: open
claim: D044 requires RFC 0062 HydrostaticsRowMetadata registry consumption in kayakgen/services/evaluation.py::analysis_view_model::hydro_rows. Audit confirms the import and wiring.
evidence:
- kayakgen/ui/hydrostatics_metadata.py — registry defined (workflow 0038)
- kayakgen/services/evaluation.py:33 — imports HYDROSTATICS_ROW_METADATA as _HYDRO_META
- tests/test_hydrostatics_row_metadata.py — regression tests verify registry structure and wiring

impact: No drift detected. D044's evaluation.py wiring is correct.

recommended_action: None. Record as a positive baseline.

follow_up: none

---

### AUD-D-010: CHANGELOG.md entries for workflows 0037 + 0038 are detailed and complete

severity: info
category: docs_drift
status: open
claim: CHANGELOG.md "Added" / "Changed" sections document workflows 0037 and 0038 with sufficient specificity: helper functions, state fields, test additions, and presentation-only claims are all recorded.
evidence:
- CHANGELOG.md lines 9-74 — detailed workflow 0037 and 0038 entries
- Entries cite specific modules (kayakgen/ui/web/app.py, generate_spec_form.py, evaluation.py)
- Entries cite test modules (tests/test_web_inline_help.py, tests/test_hydrostatics_row_metadata.py)
- Presentation-only claim ("Presentation-only; `build_spec_from_form_state` wire output unchanged") is explicitly stated

impact: No drift detected. CHANGELOG accurately mirrors the landings.

recommended_action: None. Record as a positive baseline.

follow_up: none

---

End of Lane 2 findings. Positive baselines: D042, D043, D044, RFC successor citations, USER_GUIDE serve section, WEB_VERIFICATION description accuracy, CHANGELOG entries. Minor drift: ROADMAP date (low), RFC 0060/0061 missing files (high), D043 scope clarification in RFC 0059 (info/wontfix).
