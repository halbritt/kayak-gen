# Claude Design Prompt: Kayak-Gen UI Rework

You are Claude Design working on `/home/halbritt/git/kayak-gen`. Your job is
to produce an implementation-ready UI redesign handoff for Codex implementers.
Do not implement code in this pass.

## Required Context

Read these files first:

- `AGENTS.md`
- `docs/PRD.md`
- `docs/USER_GUIDE.md`
- `docs/rfcs/README.md`
- `docs/design/kayak_hull_design_constraints.md`
- `kayakgen/ui/web/app.py`
- `kayakgen/ui/web/controllers.py`
- `kayakgen/ui/web/state.py`
- `kayakgen/ui/desktop.py`
- `kayakgen/ui/gui_params.py`

Then inspect related tests on demand, especially `tests/test_web.py`,
`tests/test_gui_params.py`, and any browser or CLI tests that describe user
flows.

## Objective

Redesign the kayak-gen user experience around the current product direction:
a working parametric kayak hull tool that is moving toward a generative CFD
pipeline with desktop and web frontends. The design must help builders and
technical users move through parameter editing, constraint warnings,
hydrostatics/stability/resistance review, comparison, mesh/package readiness,
and CFD job status without implying unsupported design-fitness, calibrated
resistance, real-solver, or hosted-worker claims.

The output must be directly usable by Codex as an implementation brief. Prefer
precise interface structure, labels, state tables, component behavior, and
acceptance checks over broad visual direction.

## Design Constraints

- Treat this as an operational engineering tool, not a marketing page.
- Do not create a landing-page hero.
- Avoid decorative gradients, orbs, bokeh, illustration-first layouts, and
  card-heavy marketing composition.
- Favor dense but readable information hierarchy, predictable navigation,
  compact controls, and side-by-side comparison where it improves decisions.
- Preserve truthful claim boundaries. Raw analytical resistance, raw CFD
  records, unvalidated fixtures, and mesh readiness warnings must remain
  visibly qualified.
- Make warnings and unsupported fields visible without blocking normal
  exploration.
- Keep desktop and web concepts aligned, while allowing each frontend to use
  native interaction patterns.
- Do not require new backend capabilities unless you explicitly label them as
  future/backlog.
- Do not hide domain complexity behind vague copy. Use precise but concise
  labels.
- Design for responsive browser layouts. Mobile can be compact and inspectable;
  it does not need to make every expert workflow equally fast.

## Required Deliverable

Create a Markdown design handoff with these sections:

1. **Design Intent**
   - One short paragraph describing the redesigned product surface.
   - Explicit statement of the claims the UI must not make.

2. **Primary User Flows**
   - Parameter edit to geometry preview.
   - Constraint warning triage.
   - Hydrostatics/stability/resistance review.
   - Comparison between variants.
   - Mesh/package readiness inspection.
   - CFD job prepare/run/status review.

3. **Information Architecture**
   - Proposed top-level navigation or layout regions.
   - What appears in the first viewport on desktop.
   - What collapses or moves on narrow screens.

4. **Screen Specifications**
   - For each major screen/panel, include purpose, visible data, controls,
     empty states, loading states, error states, and disabled states.
   - Include exact user-facing labels for important controls and warnings.

5. **Component Inventory**
   - List reusable components Codex should build or refactor toward.
   - Include props/data requirements, states, and expected interactions.

6. **Truthfulness And Claim-State Rules**
   - Table of statuses and warning language for raw, unvalidated, candidate,
     accepted, unavailable, failed, and unsupported states.
   - Include how these statuses should surface in web and desktop UI.

7. **Visual System**
   - Layout density, typography scale, spacing, icon usage, table/list style,
     plot treatment, and color semantics.
   - Keep the palette restrained but not one-note. Avoid dominant purple,
     beige/tan, dark slate/blue, or brown/orange themes.
   - Specify colors as semantic tokens, not just hex values.

8. **Implementation Map**
   - Map each proposed UI change to likely files/modules.
   - Identify which changes are safe frontend-only work and which require
     backend or model support.
   - Mark any proposed future work that should become an RFC instead of being
     implemented immediately.

9. **Acceptance Checks For Codex**
   - Concrete checklist for automated tests.
   - Include browser checks, responsive screenshots, warning text assertions,
     keyboard/accessibility checks, and regression tests for unsupported claims.

10. **Open Questions**
    - Only list questions that block implementation.
    - If a reasonable assumption is safe, make the assumption and label it.

## Output Rules

- Output only the design handoff Markdown.
- Use file references where relevant.
- Do not include implementation patches.
- Do not include an `author:` line.
- Be specific enough that Codex can implement without interpreting visual
  intent from prose alone.
