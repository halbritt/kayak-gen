# Role: implementer

You land RFC 0061 (desktop sliders on `HullParameterMetadata`) in a
single change set. Closes D043's named "desktop `SLIDERS` migration to
the same registry" follow-up.

You extend the existing registry with a one-entry
`VIEW_PARAMETER_METADATA` for the view-only `target_speed_kt`, add a
small `desktop_slider_ranges` module with `SLIDER_RANGES`,
`SLIDER_STEPS`, `SLIDER_DEFAULTS` (numeric values byte-equal to today's
desktop literals; only the keys rename to canonical Hull JSON form),
rewrite `KayakGUI`'s `SLIDERS` / `DEFAULTS` / `GLOBAL_RANGES` /
`SLIDER_STEPS` / `_NON_HULL_GUI_KEYS` to derive from the registry,
retire the `_GUI_TO_HULL` indirection in `desktop.py` and
`pv_window.py`, shrink `kayakgen/ui/gui_params.py` to a
`DeprecationWarning` shim, add a regression test pinning the five
§5 assertions, and retarget the existing `tests/test_gui_params.py`
to canonical Hull keys plus a deprecation-warning assertion.

You do not touch `CHANGELOG.md`, audit `FINDINGS.md` files, RFC source
files, `docs/rfcs/README.md`, or `docs/DECISION_LOG.md` — those are
the parent agent's job.

Use the maximal number of useful sub-agents with disjoint write scopes
if you split the work, but keep one integrator responsible for final
tests and the patch summary.
