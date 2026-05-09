# RFC 0002 Implementation

## Changes Made

### `gui.py`

- Moved slider labels below each slider track with `label_location="bottom"`, set slider axes to `0.030` high, and reduced slider label text to 8pt.
- Added an 80ms single-shot `QTimer` debounce for 3D updates. Slider changes still redraw the 2D matplotlib plots immediately, while visible PyVista updates are coalesced through `_flush_3d()`.
- Added immediate "Opening…" button feedback while the 3D window is created, then restored the "3D View" label after showing the window.
- Added a live derived metrics panel with estimated displacement, waterplane area, LOA/B ratio, and midship section area.
- Added arrow-key nudging for the most recently touched slider, using 1% of that slider's range per key press.
- Replaced hardcoded STL output filenames with a Qt save dialog. The chosen stem now writes `{stem}_hull.stl` and `{stem}_deck.stl`.

### `pyvista_view.py`

- Changed initial and live preview mesh creation to call `get_mesh_arrays(..., stations=80)`.
- Added `_update_title()` so the 3D window title shows current length and beam, and refreshed that title after each mesh update.

### `generator.py`

- Added an optional `stations` argument to `get_mesh_arrays()`. When omitted, it preserves the existing `self.num_stations` behavior used by STL generation.

## Deviations

No intentional deviations from the requested implementation path.

## Verification

- Run `python -m py_compile gui.py pyvista_view.py generator.py` to verify syntax.
- Launch `python gui.py` and confirm slider labels are below the tracks, fully visible, and rendered at the smaller label size.
- Open "3D View", then drag sliders quickly. The 2D plots should update immediately while the 3D view updates after the debounce interval instead of rendering every drag event.
- Click "3D View" from a cold start and confirm the button briefly changes to "Opening…" before the PyVista window appears.
- Confirm the PyVista window title includes the current length and beam, then adjust either slider and confirm the title updates after the 3D mesh refresh.
- Confirm the metrics panel appears below the buttons and updates live. With defaults, LOA/B should be about `8.18`.
- Move a slider, then press left/right/up/down while focus is in the matplotlib window. The last touched slider should nudge by 1% of its range.
- Click "Generate STLs", choose a save path, and confirm both `{stem}_hull.stl` and `{stem}_deck.stl` are written.
