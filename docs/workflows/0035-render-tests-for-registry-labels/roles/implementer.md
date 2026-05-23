# Role: implementer

You close audit batch R4 (AUD-O-009 and AUD-O-010) from the
2026-05-23 release_candidate audit by adding two new render-
verification tests. The workflow is tests-only — no production source
is touched.

You add:

- `tests/test_generate_panel_label_rendering.py` — captures
  `v3.VTextField` (and `v3.VSelect`) constructor calls inside
  `render_spec_form_section` via monkeypatch around
  `create_app(initial_hull=Hull())`, then asserts every base-hull
  rail `VTextField` has `hint=description(key)` and
  `label=label_with_unit(key)` for each `BASE_HULL_KEYS` entry, plus
  state-seeded picklist title checks for objectives and the variable
  selector.

- `tests/test_desktop_slider_labels.py` — constructs `KayakGUI()`
  headlessly (matplotlib Agg backend, `plt.show` patched out) and
  asserts each `KayakGUI.SLIDERS` row's matplotlib `Slider`
  `.label.get_text()` equals `label_with_unit(row[0])`, plus three
  named spot checks for `Cp`, `length_m`, and `target_speed_kt`.

You do not touch the source modules
(`kayakgen/ui/parameter_metadata.py`,
`kayakgen/ui/web/generate_spec_form.py`,
`kayakgen/ui/desktop.py`), the audit `FINDINGS.md` files,
`CHANGELOG.md`, RFC sources, `docs/rfcs/README.md`, or
`docs/DECISION_LOG.md` — those are the parent agent's job (or
upstream's).

Use the maximal number of useful sub-agents with disjoint write
scopes if you split the work between the web test and the desktop
test, but keep one integrator responsible for the final pytest run
and the patch summary.
