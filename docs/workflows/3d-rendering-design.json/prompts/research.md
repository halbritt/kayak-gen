# Job: Research Python 3D Rendering Options

## Context

The kayak-gen project is a parametric kayak hull generator (generator.py)
with a matplotlib-based parameter GUI (gui.py). The GUI currently shows
2D cross-section, side-profile, and plan-view previews that update live
as the user drags sliders.

The PRD now requires a live interactive 3D rendering of the full hull+deck
assembly. Requirements from the PRD:

- Interactive rotation and zoom of the full hull+deck model
- Hull and deck rendered as visually distinct surfaces with smooth shading
- Updates with no perceptible lag as sliders are dragged on a standard laptop
- Runs as a local desktop application — no browser required
- Minimal new dependencies; must be pip-installable

The mesh produced by KayakGenerator has ~150 stations × 79 points per
cross-section ≈ ~11,850 vertices and ~23,000 triangles per surface (hull
and deck separately). The 3D view must refresh this geometry on every
slider drag event.

## Task

Research and evaluate the following Python 3D rendering libraries:

1. **matplotlib mpl_toolkits.mplot3d** — already installed; Axes3D + plot_trisurf
2. **PyVista** — VTK-based; `pip install pyvista`
3. **vedo** — VTK-based; `pip install vedo`
4. **Vispy** — OpenGL-based; `pip install vispy`
5. **PyGFX / wgpu** — WebGPU-based; `pip install pygfx`

For each option evaluate:
- Rendering quality (smooth shading, surface normals, lighting)
- Interactive frame rate with ~23k-triangle meshes being rebuilt on slider drag
- How it integrates alongside the existing matplotlib figure (same window,
  separate window, embedded Qt widget, etc.)
- macOS arm64 (Apple Silicon) compatibility
- pip install footprint and any native lib dependencies (VTK, Qt, etc.)
- Implementation effort to wire into the existing KayakGenerator + gui.py

## Output

Write a synthesis artifact at:
  docs/workflows/3d-rendering-design.json/RESEARCH.md

Structure it as:

1. Summary table: library × criteria matrix
2. Per-library section with findings and evidence
3. Recommendation: one library choice with clear rationale
4. Risk/tradeoffs of the recommendation

Use the following front matter (required by striatum):

```
---
kind: synthesis
logical_name: research
---
```
