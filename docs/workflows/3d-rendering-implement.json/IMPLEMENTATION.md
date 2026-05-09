# 3D Rendering Implementation

## Files

- Modified `generator.py` to add `KayakGenerator.get_mesh_arrays(part_type)`, returning NumPy vertex and triangle-index arrays using the same triangulation logic as `generate_stl()`.
- Modified `gui.py` to use the Qt matplotlib backend, add the `3D View` button, open the PyVista window, and update the 3D mesh while sliders change.
- Added `pyvista_view.py` with the `PyVistaWindow` Qt window, PyVista mesh construction, hull/deck actors, waterline plane, and camera preset buttons.

## Installed Packages

Installed with:

```bash
python -m pip install "pyvista>=0.48,<0.49" "pyvistaqt>=0.11,<0.12" "PyQt6>=6.6,<6.10"
```

Resolved versions:

- `pyvista==0.48.1`
- `pyvistaqt==0.11.4`
- `PyQt6==6.9.1`
- `vtk==9.6.1`

The active virtualenv was also missing the existing project dependency that provides `from stl import mesh`, so `numpy-stl==3.2.0` was installed to keep `python gui.py` runnable.

## Verification

Run:

```bash
python gui.py
```

Expected behavior:

- The matplotlib kayak generator window opens with the existing sliders and 2D plots.
- Clicking `3D View` opens a second `Kayak 3D View` window.
- The 3D window shows the hull in blue, deck in green, and a translucent waterline plane.
- Dragging sliders updates the 2D plots and the open 3D window.
- The `Top`, `Side`, `Front`, and `Iso` buttons change the 3D camera view.

Additional checks run during implementation:

```bash
python -m py_compile generator.py gui.py pyvista_view.py
```

`KayakGenerator().get_mesh_arrays("hull")` and `"deck"` each returned `(11850, 3)` vertices and `(23244, 3)` faces.
