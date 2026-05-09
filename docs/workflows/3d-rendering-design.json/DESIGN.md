# 3D Rendering Implementation Design

author: author-claude-code-local-001

## 1. Library Choice

**PyVista 0.48.x + pyvistaqt 0.11.x**

```
pip install "pyvista>=0.48,<0.49" "pyvistaqt>=0.11,<0.12" "PyQt6>=6.6,<6.10"
```

PyVista wraps VTK's GPU-accelerated OpenGL renderer. For the kayak mesh
(~11,850 vertices × 2 surfaces = ~23,000 triangles), VTK renders sub-millisecond
per frame. PyVista's `QtInteractor` is a `QWidget` subclass that can be embedded
beside a matplotlib `FigureCanvasQTAgg` in a single `QMainWindow`.

**Version pins:**
- `PyQt6 < 6.10` — pyvistaqt issue #8285 (hang with PySide6/PyQt6 ≥ 6.10, open May 2026)
- `pyvistaqt < 0.12` — stable API surface for the embedding approach used here

**No system-level dependencies beyond pip.** VTK ships as a self-contained
wheel (~350–500 MB installed). PyQt6 is also a pip wheel.

---

## 2. Integration Architecture

**Separate Qt window, launched on demand.**

The existing `gui.py` runs a matplotlib figure under `plt.show()`, which
blocks the Python process in a matplotlib event loop. Migrating the entire
GUI to `QMainWindow` in one step is a large refactor; it also adds risk
to the working parameter sliders.

Instead, the 3D window is a lightweight second window:

- The main `gui.py` (matplotlib) stays unchanged.
- When the user clicks a new **"3D View"** button, a `PyVistaWindow`
  (`QMainWindow` containing a `pyvistaqt.QtInteractor`) is constructed and
  shown. The matplotlib figure and the PyVista window run in separate
  windows but share the same process.
- This requires switching matplotlib to a Qt backend so both windows share
  the same Qt event loop:

```python
import matplotlib
matplotlib.use("qtagg")          # must be set before any other matplotlib import
import matplotlib.pyplot as plt
```

- When PyVista window is open, slider drag events in the matplotlib figure
  call `update_plots()` as today; additionally, they call
  `pyvista_window.update_mesh(kg)` if the 3D window exists.

**Why not embed in the same figure?**  
matplotlib's `GridSpec` uses matplotlib axes; PyVista's `QtInteractor` is a
Qt widget. Mixing them in a single `plt.figure()` is not supported — you would
need a `QMainWindow` with a `FigureCanvasQTAgg` plus a `QtInteractor` in a
`QSplitter`. That is the full Qt migration approach; it remains the long-term
target but is deferred to avoid scope creep. The two-window approach delivers
the 3D preview with minimal risk to the existing slider GUI.

**User workflow:**
1. Open `gui.py` — main matplotlib window with sliders and 2D views opens.
2. Click **"3D View"** button — PyVista window opens, showing the current hull+deck.
3. Drag sliders in the matplotlib window — both 2D views and 3D view update.
4. Close PyVista window — 3D updates stop; main window continues.

---

## 3. Geometry Pipeline

### 3a. Exposing mesh data from KayakGenerator

Add a new method to `KayakGenerator` that returns raw NumPy arrays instead of
writing an STL file. No changes to the existing `generate_stl()` method.

```python
def get_mesh_arrays(self, part_type: str) -> tuple[np.ndarray, np.ndarray]:
    """Return (vertices, faces) as NumPy arrays.

    vertices: shape (N, 3) — x, y, z
    faces:    shape (M, 3) — triangle indices into vertices
    """
    x_positions = np.linspace(-self.L / 2, self.L / 2, self.num_stations)
    all_slices = []
    for x in x_positions:
        slice_pts = self._get_slice_points(x, part_type)
        full_pts = np.column_stack(
            (np.full(len(slice_pts), x), slice_pts[:, 0], slice_pts[:, 1])
        )
        all_slices.append(full_pts)

    vertices = np.vstack(all_slices)
    pts_per_slice = len(all_slices[0])
    num_slices = len(all_slices)

    faces = []
    for i in range(num_slices - 1):
        s, n = i * pts_per_slice, (i + 1) * pts_per_slice
        for j in range(pts_per_slice - 1):
            c1, c2, n1, n2 = s + j, s + j + 1, n + j, n + j + 1
            if part_type == "hull":
                faces.extend([[c1, n1, c2], [c2, n1, n2]])
            else:
                faces.extend([[c1, n2, c2], [c2, n2, n1]])

    return vertices, np.array(faces)
```

This duplicates the triangulation logic from `generate_stl()`. A future
refactor can make `generate_stl()` call `get_mesh_arrays()` internally, but
that is not required for this feature.

### 3b. PyVista mesh construction

```python
import pyvista as pv

def _build_pv_mesh(vertices: np.ndarray, faces: np.ndarray) -> pv.PolyData:
    # PyVista face format: [3, i0, i1, i2, 3, i0, i1, i2, ...]
    pv_faces = np.hstack([np.full((len(faces), 1), 3), faces]).ravel()
    mesh = pv.PolyData(vertices, pv_faces)
    mesh.compute_normals(inplace=True)   # required for smooth shading
    return mesh
```

### 3c. Full pipeline on each update

```
slider event
  → on_slider_change() in KayakGUI
    → params updated
    → update_plots()          (existing 2D views)
    → pyvista_window.update_mesh(params)   (if 3D window open)
      → KayakGenerator(**params).get_mesh_arrays("hull")  → hull_verts, hull_faces
      → KayakGenerator(**params).get_mesh_arrays("deck")  → deck_verts, deck_faces
      → hull_actor.mapper.SetInputData(pv_hull)   # VTK in-place update
      → deck_actor.mapper.SetInputData(pv_deck)
      → plotter.render()
```

---

## 4. Update Strategy

**Full mesh rebuild on each slider event; no throttling initially.**

- Each slider drag event triggers `update_mesh()` immediately.
- `KayakGenerator(**params).get_mesh_arrays("hull")` takes ~2–5ms (150 stations
  × 79 points, pure NumPy). `get_mesh_arrays("deck")` is the same.
- PyVista `plotter.render()` with 23k triangles is sub-millisecond on GPU.
- Total round-trip estimated at ~15–30ms — well within interactive threshold.

**Throttling:** If profiling reveals that NumPy geometry rebuild becomes
expensive with higher station/point counts, add a 50ms debounce:

```python
from threading import Timer

class PyVistaWindow:
    def __init__(self): self._timer = None

    def update_mesh(self, params):
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(0.05, self._do_update, args=[params])
        self._timer.start()
```

This is a fallback; implement only if measured latency exceeds 100ms.

**In-place VTK update (no actor re-add):** Update `actor.mapper.dataset.points`
and `actor.mapper.dataset.faces` directly rather than calling `plotter.add_mesh()`
again. Re-adding an actor resets the camera; in-place update preserves the user's
current view angle.

```python
hull_pv = _build_pv_mesh(*kg.get_mesh_arrays("hull"))
self._hull_actor.mapper.dataset.points = hull_pv.points
self._hull_actor.mapper.dataset.faces  = hull_pv.faces
self._hull_actor.mapper.dataset.compute_normals(inplace=True)
self._plotter.render()
```

---

## 5. Camera and User Controls

PyVista's `QtInteractor` provides VTK's built-in trackball camera by default:

| Interaction | Gesture |
|-------------|---------|
| Rotate | Left-click drag |
| Pan | Middle-click drag (or Shift + left-click) |
| Zoom | Scroll wheel |
| Reset camera | Press `r` |

Add three preset-view toolbar buttons in the `PyVistaWindow`:

```python
for label, pos in [("Top",   (0, 0, 1)),
                   ("Side",  (1, 0, 0)),
                   ("Front", (0, 1, 0))]:
    btn = QPushButton(label)
    btn.clicked.connect(lambda _, p=pos: (
        self._plotter.camera_position = [(p[0]*10, p[1]*10, p[2]*5),
                                         (0, 0, 0), (0, 0, 1)],
        self._plotter.render()
    ))
    toolbar.addWidget(btn)
```

---

## 6. Visual Treatment

| Surface | Color | Opacity | Shading |
|---------|-------|---------|---------|
| Hull (below waterline) | `#3a7ebf` (steel blue) | 1.0 | Smooth (Phong) |
| Deck (above waterline) | `#4caf6e` (sea green) | 0.85 | Smooth (Phong) |
| Waterline plane | `#aaddff` (light blue) | 0.2 | Flat |

**Setup:**

```python
hull_actor = plotter.add_mesh(
    hull_pv, color="#3a7ebf", smooth_shading=True,
    split_sharp_edges=True, show_edges=False,
)
deck_actor = plotter.add_mesh(
    deck_pv, color="#4caf6e", smooth_shading=True,
    split_sharp_edges=True, opacity=0.85, show_edges=False,
)
# Waterline plane at z=0
wl = pv.Plane(center=(0, 0, 0), direction=(0, 0, 1),
               i_size=kg.L * 1.1, j_size=kg.B * 1.5)
plotter.add_mesh(wl, color="#aaddff", opacity=0.2, show_edges=False)
```

**Lighting:** PyVista's default three-light rig is adequate. No custom lighting
needed. If the hull looks flat, add `plotter.enable_eye_dome_lighting()` (VTK
screen-space ambient occlusion approximation, one-line call).

**Background:** `plotter.set_background("#1a1a2e")` — dark navy, makes the hull
colors pop without being distracting.

**Axes:** `plotter.add_axes()` — small orientation widget in the corner showing
X/Y/Z directions.

---

## 7. Implementation Plan

### Step 1 — Add `get_mesh_arrays()` to `generator.py`

- File: `generator.py`
- ~25 lines added inside the `KayakGenerator` class
- No changes to existing methods
- Can be tested independently: `kg.get_mesh_arrays("hull")` should return
  arrays with shapes `(num_stations * pts_per_slice, 3)` and `(num_faces, 3)`

### Step 2 — Switch matplotlib backend in `gui.py`

- Add `import matplotlib; matplotlib.use("qtagg")` at the very top of `gui.py`,
  before any other matplotlib import.
- Install `PyQt6<6.10` if not already present.
- Verify the existing 2D GUI still works: `python gui.py`

### Step 3 — Create `pyvista_view.py`

New file `pyvista_view.py` (~120 lines):

```python
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton

from generator import KayakGenerator

def _build_pv_mesh(vertices, faces):
    pv_faces = np.hstack([np.full((len(faces), 1), 3), faces]).ravel()
    mesh = pv.PolyData(vertices, pv_faces)
    mesh.compute_normals(inplace=True)
    return mesh

class PyVistaWindow(QMainWindow):
    def __init__(self, params: dict):
        super().__init__()
        self.setWindowTitle("Kayak 3D View")
        self.resize(900, 650)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        # Preset-view toolbar
        toolbar = QHBoxLayout()
        layout.addLayout(toolbar)
        for label, cam in [
            ("Top",   [(0, 0, 20), (0, 0, 0), (0, 1, 0)]),
            ("Side",  [(20, 0, 2), (0, 0, 0), (0, 0, 1)]),
            ("Front", [(0, 20, 2), (0, 0, 0), (0, 0, 1)]),
            ("Iso",   [(10, 10, 6), (0, 0, 0), (0, 0, 1)]),
        ]:
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, c=cam: self._set_camera(c))
            toolbar.addWidget(btn)
        toolbar.addStretch()

        self._plotter = QtInteractor(central)
        layout.addWidget(self._plotter.interactor)

        self._plotter.set_background("#1a1a2e")
        self._hull_actor = None
        self._deck_actor = None
        self._build_scene(params)
        self._plotter.add_axes()
        self._plotter.reset_camera()

    def _build_scene(self, params: dict):
        kg = KayakGenerator(**params)

        hull_pv = _build_pv_mesh(*kg.get_mesh_arrays("hull"))
        deck_pv = _build_pv_mesh(*kg.get_mesh_arrays("deck"))

        self._hull_actor = self._plotter.add_mesh(
            hull_pv, color="#3a7ebf", smooth_shading=True,
            split_sharp_edges=True, show_edges=False, name="hull",
        )
        self._deck_actor = self._plotter.add_mesh(
            deck_pv, color="#4caf6e", smooth_shading=True,
            split_sharp_edges=True, opacity=0.85, show_edges=False, name="deck",
        )
        # Static waterline plane
        wl = pv.Plane(center=(0, 0, 0), direction=(0, 0, 1),
                      i_size=kg.L * 1.2, j_size=kg.B * 2.0)
        self._plotter.add_mesh(wl, color="#aaddff", opacity=0.2,
                                show_edges=False, name="waterline")

    def update_mesh(self, params: dict):
        kg = KayakGenerator(**params)
        for part, actor_attr in [("hull", "_hull_actor"), ("deck", "_deck_actor")]:
            verts, faces = kg.get_mesh_arrays(part)
            pv_mesh = _build_pv_mesh(verts, faces)
            actor = getattr(self, actor_attr)
            actor.mapper.dataset.points = pv_mesh.points
            actor.mapper.dataset.faces  = pv_mesh.faces
            actor.mapper.dataset.compute_normals(inplace=True)
        self._plotter.render()

    def _set_camera(self, cam):
        self._plotter.camera_position = cam
        self._plotter.render()
```

### Step 4 — Wire 3D button into `gui.py`

Add to `KayakGUI._build_button()`:

```python
ax_3d = self.fig.add_axes([0.17, 0.07, 0.11, 0.045])   # adjust x to fit
self.btn_3d = widgets.Button(ax_3d, "3D View", color="0.3", hovercolor="0.4")
self.btn_3d.label.set_color("white")
self.btn_3d.on_clicked(self._on_open_3d)
self._pv_window = None
```

Add method to `KayakGUI`:

```python
def _on_open_3d(self, _event):
    from pyvista_view import PyVistaWindow
    if self._pv_window is None or not self._pv_window.isVisible():
        self._pv_window = PyVistaWindow(self.params)
        self._pv_window.show()
```

Add to `KayakGUI.update_plots()` at the end:

```python
if self._pv_window is not None and self._pv_window.isVisible():
    self._pv_window.update_mesh(self.params)
```

### Step 5 — Test and tune

- Drag all sliders with 3D window open; verify no lag.
- Verify camera angle persists across slider updates.
- Verify window close / re-open cycle works without crash.
- If lag is observed: profile `get_mesh_arrays()` and `_build_pv_mesh()`;
  consider dropping `num_stations` from 150 to 80 for the 3D view only
  (a separate `KayakGenerator` init parameter would allow this without
  affecting STL export resolution).

---

## Estimate

| File | Change | LOC |
|------|--------|-----|
| `generator.py` | Add `get_mesh_arrays()` method | +25 |
| `gui.py` | Add `matplotlib.use("qtagg")`, 3D button, `update_plots` hook | +15 |
| `pyvista_view.py` | New file — `PyVistaWindow` class | +120 |
| **Total** | | **~160 lines** |

Dependencies to add: `pyvista`, `pyvistaqt`, `PyQt6` (all pip-installable).
