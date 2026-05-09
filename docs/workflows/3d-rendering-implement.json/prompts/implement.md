# Task: Implement 3D Rendering Panel

You are implementing a live interactive 3D rendering panel for the kayak
generator GUI. The full technical design is in DESIGN.md (provided as a
context file). Read it carefully before writing any code.

## What to implement

### 1. Install dependencies

```bash
pip install "pyvista>=0.48,<0.49" "pyvistaqt>=0.11,<0.12" "PyQt6>=6.6,<6.10"
```

### 2. Add `get_mesh_arrays()` to `generator.py`

Inside the `KayakGenerator` class, add a new public method that returns
`(vertices, faces)` as NumPy arrays instead of writing an STL file.
The triangulation logic is identical to `generate_stl()`. Do NOT change
any existing methods.

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

### 3. Modify `gui.py`

Two changes only — do not touch anything else:

**a)** At the very top of the file, before any other import, add:
```python
import matplotlib
matplotlib.use("qtagg")
```

**b)** In `_build_button()`, add a "3D View" button after the existing
Reset button:
```python
ax_3d = self.fig.add_axes([0.04, 0.13, 0.24, 0.045])
self.btn_3d = widgets.Button(ax_3d, "3D View", color="0.25", hovercolor="0.35")
self.btn_3d.label.set_color("white")
self.btn_3d.on_clicked(self._on_open_3d)
self._pv_window = None
```

Add these two methods to `KayakGUI`:
```python
def _on_open_3d(self, _event):
    from pyvista_view import PyVistaWindow
    if self._pv_window is None or not self._pv_window.isVisible():
        self._pv_window = PyVistaWindow(self.params)
        self._pv_window.show()

# At the end of update_plots(), add:
# if self._pv_window is not None and self._pv_window.isVisible():
#     self._pv_window.update_mesh(self.params)
```

Add the 3D update call at the end of `update_plots()`:
```python
        if self._pv_window is not None and self._pv_window.isVisible():
            self._pv_window.update_mesh(self.params)
```

### 4. Create `pyvista_view.py`

Create this file from scratch:

```python
import numpy as np
import pyvista as pv
from pyvistaqt import QtInteractor
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton
)
from generator import KayakGenerator


def _build_pv_mesh(vertices: np.ndarray, faces: np.ndarray) -> pv.PolyData:
    pv_faces = np.hstack([np.full((len(faces), 1), 3), faces]).ravel()
    mesh = pv.PolyData(vertices, pv_faces)
    mesh.compute_normals(inplace=True)
    return mesh


class PyVistaWindow(QMainWindow):
    PRESETS = [
        ("Top",   [(0, 0, 20),  (0, 0, 0), (0, 1, 0)]),
        ("Side",  [(20, 0, 2),  (0, 0, 0), (0, 0, 1)]),
        ("Front", [(0, 20, 2),  (0, 0, 0), (0, 0, 1)]),
        ("Iso",   [(10, 10, 6), (0, 0, 0), (0, 0, 1)]),
    ]

    def __init__(self, params: dict):
        super().__init__()
        self.setWindowTitle("Kayak 3D View")
        self.resize(900, 650)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        toolbar = QHBoxLayout()
        layout.addLayout(toolbar)
        for label, cam in self.PRESETS:
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
        wl = pv.Plane(
            center=(0, 0, 0), direction=(0, 0, 1),
            i_size=kg.L * 1.2, j_size=kg.B * 2.0,
        )
        self._plotter.add_mesh(
            wl, color="#aaddff", opacity=0.2, show_edges=False, name="waterline"
        )

    def update_mesh(self, params: dict):
        kg = KayakGenerator(**params)
        for part, attr in [("hull", "_hull_actor"), ("deck", "_deck_actor")]:
            verts, faces = kg.get_mesh_arrays(part)
            pv_mesh = _build_pv_mesh(verts, faces)
            actor = getattr(self, attr)
            actor.mapper.dataset.points = pv_mesh.points
            actor.mapper.dataset.faces = pv_mesh.faces
            actor.mapper.dataset.compute_normals(inplace=True)
        self._plotter.render()

    def _set_camera(self, cam):
        self._plotter.camera_position = cam
        self._plotter.render()
```

### 5. Write `docs/workflows/3d-rendering-implement.json/IMPLEMENTATION.md`

After writing the code above, create this file summarising:
- Which files were created or modified
- The pip packages installed and their versions
- How to verify the implementation works (launch command + what to expect)

## Verification

After implementation, the user should be able to run:

```bash
python gui.py
```

The matplotlib slider window opens. Clicking "3D View" opens a second
window showing the kayak hull (blue) and deck (green) in 3D. Dragging
any slider updates both windows.
