# RFC 0002: GUI Usability Improvements

Status: landed
Date: 2026-05-09
Context: gui.py, pyvista_view.py; follows RFC 0001 (3D rendering panel)

## Problem

The current GUI has several usability friction points identified after
first use:

1. **Slider panel occlusion** — the slider labels on the left side of the
   matplotlib figure are clipped at the window edge. There is no left margin,
   so the first character of each label is hidden or very tight.

2. **3D render lag** — every slider drag event triggers a full mesh rebuild
   (`KayakGenerator.get_mesh_arrays()` × 2) and a full VTK render. At 150
   stations × 79 points, each rebuild takes ~5–20ms and normal-computation
   adds more. When the user drags quickly, events queue and the window feels
   sluggish or frozen.

3. **No feedback during 3D window open** — clicking "3D View" triggers a
   cold VTK scene build (~500ms–1s) with no spinner or status indicator.
   The button appears unresponsive.

4. **Two separate windows feel disconnected** — the matplotlib parameter
   window and the PyVista 3D window have no visual relationship. Users must
   alt-tab between them and may not realise the 3D view tracks the sliders.

5. **No display of key derived metrics** — the user sets Cp, beam, draft,
   etc. but never sees the resulting displacement volume, waterplane area, or
   LOA/B ratio. These numbers help a builder sanity-check their design without
   running a separate calculator.

6. **Slider range limits are arbitrary** — the hard-coded min/max values
   (e.g. beam 0.3–0.9 m) have no in-UI explanation and can't be overridden
   without editing source.

7. **No keyboard control** — there is no way to nudge a parameter by a small
   increment with the keyboard, which makes fine-tuning tedious with a mouse.

8. **"Generate STLs" overwrites without warning** — if kayak_hull.stl and
   kayak_deck.stl already exist, they are silently overwritten. There is no
   way to specify an output filename.

## Goals

- Slider labels are fully legible at default window size without resizing.
- 3D view updates feel instantaneous during fast slider drag (no queued
  renders backing up).
- Clicking "3D View" shows immediate visual feedback within 100ms.
- Key derived metrics (displacement volume, waterplane area, LOA/B ratio,
  midship section area) are visible and update live.
- Users can nudge any focused slider with arrow keys.
- "Generate STLs" prompts for a filename or at minimum shows the output path
  and does not silently overwrite.

## Non-Goals

- Full Qt migration of the matplotlib window (deferred; large refactor).
- Embedding the 3D view inside the matplotlib figure layout.
- Hydrostatics calculations beyond simple geometric approximations (displaced
  volume, waterplane area).
- Undo/redo of parameter changes.
- Saving/loading parameter presets to disk (separate RFC).

## Proposal

### 1. Fix slider label clipping (gui.py)

The root cause is the `GridSpec(left=0.32)` and slider axes positioned at
`x=0.04` with `width=0.24`. The label text overflows left of x=0.04.
matplotlib `Slider` places its label to the left of the track by default.

**Fix:** switch to `label_location="bottom"` (matplotlib ≥3.7) so the label
sits below the track rather than to its left, eliminating the clipping
entirely. Alternatively, widen the left margin to `left=0.36` and shift all
slider axes right to `x=0.06`.

Recommended: `label_location="bottom"` — it also gives more horizontal space
to the slider track itself.

### 2. Debounce 3D mesh updates (gui.py + pyvista_view.py)

Every `_on_change` event currently calls `update_plots()` synchronously,
which calls `pyvista_window.update_mesh()` synchronously. During fast drag,
events arrive faster than renders complete, causing a queue of pending redraws.

**Fix:** add a 80ms debounce timer in `KayakGUI` that coalesces rapid slider
events into a single 3D update. 2D plots (cheap matplotlib redraws) continue
to update on every event; only the 3D VTK render is debounced.

```python
from PyQt6.QtCore import QTimer   # available once qtagg backend is loaded

class KayakGUI:
    def __init__(self):
        ...
        self._3d_timer = QTimer()
        self._3d_timer.setSingleShot(True)
        self._3d_timer.setInterval(80)   # ms
        self._3d_timer.timeout.connect(self._flush_3d_update)

    def _on_change(self, _val):
        ...
        self.update_plots()              # 2D: always immediate
        if self._pv_window and self._pv_window.isVisible():
            self._3d_timer.start()       # restart 80ms window

    def _flush_3d_update(self):
        if self._pv_window and self._pv_window.isVisible():
            self._pv_window.update_mesh(self.params)
```

Remove the `update_mesh` call from the end of `update_plots()`.

Additionally, reduce the default `num_stations` from 150 to 80 for the live
3D preview (the STL export continues to use 150). Add a `stations` parameter
to `get_mesh_arrays()` that overrides `self.num_stations`:

```python
def get_mesh_arrays(self, part_type, stations=None):
    n = stations or self.num_stations
    x_positions = np.linspace(-self.L / 2, self.L / 2, n)
    ...
```

`PyVistaWindow` calls `kg.get_mesh_arrays(part, stations=80)`; `generate_stl`
continues to use `self.num_stations=150`.

### 3. "3D View" button loading state (gui.py)

Set the button label to "Opening…" on click and restore it after the window
is shown:

```python
def _on_open_3d(self, _event):
    self.btn_3d.label.set_text("Opening…")
    self.fig.canvas.draw()
    from pyvista_view import PyVistaWindow
    if self._pv_window is None or not self._pv_window.isVisible():
        self._pv_window = PyVistaWindow(self.params)
        self._pv_window.show()
    self.btn_3d.label.set_text("3D View")
    self.fig.canvas.draw()
```

### 4. Window title linkage (pyvista_view.py)

Set the PyVista window title to include the current LOA so the user can
glance at the taskbar and know which design they're looking at:

```python
self.setWindowTitle(f"Kayak 3D — {params['length']:.1f}m × {params['beam']:.2f}m")
```

Update the title in `update_mesh()` as well.

### 5. Live derived metrics panel (gui.py)

Add a read-only text block below the sliders showing four computed values
that update on every slider event:

| Metric | Formula |
|--------|---------|
| Est. displacement | `Cp × Cm × L × B × T × 1025` kg (seawater) |
| Waterplane area | `Cwp × L × B` where `Cwp ≈ 0.7 + 0.16×Cp` (empirical) |
| LOA/B ratio | `L / B` |
| Midship section area | `Cm × B × T` |

These are geometric approximations, not hydrostatics. Label them clearly
as "Estimates" to avoid implying precision.

Render as a matplotlib `Text` object in a dedicated axes below the sliders,
updated in `_on_change`.

### 6. Arrow-key nudge for sliders (gui.py)

Connect matplotlib's key-press event to nudge the most-recently-touched
slider by ±1% of its range:

```python
self.fig.canvas.mpl_connect("key_press_event", self._on_key)
self._active_slider_key = None

def _on_key(self, event):
    if self._active_slider_key and event.key in ("left", "right", "up", "down"):
        s = self.sliders[self._active_slider_key]
        delta = (s.valmax - s.valmin) * 0.01
        direction = 1 if event.key in ("right", "up") else -1
        s.set_val(np.clip(s.val + direction * delta, s.valmin, s.valmax))
```

Track the active slider by adding an `on_changed` wrapper that records which
key was last moved.

### 7. STL output filename prompt (gui.py)

Replace the hardcoded filenames with a `QFileDialog` save prompt. On click:

```python
from PyQt6.QtWidgets import QFileDialog
path, _ = QFileDialog.getSaveFileName(
    None, "Save STL", "kayak_hull.stl", "STL files (*.stl)"
)
if path:
    stem = path.removesuffix("_hull.stl").removesuffix(".stl")
    kg.generate_stl("hull", f"{stem}_hull.stl")
    kg.generate_stl("deck", f"{stem}_deck.stl")
    self.status.set_text(f"Saved {stem}_hull.stl + _deck.stl")
```

If the user cancels, do nothing and clear the status.

## Acceptance Criteria

- Slider labels are fully visible at 1440×900 and 1920×1080 without
  resizing the window.
- Dragging a slider as fast as possible for 2 seconds results in at most
  one queued 3D render in-flight at any moment; the window does not freeze.
- Clicking "3D View" changes the button label within 100ms of the click.
- The derived-metrics block updates on every slider event and shows correct
  LOA/B ratio (verifiable by inspection: L=4.5, B=0.55 → 8.18).
- Arrow keys nudge the last-moved slider when focus is in the matplotlib
  figure.
- "Generate STLs" opens a save dialog and produces `{stem}_hull.stl` and
  `{stem}_deck.stl` at the chosen path.

## Open Questions

- **Debounce interval**: 80ms tested on M-series MacBook; should this be
  configurable or auto-tuned based on measured render time?
- **Metrics panel height**: how much vertical space can the metrics block
  take before it crowds the sliders on smaller screens?
- **QTimer dependency**: importing `QTimer` from PyQt6 at module level in
  `gui.py` adds a hard Qt dependency to what was previously a pure-matplotlib
  file. Acceptable given the 3D View button already requires Qt?

## Implementation Path

- Step 1 — Fix slider label clipping (`label_location="bottom"` or margin
  increase). ~5 lines in `gui.py`. Lowest risk, ship first.
- Step 2 — Add debounce timer and reduce 3D preview stations to 80.
  ~20 lines in `gui.py`, 2 lines in `generator.py`, 1 line in
  `pyvista_view.py`.
- Step 3 — "3D View" loading label. ~4 lines in `gui.py`.
- Step 4 — Window title linkage. ~3 lines in `pyvista_view.py`.
- Step 5 — Derived metrics panel. ~25 lines in `gui.py`.
- Step 6 — Arrow-key nudge. ~15 lines in `gui.py`.
- Step 7 — STL filename dialog. ~10 lines in `gui.py`.

Total: ~85 lines changed/added across 3 files. No new dependencies beyond
PyQt6 (already required by the 3D view).

## Domain Modeling

These are pure UI-layer changes. No domain concepts are introduced or
modified. The derived metrics (displacement estimate, waterplane area) are
display-only approximations and do not belong in `KayakGenerator` — they
live in the view layer and are labelled as estimates. If precise hydrostatics
are later added to `KayakGenerator` (a separate RFC), the metrics panel would
be wired to those computed values instead.
