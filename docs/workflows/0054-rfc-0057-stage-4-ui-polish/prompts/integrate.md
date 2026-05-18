# Integration Prompt

You run after every `implement_*` track has completed and published a patch
summary. Read each implementation's patch summary, the
`STAGE_4_DECISIONS.md` file, and the existing `_render_generate_tab()` in
`kayakgen/ui/web/app.py` before making changes.

Wire the new modules into the Generate tab:

- Replace the existing `_render_generate_tab()` body with calls to
  `render_spec_form_section(self)` (track 1) and
  `render_frontier_view_section(self)` (track 2).
- Per-row Pareto-pick rendering must call `render_fork_button(self, summary)`
  (track 6) on rows whose state is `succeeded`.
- In `KayakgenApp.__init__`, after the controller-callback wiring block,
  invoke `install_generate_state_listener(self)` (track 3) to enable the
  auto-poll cadence.
- Remove the legacy raw-JSON-only textarea render so the form-builder is the
  primary surface and the raw-JSON tab is collapsible (form-builder track
  provides the collapsible widget).

Add a panel-level integration test (`tests/test_generative_jobs_web.py`
extension) that creates the Trame app via `create_app`, submits a spec via
the form-builder, asserts a job lands in the listing, verifies the fork
button surfaces on a succeeded row, and confirms the panel never embeds any
forbidden-claim copy. Update `tests/test_web_layout.py` if `REVIEW_TABS`
ordering changes.

Requirements:

- The forbidden-claim scan, ui-theme orphan scan, and import-boundary scan
  must remain green.
- Do not re-implement any track's logic. Limit edits to the wiring layer
  and the integration test. If a track's module is missing or its public
  surface is wrong, escalate as a `needs_revision` for that track rather
  than patching around it.
- Run the full repo suite minus the env-gated OpenFOAM smoke before
  publishing your patch summary.

Publish the required patch summary artifact.
