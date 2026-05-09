---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

# 3D Rendering Library Research

## Summary Table

| Library | Quality | Interactivity | Integration | macOS arm64 | Install size | Effort |
|---------|---------|--------------|-------------|-------------|--------------|--------|
| matplotlib mplot3d | Poor | Poor | Excellent | Excellent | Zero (installed) | Low |
| PyVista | Excellent | Good | Fair | Good | ~150–200 MB (VTK) | Medium |
| vedo | Excellent | Good | Fair | Good | ~150–200 MB (VTK) | Medium |
| Vispy | Good | Excellent | Good | Fair | ~10 MB | High |
| PyGFX / wgpu | Excellent | Excellent | Good | Good | ~25 MB | High |

---

## Per-Library Findings

### 1. matplotlib mpl_toolkits.mplot3d

**Version / status:** Ships with matplotlib 3.10.x. `Axes3D` + `plot_trisurf`. No additional install needed.

**Rendering quality / shading:** Poor. mplot3d uses a CPU painter's-algorithm approximation, not true OpenGL depth testing. This produces visible Z-fighting artifacts on a closed hull+deck assembly where surfaces overlap at the sheer line. Only flat per-polygon shading is available — no smooth (Phong) shading — so a curved kayak hull will look faceted.

**Interactivity with 23k-triangle mesh on slider drag:** Poor. mplot3d is strictly CPU-rendered and redraws the entire scene on every interaction. Full-redraw latency for 23,000 triangles across two surfaces is 1–3 seconds per frame on a laptop CPU, making slider drag feel completely frozen. A community thread titled "Surface plot interactive chart is very slow" and issue matplotlib#16659 ("Speeding up plot_surface 4–8×") confirm this is a known, hard ceiling.

**Integration with existing matplotlib GUI:** Excellent. `fig.add_subplot(projection='3d')` is a drop-in in any `GridSpec` layout — zero architectural change to `gui.py`.

**macOS arm64 compatibility:** Excellent. Already installed and tested.

**Install footprint:** Zero.

**Implementation effort:** Low (~20 lines to add `plot_trisurf`).

**Verdict:** Ruled out for the 3D panel. CPU rendering ceiling makes interactive updates on this mesh size impossible.

---

### 2. PyVista

**Version / status:** 0.48.1 (released May 7, 2026). Actively maintained. pyvistaqt 0.11.x provides Qt embedding.

**Rendering quality / shading:** Excellent. PyVista wraps VTK's GPU-accelerated OpenGL renderer with proper depth testing, back-face culling, and Phong/PBR shading. `add_mesh(mesh, smooth_shading=True, split_sharp_edges=True)` produces a visually clean, smooth hull surface. Two independent actors (hull, deck) with distinct colors render without any Z-fighting.

**Interactivity with 23k-triangle mesh on slider drag:** Good. VTK renders 23k triangles sub-millisecond on any GPU. The Python-side cost is recomputing ~11,850 vertices in NumPy and assigning `mesh.points = new_array`, then calling `plotter.render()`. Community measurements put this at well under 200ms per event — imperceptible at human interaction speeds. Because the existing GUI uses matplotlib sliders (not VTK sliders), continuous drag callbacks route through Qt signals naturally.

**Integration with existing matplotlib GUI:** Fair — requires a Qt migration. The current `gui.py` runs under `plt.show()` (matplotlib event loop). To embed PyVista alongside it, both must run under Qt: matplotlib switches to `Qt5Agg`/`Qt6Agg` and is embedded as `FigureCanvasQTAgg`; PyVista uses `pyvistaqt.QtInteractor` in the same `QMainWindow`. This is ~80–120 lines of structural refactoring but is well-documented and fully supported.

**macOS arm64 compatibility:** Good. VTK 9.5.2 + PyVista 0.46.4 confirmed working on Apple M3 Pro (December 2025). VTK 9.6.1 provides native arm64 wheels.

**Install footprint:** Large. `pip install pyvista pyvistaqt` pulls VTK (~100–150 MB compressed, ~350–500 MB installed).

**Implementation effort:** Medium. Qt migration (~100 lines) + PyVista panel + slider wiring (~50 lines).

**Known issue:** pyvistaqt hangs with PySide6 ≥6.10 (issue pyvista#8285, opened Feb 2026, unresolved May 2026). Mitigation: pin `PySide6<6.10` or use PyQt5/PyQt6.

---

### 3. vedo

**Version / status:** 2026.6.1 (released February 17, 2026). Built on VTK; Python ≥3.10.

**Rendering quality / shading:** Excellent. Same VTK GPU renderer as PyVista. `mesh.phong()` enables smooth Phong shading. The `Mesh((vertices, faces))` constructor accepts NumPy arrays directly — arguably cleaner syntax than PyVista's `PolyData`.

**Interactivity with 23k-triangle mesh on slider drag:** Good. Identical VTK rendering performance. `add_slider()` with `delayed=False` fires callbacks continuously during drag, which is the correct mode for this use case.

**Integration with existing matplotlib GUI:** Fair — same Qt migration requirement as PyVista. vedo's Qt integration is documented but has fewer community examples than PyVista in a desktop matplotlib+vedo context.

**macOS arm64 compatibility:** Good. vedo is pure Python; depends on VTK which has native arm64 wheels (VTK 9.6.1, April 2026).

**Install footprint:** Large — VTK dominates (same as PyVista).

**Implementation effort:** Medium. Slightly more ergonomic mesh API; similar Qt migration cost.

---

### 4. Vispy

**Version / status:** 0.16.1 (released January 7, 2026). Pre-built macOS arm64 wheels available.

**Rendering quality / shading:** Good. Direct OpenGL via GLSL shaders. `MeshVisual` supports flat and smooth (Phong via `ShadingFilter`) shading. Two surfaces with distinct colors are straightforward as separate `MeshVisual` objects.

**Interactivity with 23k-triangle mesh on slider drag:** Excellent in principle. Community benchmarks show Vispy at 45 FPS where matplotlib stalls at 1 FPS for 5M points. Mesh updates via `mesh.set_data(vertices=..., faces=...)` are incremental GPU buffer updates, faster than VTK pipeline recalculation. However, unresolved issue vispy#2430 reports a drop from 60 FPS to 1–2 FPS with certain visual compositions (cause unknown).

**Integration with existing matplotlib GUI:** Good in theory, requires Qt migration. Vispy provides a `QWidget`-compatible canvas that sits beside `FigureCanvasQTAgg` in a `QHBoxLayout`. Requires explicit `vispy.use('pyqt5')` or similar before any Vispy import, coordinating with matplotlib's Qt binding.

**macOS arm64 compatibility:** Fair — significant strategic risk. OpenGL is deprecated by Apple since macOS Mojave. Apple has not set a removal date, but Vispy has no Metal fallback. Vispy 2.0 (planned, Datoviz/Vulkan backend) is not yet released. Running on a deprecated API path is a liability for a design tool expected to be maintained over years.

**Install footprint:** Small (~10 MB + Qt binding).

**Implementation effort:** High. Lower-level API than VTK-based options; manual scene graph assembly, `MeshData`, `ShadingFilter`, lighting setup. Same Qt migration required.

---

### 5. PyGFX / wgpu

**Version / status:** pygfx 0.16.0 (March 3, 2026); wgpu 0.31.0 with `macosx_11_0_arm64` wheel. **Pre-1.0 — API changes with each minor version until ~July 2026 1.0 target.**

**Rendering quality / shading:** Excellent. WebGPU wraps Metal (macOS), Vulkan (Linux), DirectX 12 (Windows). `MeshPhongMaterial` + `DirectionalLight` produces correct, artifact-free Phong shading. Best rendering ceiling of all options. No OpenGL deprecation risk on macOS — uses Metal natively.

**Interactivity with 23k-triangle mesh on slider drag:** Excellent. WebGPU has lower driver overhead than OpenGL. Topology-constant vertex updates are GPU memcpy operations — near-zero latency. The `canvas.update_mode = "ondemand"` setting redraws only on geometry changes.

**Integration with existing matplotlib GUI:** Good. `WgpuCanvas` is a `QWidget` embedable in any Qt layout. Qt binding auto-detection works. Same Qt migration of `gui.py` required.

**macOS arm64 compatibility:** Good. Metal-native; arm64 wheel confirmed.

**Install footprint:** Moderate (~25–40 MB, no VTK dependency).

**Implementation effort:** High. Pre-1.0 API, manual scene assembly (`Scene`, `PerspectiveCamera`, `Mesh`, `MeshPhongMaterial`, lighting, orbit controller, render loop). Fewest worked examples for this exact use case. Version-pinning is mandatory to avoid breakage.

---

## Recommendation

**Recommended library: PyVista (with pyvistaqt)**

PyVista is the best fit for kayak-gen's 3D preview, for these concrete reasons:

1. **Rendering quality meets the requirement.** VTK's GPU-accelerated Phong shading with `smooth_shading=True` produces a clean kayak hull without faceting.

2. **Interactivity is adequate.** 23k triangles is negligible for VTK's OpenGL renderer. Geometry rebuild (recompute ~11,850 vertices, assign `mesh.points`) is well under 200ms per slider event — imperceptible at human interaction speeds.

3. **macOS arm64 is confirmed working.** VTK 9.6.1 provides native arm64 wheels; tested on M3 Pro December 2025.

4. **API maturity and stability.** PyVista v0.48 is stable, well-documented, widely used. pygfx is pre-1.0 with documented breaking changes per minor version.

5. **Clear implementation path.** Qt migration of `gui.py` is a one-time ~100-line refactoring with well-documented examples from both matplotlib (`FigureCanvasQTAgg`) and PyVista (`QtInteractor`).

**Fallback:** vedo — same VTK backend, cleaner mesh-construction API, same install cost.

---

## Risks and Tradeoffs

### PyVista (recommended)

- **Qt migration required.** ~80–120 lines of structural change to `gui.py`. Well-understood; good documentation.
- **VTK install size.** ~350–500 MB installed. Acceptable on a developer workstation; problematic for a slim distribution.
- **pyvistaqt / PySide6 ≥6.10 hang** (issue pyvista#8285, open May 2026). Mitigation: pin `PySide6<6.10` or use PyQt5/PyQt6.
- **Geometry update is full replace.** Every slider event reassigns `mesh.points` with a freshly computed NumPy array. At 11,850 vertices this is fast, but not incremental.

### Vispy

- **OpenGL deprecation on macOS is an unquantified strategic risk.** Apple has not set a removal date but has not reversed the deprecation either. A design tool expected to be maintained for years should not depend on a deprecated API path.

### PyGFX / wgpu

- **Pre-1.0 API instability.** Every minor upgrade may require code changes. Mandatory version-pinning.
- Highest implementation effort; fewest community examples for this specific use case.

### matplotlib mplot3d

- Ruled out. Cannot meet the interactivity requirement.
