# Task: Implement RFC 0002 — GUI Usability Improvements

Implement all seven improvements from RFC 0002 (provided as a context file).
The current source files `gui.py`, `pyvista_view.py`, and `generator.py` are
also provided as context. Read them carefully before writing any code.

Work through the items in the order listed below (lowest risk first).

---

## 1. Fix slider label clipping — `gui.py`

In `_build_sliders()`, add `label_location="bottom"` to each `widgets.Slider`
constructor call so labels appear below the track instead of to the left.

```python
s = widgets.Slider(ax, label, vmin, vmax, valinit=self.params[key],
                   label_location="bottom")
```

Also tighten the slider axis height slightly to `0.030` and reduce the font
size of each label to 8pt after creation:

```python
s.label.set_fontsize(8)
```

---

## 2. Debounce 3D updates + reduce preview resolution — `gui.py` + `generator.py`

### generator.py

Add an optional `stations` parameter to `get_mesh_arrays()`:

```python
def get_mesh_arrays(self, part_type: str, stations: int = None) -> tuple[np.ndarray, np.ndarray]:
    n = stations if stations is not None else self.num_stations
    x_positions = np.linspace(-self.L / 2, self.L / 2, n)
    ...  # rest unchanged, just replace self.num_stations with n
```

### pyvista_view.py

Change both `get_mesh_arrays` calls to use `stations=80`:

```python
hull_pv = _build_pv_mesh(*kg.get_mesh_arrays("hull", stations=80))
deck_pv = _build_pv_mesh(*kg.get_mesh_arrays("deck", stations=80))
```

Do the same in `update_mesh()`.

### gui.py

Add a QTimer debounce for 3D updates. Import at the top:

```python
from PyQt6.QtCore import QTimer
```

In `__init__`, after `self._pv_window = None`:

```python
self._3d_timer = QTimer()
self._3d_timer.setSingleShot(True)
self._3d_timer.setInterval(80)
self._3d_timer.timeout.connect(self._flush_3d)
```

Add method:

```python
def _flush_3d(self):
    if self._pv_window is not None and self._pv_window.isVisible():
        self._pv_window.update_mesh(self.params)
```

In `_on_change`, replace any direct `update_mesh` call with:

```python
if self._pv_window is not None and self._pv_window.isVisible():
    self._3d_timer.start()
```

Remove the `update_mesh` call from the end of `update_plots()` entirely —
the timer handles it.

---

## 3. "3D View" loading state — `gui.py`

Replace `_on_open_3d` with:

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

---

## 4. Window title with dimensions — `pyvista_view.py`

In `__init__`, change the title line to:

```python
self._update_title(params)
```

Add method:

```python
def _update_title(self, params: dict):
    self.setWindowTitle(
        f"Kayak 3D — {params['length']:.1f}m × {params['beam']:.2f}m beam"
    )
```

Call `self._update_title(params)` at the end of `update_mesh()`.

---

## 5. Live derived metrics panel — `gui.py`

Add a helper method:

```python
def _compute_metrics(self) -> dict:
    p = self.params
    L, B, T = p["length"], p["beam"], p["draft"]
    Cp = p["Cp"]
    Cm = 0.85
    Cwp = 0.7 + 0.16 * Cp
    vol = Cp * Cm * L * B * T
    disp_kg = vol * 1025
    wpa = Cwp * L * B
    lob = L / B
    mid_area = Cm * B * T
    return dict(disp_kg=disp_kg, wpa=wpa, lob=lob, mid_area=mid_area)
```

In `_build_button()`, add a metrics text area below the status text:

```python
self.ax_metrics = self.fig.add_axes([0.04, 0.14, 0.24, 0.10])
self.ax_metrics.axis("off")
self.metrics_text = self.ax_metrics.text(
    0.0, 1.0, "", ha="left", va="top",
    transform=self.ax_metrics.transAxes,
    fontsize=7.5, fontfamily="monospace",
)
```

Add a method to refresh metrics:

```python
def _refresh_metrics(self):
    m = self._compute_metrics()
    txt = (
        f"Est. displ.  {m['disp_kg']:6.0f} kg\n"
        f"Waterplane   {m['wpa']:6.2f} m²\n"
        f"LOA/B ratio  {m['lob']:6.2f}\n"
        f"Mid section  {m['mid_area']:6.4f} m²"
    )
    self.metrics_text.set_text(txt)
```

Call `self._refresh_metrics()` at the end of `_on_change()` and once during
`__init__` after `self.update_plots()`.

Adjust the `btn_3d` axes y position from `0.13` to `0.255` to make room for
the metrics block above it. Also shift `ax_btn` and `ax_rst` up accordingly:
- `ax_btn`:     y = `0.205`
- `ax_rst`:     y = `0.205`
- `ax_3d`:      y = `0.255`  ← this is the 3D View button
- `ax_status`:  y = `0.160`
- `ax_metrics`: y = `0.020`

---

## 6. Arrow-key nudge — `gui.py`

In `__init__`, after building sliders, add:

```python
self._last_slider_key = list(self.sliders.keys())[0]
self.fig.canvas.mpl_connect("key_press_event", self._on_key)
```

For each slider, wrap its on_changed to track which was last touched:

```python
for key, s in self.sliders.items():
    s.on_changed(lambda v, k=key: self._track_slider(k))
```

Add methods:

```python
def _track_slider(self, key: str):
    self._last_slider_key = key

def _on_key(self, event):
    if event.key not in ("left", "right", "up", "down"):
        return
    s = self.sliders[self._last_slider_key]
    delta = (s.valmax - s.valmin) * 0.01
    direction = 1 if event.key in ("right", "up") else -1
    s.set_val(float(np.clip(s.val + direction * delta, s.valmin, s.valmax)))
```

---

## 7. STL save dialog — `gui.py`

Replace `_on_generate` with:

```python
def _on_generate(self, _event):
    from PyQt6.QtWidgets import QFileDialog
    path, _ = QFileDialog.getSaveFileName(
        None, "Save kayak STLs", "kayak", "STL files (*.stl)"
    )
    if not path:
        return
    stem = path.removesuffix("_hull.stl").removesuffix(".stl")
    self.status.set_text("Generating…")
    self.fig.canvas.draw()
    kg = KayakGenerator(**self.params)
    kg.generate_stl("hull", f"{stem}_hull.stl")
    kg.generate_stl("deck", f"{stem}_deck.stl")
    import os
    self.status.set_text(f"Saved {os.path.basename(stem)}_hull/deck.stl")
    self.fig.canvas.draw()
```

---

## Output

After implementing all seven items, write
`docs/workflows/gui-usability.json/IMPLEMENTATION.md` summarising:
- Which changes were made in each file
- Any deviations from the RFC and why
- How to verify each improvement works

Verify syntax with:
```bash
python -m py_compile gui.py pyvista_view.py generator.py
```
