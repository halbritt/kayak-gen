Verdict intent: accept_with_findings

## Reviewed scope

- RFC 0033 (`docs/rfcs/0033-workspace-ui-rework.md`) against `docs/rfcs/README.md`,
  `docs/PRD.md`, `docs/design/kayak_hull_design_constraints.md`, and the companion
  RFCs 0008, 0010, 0013, 0018, 0025, and 0031.
- Workflow scaffold under `docs/workflows/0044-workspace-ui-rework/` (workflow.json,
  SOURCES.md, RUNBOOK.md, and the eight prompt/role pairs) against the workflow-local
  remediation artifact `striatum/0044-workspace-ui-rework/review_remediation/REMEDIATION.md`.
- Current surfaces named by RFC 0033 under `kayakgen/ui/`, `kayakgen/model/`, and
  `kayakgen/eval/` to confirm the RFC's "today" claims and proposed deltas are
  grounded in real code paths.
- RFC 0033 acceptance criteria checklist against the workflow's review and final-review
  prompts to confirm each acceptance assertion is owned by at least one downstream job.

## Sub-agent / parallel assistance used

Four read-only Explore sub-agents ran in parallel with disjoint scopes:

- **web-surface**: validated RFC 0033 "today" claims about `kayakgen/ui/web/app.py`,
  `controllers.py`, `state.py`, named REST routes, and absent helpers.
- **desktop-surface**: validated `kayakgen/ui/desktop.py`, `gui_params.py`, and
  `pv_window.py` against RFC 0033's desktop claims (plot colour literals, separate
  PyVista window, missing `Cm` slider, "Generate STLs" label, `_classify`,
  `GridSpec` layout, absence of `theme.py`/`PLOT_PALETTE`).
- **model/eval-surface**: confirmed the existence and field shapes of
  `DesignAdvisory`, `Hull`, `KayakClass`, `ClaimState`, `MeshDiagnostics`,
  `MeshPackageManifest`, `CfdRunStatus`, `validation_error_payload`,
  `DesignValidityFinding`, and `ResistanceMetadata.warnings`.
- **RFC-cross-ref**: read RFCs 0008, 0010, 0013, 0018, 0025, 0031 and checked the
  specific terms RFC 0033 cites by name (readiness levels, profile IDs, claim
  literals, deferrals, unsupported-field channel).

Findings below cite file:line evidence gathered jointly across these reviews.

## Findings

### No blocking findings

RFC 0033 maps cleanly to the existing RFCs and to today's controllers, payloads,
and CLI surfaces. The five named deferrals — hosted CFD, calibrated drag,
high-angle GZ visualisation, multi-variant 2D geometry overlay, and web-side
mesh-package authoring API — are unambiguous in `docs/rfcs/0033-workspace-ui-rework.md:73-83`
and are echoed without contradiction in `docs/workflows/0044-workspace-ui-rework/SOURCES.md`,
`prompts/findings_ledger.md`, and `prompts/implement_findings.md`. Every RFC 0033
acceptance criterion (`docs/rfcs/0033-workspace-ui-rework.md:295-330`) is named by
at least one of the four review prompts and revisited by `prompts/final_review.md`.
The remediation artifact's claim that no first-pass review artifacts pre-existed
matches the current directory state (`striatum/0044-workspace-ui-rework/{domain,
ergonomics,ops,traceability}/` are all empty before this artifact).

### F1. Mesh diagnostics field naming is ambiguous between RFC copy and model fields (implementation-side)

RFC 0033 §4 Mesh describes the Hull and Deck diagnostics cards in terms of
"boundary edges, non-manifold edges, degenerate faces" (`docs/rfcs/0033-workspace-ui-rework.md:185-189`).
The current model exposes five fields, splitting boundary and non-manifold counts
into raw and welded variants: `raw_boundary_edges`, `raw_nonmanifold_edges`,
`welded_boundary_edges`, `welded_nonmanifold_edges`, `degenerate_faces`
(`kayakgen/eval/mesh_diagnostics.py:75-79`). The RFC does not pick between raw
and welded, so the implementer can land it inconsistently. Not a scope blocker;
flows to the ledger as an explicit choice for the Mesh tab.

### F2. Mesh-profile UI labels differ from canonical profile IDs

RFC 0033 §4 says the profile select offers `open-wetted-surface` (default) and
`watertight-solid` (disabled, with the tooltip "Current generated packages do not
satisfy watertight-solid readiness.") (`docs/rfcs/0033-workspace-ui-rework.md:191-196`).
The model's canonical profile names are `open_wetted_surface_resistance_v1` and
`watertight_solid_resistance_v1` (`kayakgen/eval/mesh_package.py:55-80`). RFC 0033
is using human-readable labels rather than the literal profile IDs from the
manifest. This is consistent with the README description of the RFC 0010
landed slice but should be wired explicitly so the chip text and the manifest
profile_name stay traceable. Not a scope blocker.

### F3. RFC 0033 supersedes RFC 0008's two-column layout without saying so in either RFC

RFC 0008 commits to a two-column Vuetify layout (left rail + right 3D + tabs).
RFC 0033 replaces `SinglePageWithDrawerLayout` and the matplotlib `GridSpec` with
a three-region shell (`docs/rfcs/0033-workspace-ui-rework.md:88-96`). Neither RFC
0008 nor RFC 0033 records the supersession; `docs/rfcs/README.md:33-34` still
describes RFC 0008's web slice as the accepted boundary. This is an RFC-index
hygiene finding, not a blocker — the workflow is allowed to land the rework
because RFC 0033 is proposed and explicit about replacing the existing shells —
but a one-line cross-link in RFC 0008 (and a status note in `docs/rfcs/README.md`
after acceptance) would prevent future readers from treating the two layouts as
co-equal commitments.

### F4. `target_speed_kt` is a UI-state-only field, not a Hull field

RFC 0033 §2 lists `target_speed_kt` among the parameter-rail sliders and labels
it "view-only" (`docs/rfcs/0033-workspace-ui-rework.md:115-119`). The current
`Hull` dataclass does not carry `target_speed_kt`; it lives only in the web state.
This matches the "view-only" qualifier, so the RFC is internally consistent, but
implementers should not extend the Hull model on its behalf. Logged here so the
ledger can pin the constraint.

### F5. RFC 0033's `Advisory` value object is a proper subset of `DesignValidityFinding`

RFC 0031 already defines `DesignValidityFinding` with `code`, `level`,
`severity`, `message`, `source`, `parameters` (`kayakgen/model/validity.py:58-72`).
RFC 0033 §7 proposes a smaller `Advisory` record `{code, message, field_refs}`
and explicitly says it is "shape-compatible with RFC 0031's `DesignValidityFinding`
and may collapse into that record in a future revision"
(`docs/rfcs/0033-workspace-ui-rework.md:380-393`). The current `DesignAdvisory`
keeps `warnings: tuple[str, ...]` at `kayakgen/model/advisory.py:27`. The
proposed additive `advisories: tuple[Advisory, ...]` field preserves the
RFC 0031 compatibility constraint. No mismatch; flagged for traceability.

### F6. All non-trivial RFC 0033 "today" claims are accurate

Verified against current code:

- Web `app.py` exposes the toolbar Reset/Share/Export buttons and three flat tabs
  (`kayakgen/ui/web/app.py` toolbar block and `tabs` block; the toolbar is
  present today, contrary to the RFC's "no toolbar" wording, but the broader
  "ad-hoc, not a workspace shell" framing still holds). The RFC's tabbed-but-flat
  characterisation is consistent with the source.
- VTK background `(0.10, 0.10, 0.18)` is set at `kayakgen/ui/web/app.py:150`,
  exactly the value the RFC quotes.
- Controllers expose every helper the RFC names: `clamp_beam_wl_state`,
  `metrics_from_state`, `analysis_view_model`, `analysis_lines_from_state`,
  `cfd_status_lines_from_payload` (`kayakgen/ui/web/controllers.py:51, 97, 136,
  189, 589`); `encode_hull_query` / `decode_hull_query`
  (`kayakgen/ui/web/state.py:51, 56`).
- The three new helpers the RFC adds (`evaluation_summary(state)`,
  `mesh_diagnostics_lines_from_state`, `mesh_package_view_model(path)`) are
  genuinely absent today.
- REST routes `/api/evaluate`, `/api/stl`, `/api/cfd/*`, `/api/hulls/*` all
  exist (`kayakgen/ui/web/controllers.py:1131-1142`).
- `HULL_STATE_FIELDS` is defined in `kayakgen/ui/web/state.py:19-31`.
- Desktop has hardcoded `steelblue`, `seagreen`, `crimson` plot colours
  (`kayakgen/ui/desktop.py:397-426`), separate PyVista window
  (`kayakgen/ui/desktop.py:105, 293-303`), and a "Generate STLs" button
  (`kayakgen/ui/desktop.py:197`).
- Desktop GUI does not surface `Cm` today: `SLIDERS` (`kayakgen/ui/desktop.py:40-52`)
  and `gui_params.GUI_TO_HULL` (`kayakgen/ui/gui_params.py:9-20`) lack it; this
  matches the RFC's call-out that desktop adopts Cm in this rework.
- `desktop._classify` exists for the validity badge derivation
  (`kayakgen/ui/desktop.py:305-319`).
- `MeshPackageManifest` is exported from `kayakgen/eval/mesh_package.py` and the
  `cfd_surface_candidate` readiness level returned for currently generated
  packages is consistent with `docs/rfcs/0010-cfd-ready-mesh-contract.md:67-77`
  and the README's "current generated packages remain open-surface and not
  `cfd_ready`" wording (`docs/rfcs/README.md`).
- `ClaimState` literals include `uncalibrated_comparative`
  (`kayakgen/eval/claims.py:10-18`), matching RFC 0025's table and the chip
  copy quoted in RFC 0033 §4 Resistance.
- `CfdRunStatus` literals are `queued | running | succeeded | failed |
  unavailable` (`kayakgen/eval/cfd/jobs.py:24`); the RFC's "Status chips and
  error-kind copy use the existing `CfdRunStatus` literals" line is grounded.
- `validation_error_payload` exists at `kayakgen/ui/web/controllers.py:73-94`,
  matching the RFC's invalid-hull-state banner contract.
- `ResistanceMetadata.warnings` is a real list, exposed through the analysis
  payload (`kayakgen/eval/contract.py:23-53` and `kayakgen/ui/web/controllers.py:185`).

### F7. Scaffold validation

- `docs/workflows/0044-workspace-ui-rework/workflow.json` references nine role
  files; all nine exist under `roles/`.
- All eight prompt files referenced by `workflow.json` exist under `prompts/`.
- All required context docs declared in `workflow.json.context_docs` exist on
  disk, including `CLAUDE_DESIGN_UI_REWORK_PROMPT.md`, `docs/USER_GUIDE.md`, and
  `docs/workflows/0042-design-constraint-surfacing-revision/workflow.json`.
- The four first-pass review jobs have disjoint write scopes
  (`striatum/0044-workspace-ui-rework/{traceability,domain,ergonomics,ops}/`),
  matching `parallelism.require_disjoint_write_scopes: true`.
- The remediation artifact's "search found no remaining blocker references to
  the unstored original handoff" claim was spot-checked: RFC 0033 itself names
  the handoff only as provenance (`docs/rfcs/0033-workspace-ui-rework.md:5-13`)
  and routes scope/copy/acceptance through the RFC.

## Required actions

All actions are implementation-flow and route to the findings ledger; no item
returns to `review_remediation`.

1. Pick raw vs. welded for the Mesh tab Hull/Deck diagnostics chip and pin that
   choice in the ledger so Hull and Deck cards stay aligned
   (`kayakgen/eval/mesh_diagnostics.py:75-79`, RFC 0033 §4 Mesh).
2. Map the RFC's `open-wetted-surface` / `watertight-solid` select labels to
   canonical profile IDs `open_wetted_surface_resistance_v1` /
   `watertight_solid_resistance_v1` in the ledger and reflect that label/ID
   distinction in the chip copy (`kayakgen/eval/mesh_package.py:55-80`,
   RFC 0033 §4 Mesh).
3. Note in the ledger that `target_speed_kt` stays in web state only and must
   not be added to `Hull` during this slice (RFC 0033 §2,
   `kayakgen/model/hull.py:14-93`).
4. (Optional, hygiene) Add a short cross-link in `docs/rfcs/0008-web-frontend.md`
   and a status note in `docs/rfcs/README.md` once RFC 0033 lands, so the
   two-column layout is not still read as the accepted boundary.

## Residual risk

- The mesh-diagnostics field-naming ambiguity (F1) and the profile label/ID
  distinction (F2) are the only places where the RFC's copy could be wired
  inconsistently with the existing payload. Both are caught by the
  forbidden-string regression suite in spirit but not in letter; the ledger
  should make the picks explicit so the implementer does not need to guess.
- RFC 0008's status text in `docs/rfcs/README.md` will read as authoritative
  until RFC 0033 lands; downstream agents picking up "what is being built" from
  the README alone could miss that the workspace shell supersedes the two-column
  layout. Low risk because RFC 0033 is now indexed and AGENTS.md routes new
  readers through the README.
- The remaining acceptance criteria, forbidden-claim strings, and chip copy in
  RFC 0033 §4–§8 are explicit and testable; downstream review lanes
  (domain, ergonomics, ops) own enforcement.
