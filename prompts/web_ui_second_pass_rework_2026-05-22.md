# Claude Design — Kayak-Gen Web UI: Second-Pass Rework

You are Claude Design working on `/home/halbritt/git/kayak-gen`. The web
frontend (`kayakgen serve`, Trame + Vuetify 3) has been through one rework
cycle and the operator is still unhappy with it. Your job is to produce a
**second-pass** UI redesign handoff that a Codex implementer can land in
one or two small RFCs.

Do not write code in this pass.

## Read first

1. **`prompts/CLAUDE_DESIGN_UI_REWORK_PROMPT.md`** — the previous rework brief.
   Treat its "Design Constraints", "Required Deliverable", and "Output
   Rules" sections as still binding for this pass unless this prompt
   explicitly overrides them. Notably: this is an engineering tool, not a
   marketing page; no hero, no gradients/orbs/bokeh; truthful claim
   boundaries always visible.
2. `AGENTS.md` (six-file orientation list) and `docs/CONTEXT_HYGIENE.md`.
3. `docs/PRD.md` for scope; `docs/USER_GUIDE.md` `### serve` section for
   the current surface; `docs/UBIQUITOUS_LANGUAGE.md` for vocabulary.
4. **Recent UX work that just landed** — do not undo it:
   - RFC 0060 (`docs/rfcs/0060-*.md`) + RFC 0061 (`docs/rfcs/0061-*.md`):
     `HullParameterMetadata` registry now feeds friendly labels and
     hover tooltips to the Generate panel form and the desktop sliders.
     The registry is at `kayakgen/ui/parameter_metadata.py`. Any new
     hull-field label belongs in that registry, not redefined inline.
   - RFC 0057 stage 4 (`docs/rfcs/0057-*.md`): the Generate panel +
     form-builder + 2D Pareto frontier + auto-poll + fork-with-seed.
     This is the surface most likely to feel "terrible" today — start
     your investigation there.
5. The live UI modules:
   - `kayakgen/ui/web/app.py` (top-level Trame app)
   - `kayakgen/ui/web/generate_spec_form.py` (Generate panel)
   - `kayakgen/ui/web/generate_frontier_view.py` (2D Pareto scatter)
   - `kayakgen/ui/web/controllers.py`, `state.py`, `read_models.py`
6. `kayakgen/ui/desktop.py` for parity reference — the desktop slider
   labels just got registry-sourced; the web should feel like a
   first-class sibling, not a poor cousin.

## What is most likely wrong (start here, then go look)

The operator did not give specifics, so investigate these likely
suspects and prioritize the ones that survive contact with the live
UI:

- **Generate panel density and hierarchy.** The form-builder has
  variables, objectives, evaluators, algorithm, budget, and the
  CFD-in-loop acknowledgement stacked vertically with low visual
  hierarchy. Confirm by reading `generate_spec_form.py` and rendering
  it. Likely fix: a clearer two-column layout, section headers that
  the eye can scan, and progressive disclosure for the rare controls.
- **Pareto frontier readability.** The 2D scatter (`generate_frontier_view.py`)
  is the primary decision surface. Confirm whether axis labels, point
  colour mapping (claim-label aware per RFC 0058), hover tooltips,
  selected-candidate handoff, and the undo toast actually communicate
  what they're supposed to.
- **Jobs index ergonomics.** RFC 0057 stage 4 added a live-refreshing
  jobs list with fork-with-seed and log redaction. Look at how it
  handles failures, resumable state, cancellation, and progress.
- **Class preset selector + rail validity badge.** Documented in
  USER_GUIDE around the `### serve` section. Confirm whether the
  "Custom — sub-touring" / "In <class> envelope" copy actually reads
  as intended or feels like a sticker that no one understands.
- **Vocabulary surface.** `unvalidated_hydrostatic_comparison`,
  `raw_unvalidated`, `uncalibrated_comparative` appear in the UI by
  design (truthful claims are mandatory). Look for places where they
  ARE shown but in a way that confuses rather than informs, vs
  places where they should be shown but are hidden.

Anything else that smells off when you actually load `kayakgen serve` —
record it. The operator's "pretty terrible" is one data point; your
own first-load reaction is another.

## Hard constraints — do NOT propose changes that

- Alter the form's submitted JSON payload (RFC 0060 acceptance gate;
  the round-trip snapshot tests in `tests/test_generate_spec_form.py`
  are non-negotiable).
- Rename or weaken claim-state literals (`raw_unvalidated`,
  `unvalidated_hydrostatic_comparison`, `validated_hydrostatic_comparison`,
  `uncalibrated_comparative`, `validation_fixture`, `calibrated_model`,
  `validated_design_fitness`). These are pinned by
  `tests/test_vocabulary_coverage.py` and named in `DECISION_LOG.md`
  rows.
- Add new backend capabilities (new evaluators, new schemas, new CFD
  paths). The brief is presentation-only. Flag anything that would
  require backend work as a "deferred follow-up RFC" with a one-line
  scope note.
- Hide truthful warnings. RFC 0025/0027/0043/0058 claim gates +
  `not_safety_or_seaworthiness_claim` etc. must remain visible in
  every surface that shows the underlying number.
- Touch the desktop matplotlib UI. The desktop got its registry
  migration in RFC 0061; treat it as a sibling surface to keep
  aligned in concept, but the desktop is out of scope for this pass.

## Deliverable

Write the handoff to
`docs/design/WEB_UI_REWORK_2026-05-22.md` (create the file). Follow
the 10-section shape from `prompts/CLAUDE_DESIGN_UI_REWORK_PROMPT.md`
"Required Deliverable" — Design Intent, Primary User Flows,
Information Architecture, Screen Specifications, Component Inventory,
Truthfulness And Claim-State Rules, Visual System, Implementation Map,
Acceptance Checks For Codex, Open Questions.

Additions specific to this pass:

- **Pain audit (new section, before Design Intent).** List the
  concrete pain points you actually found in the live UI, with file:line
  citations to the offending code (or screenshot descriptions). If the
  operator's complaint turned out to be one or two specific issues
  hiding inside the broader Generate panel, name them.
- **Implementation Map must explicitly cite RFC 0060 / 0061 / 0057**
  for every proposed Generate-panel change, so the Codex implementer
  doesn't have to re-derive the dependency graph.
- **Acceptance Checks must reference the existing snapshot tests**
  (`tests/test_generate_spec_form.py` round-trip, byte-stable payload)
  as gates that must continue to pass.

If the changes you propose are large enough to warrant their own RFC
(e.g. a new top-level navigation, a new layout primitive, a new
graph component), say so explicitly in the Implementation Map and
sketch the RFC's Problem / Goals in one paragraph each. RFC 0062 is
the next free number.

## Output rules

- Output only the handoff Markdown file (`docs/design/WEB_UI_REWORK_2026-05-22.md`).
- No `author:` line.
- File:line citations for every claim about current behavior.
- Where you describe a layout, ASCII wireframes are fine and preferred
  over verbal-only description. Use them.
- Don't include implementation patches.
- Don't propose changes that contradict the hard constraints above.
  If a constraint feels wrong, flag it in Open Questions; don't
  silently violate it.
