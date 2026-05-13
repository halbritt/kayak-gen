# RFC 0008: Portable Web Frontend (Trame)

Status: partial
Date: 2026-05-09
Context: builds on RFC 0007 (architectural revisit). Touches the
`kayakgen.ui` and `kayakgen.cli` boundaries; does not change
`kayakgen.model` or `kayakgen.eval`.

Status note (workflow 0010, 2026-05-12): partially landed. The Trame shell,
sliders, VTK view, metrics helpers, share-query encoding, REST route
scaffolding, and Docker build path exist. Plot tabs, full browser smoke,
Lighthouse verification, and hosted demo deployment remain follow-up work.

## Problem

The desktop GUI (`PyQt6 + matplotlib + PyVista`) requires a graphical
workstation, a working Qt install, and a `pip install` of the full
dependency tree before anyone can see a hull. That is a high floor
for three things we want:

1. **Sharing a hull.** "Look at this design" today means exporting an
   STL and emailing it, or pushing parameters in a chat message and
   asking the recipient to type them into their copy of the GUI. There
   is no shareable URL.
2. **Trying the tool without installing it.** Anyone evaluating
   whether the project is useful has to clone the repo, build a Qt
   environment, and launch a desktop window. That is the wrong
   onboarding curve for a design tool.
3. **Running on non-desktop targets.** Tablet on a beach, ChromeOS,
   a remote CI / cloud workstation, a phone screenshot for a quick
   sanity check. The Qt GUI cannot reach any of these.

RFC 0007 already proposes a headless `kayakgen` core that does
everything the desktop GUI does without the GUI. That makes a web
frontend a layering problem rather than a rewrite. This RFC fills in
that layer.

## Goals

- Ship a browser-based UI that has visual parity with the desktop GUI:
  the same sliders, the same 3D hull, the same metrics, the same STL
  export.
- Keep the hull aggregate, geometry, and evaluators **untouched** —
  the web frontend imports `kayakgen.model` and `kayakgen.eval` and
  consumes their public APIs.
- One command runs it locally: `kayakgen serve [--port 8080]` opens a
  browser tab and renders the app.
- One Dockerfile deploys it remotely. A user with a URL and no Python
  installed can design a hull.
- Hulls are shareable as URLs: `?hull=<base64-or-id>` reconstitutes
  state. Saving a design is "copy this URL".
- Reserve a clean seam for a job-queued CFD tier so the future
  resistance / RANS RFCs do not block on this one.

## Non-Goals

- Replacing the desktop GUI. It stays. Both consume the same core.
- Building a custom JS frontend (React + three.js). That is a much
  larger rewrite and the web-tier UX bar does not require it. Reserve
  RFC 0009 for it if Trame's UX ceiling is hit.
- Pyodide / fully-static, backend-free deploy. Considered and
  deferred — see Open Questions.
- Multi-user, accounts, persistence beyond URL state, design libraries,
  comments, sharing-with-permissions. Out of scope; later RFCs.
- Realtime collaborative editing.
- Mobile-native apps.

## Proposal

### 1. Framework: Trame

[Trame](https://kitware.github.io/trame/) is the first-party
browser frontend for VTK / PyVista from Kitware. It bridges:

- a Python process (Vue-aware via aiohttp / FastAPI) that owns
  application state and runs the same `kayakgen` evaluators the
  desktop GUI runs;
- a Vuetify-3 single-page UI with sliders, buttons, plots;
- a `VtkRemoteView` / `VtkLocalView` 3D widget that renders the
  exact PyVista mesh used by the desktop `pyvista_view.py`.

Why Trame and not the alternatives:

| Option | Effort | Loses | Wins |
|---|---|---|---|
| **Trame** (chosen) | Small. ~600 LOC port of `gui.py` + `pyvista_view.py`. | Nothing — PyVista mesh, matplotlib plots, Python evaluators all work as-is. | Browser-portable, shareable URLs, Docker-deployable. |
| FastAPI + React + three.js | Large. ~3000 LOC, plus npm toolchain. | PyVista's free 3D rendering. | Fully custom UX, scales to richer design tooling. |
| Pyodide (browser-side Python) | Medium. PyVista will not run; need a separate three.js viewer. | PyVista, server-side CFD. | No backend; static hosting on GitHub Pages. |
| Streamlit / Gradio | Tiny. | 3D control, sliders-as-controls UX, custom layout. | Trivial deploy. |

Trame is the smallest delta from RFC 0007's package layout that
yields a real, portable web app.

### 2. Module placement

Per RFC 0007 §1:

```
kayakgen/
  ui/
    desktop.py      # existing PyQt6 GUI (refactored)
    pv_window.py    # existing PyVista window
    web/
      __init__.py
      app.py        # TrameApp factory; UI layout
      state.py      # state schema; mirrors Hull params
      controllers.py# action handlers (export STL, share URL, …)
      static/       # any custom CSS / icons
```

`kayakgen.ui.web.app:create_app(server=None) -> TrameApp` is the
single entry point. `kayakgen serve` (in `kayakgen.cli.main`) calls
it and runs the server.

### 3. UI layout

Two-column Vuetify layout, matching the desktop GUI's information
density:

```
┌───────────────────────────────────────────────────────────────┐
│  kayakgen                       [Reset] [Share] [Export STL]  │
├──────────────────┬────────────────────────────────────────────┤
│ Class: [select]  │                                            │
│ Length:    ──•── │           VtkRemoteView (3D hull)          │
│ Beam (oa): ──•── │           with camera presets              │
│ Beam (wl): ──•── │                                            │
│ Draft:     ──•── │                                            │
│ ...              │                                            │
│ Cp:        ──•── ├────────────────────────────────────────────┤
│ Bow rake:  ──•── │ Sheer plan / cross-section / metrics tabs  │
│                  │  [matplotlib figure rendered server-side]  │
└──────────────────┴────────────────────────────────────────────┘
```

The sliders bind directly to a `state` dict whose keys mirror
`Hull` field names. `@state.change(...)` hooks call into
`kayakgen.eval.hydrostatics.evaluate(hull)` and update both the 3D
mesh and the matplotlib figures.

The 3D widget defaults to `VtkRemoteView` (server renders, pushes
JPEG frames) for predictability across browsers. A query-string flag
`?render=local` flips to `VtkLocalView` (vtk.js renders client-side
from geometry); useful for low-bandwidth links and for the public
demo.

### 4. URL state and sharing

A hull's design parameters round-trip through the URL:

```
https://kayakgen.example.com/?hull=eyJsZW5ndGgiOjQuNSwiYmVhbSI6MC41NSwgLi4u
```

The `hull` query parameter is the base64-encoded JSON of a
`Hull` (RFC 0007). On load, the server decodes it, validates with
Pydantic, and seeds the state. `[Share]` copies the current URL to
clipboard.

For URLs that would exceed ~2 kB, fall back to a content-addressed
store: POST the hull JSON to `/api/hulls`, receive `{"id": "<hash>"}`,
and produce `?hull=id:<hash>`. The store is a flat directory on disk
for v1; SQLite/Redis are later concerns.

### 5. REST API surface

The Trame app also serves a small JSON API so non-Trame clients
(notebooks, future React frontend, CI scripts) can drive the same
core:

```
POST /api/evaluate       body: Hull JSON      → EvaluationResult JSON
POST /api/stl            body: Hull JSON      → application/sla
POST /api/hulls          body: Hull JSON      → {"id": "<hash>"}
GET  /api/hulls/<id>                          → Hull JSON
```

These endpoints are thin wrappers around the same functions
`kayakgen.cli` calls. No business logic lives in the route handlers.

### 6. Heavy-CFD tier (placeholder)

Hydrostatics + Michell (RFCs 0005, 0006) finish in <100 ms — handle
synchronously in the request. A future RANS / OpenFOAM evaluator
will not. Reserve the seam now:

```
POST /api/jobs                body: {hull, evaluator: "rans"}
GET  /api/jobs/<id>           → {status, result?}
```

Implementation deferred to the CFD RFC; the route stubs return 501.
Naming and contract are fixed here so the frontend can be designed
against them.

### 7. Deployment

- **Local:** `kayakgen serve` launches the server on `127.0.0.1:8080`
  and opens the user's default browser. No login, no auth, no shared
  state — equivalent to running the desktop GUI.
- **Hosted:** a Dockerfile (~20 lines) installs `kayakgen[web]` and
  runs `kayakgen serve --host 0.0.0.0 --port 8080`. Behind any reverse
  proxy. The hull-id store is a mounted volume.
- **Sharing the demo:** a static URL pointing at the hosted instance.
  Anyone with the URL gets the GUI; query-string state lets people
  share specific hulls.

The Docker image is the same artifact for "demo" and "team-internal"
deploys; configuration is environment variables only.

### 8. Tests

- **State round-trip:** `Hull` → URL encode → URL decode → `Hull`,
  bit-equal.
- **REST contract:** for a fixed hull, `/api/evaluate` returns the
  same `EvaluationResult` as `kayakgen evaluate <hull.json>`.
- **3D mesh:** the `VtkRemoteView`'s underlying mesh has the same
  vertex count as the desktop GUI's `pv_window` for the same hull.
- **Smoke test:** Playwright / pytest-playwright launches the app,
  drags the length slider, and asserts that the metrics panel
  changes. One end-to-end test, run on CI.

## Acceptance Criteria

- `kayakgen serve` opens a browser tab showing a hull within 2 s on a
  modern laptop.
- Every slider on the desktop GUI has a corresponding control in the
  web UI; their value ranges are identical.
- The 3D view shows the hull and updates within 200 ms of a slider
  drag.
- `[Share]` produces a URL whose page load reconstructs the exact
  hull bit-for-bit (same `Hull.hash()`).
- `[Export STL]` downloads the same bytes that
  `kayakgen generate <hull.json>` would write for the same parameters.
- A `Dockerfile` at the repo root builds and `docker run -p 8080:8080
  kayakgen` opens a working app.
- Hydrostatics displayed in the web UI match those displayed in the
  desktop GUI to 1e-6 (same evaluator, same hull).
- Lighthouse "Best Practices" score ≥ 90 on the served page (no
  console errors, no mixed-content warnings).

## Open Questions

- **Pyodide / static deploy.** A second frontend that runs the
  evaluators in-browser via Pyodide would let us host a
  no-installation demo on GitHub Pages. Costs: rebuild the 3D viewer
  on three.js or model-viewer (PyVista will not run in WASM); CFD
  must still hit a backend; second UI surface to keep in sync. Lean:
  defer to RFC 0010 unless the demo-on-Pages requirement becomes
  load-bearing.
- **Streamlit / Gradio as a quick first pass.** Tempting for a 50-LOC
  prototype, but the slider-heavy, 3D-centric, plot-rich UX is the
  shape Trame is built for and Streamlit fights. Lean: skip the
  prototype; go straight to Trame.
- **VtkRemoteView vs. VtkLocalView default.** Remote (server renders,
  pushes pixels) is bandwidth-heavy but predictable; local (vtk.js
  renders) is light but has cross-browser quirks. Lean: remote
  default, local opt-in via query param. Revisit after we see real
  user numbers.
- **Auth for the hosted demo.** None for v1 — public URL, public
  evaluator, no persistence beyond ephemeral hull-id store with an
  age-out. Add basic auth or magic-link auth in a later RFC if abuse
  shows up.
- **Single-binary distribution.** PyInstaller / shiv could bundle
  `kayakgen serve` into one executable for users who do not have
  Python. Possibly worth doing; orthogonal to this RFC's web work.
- **Mobile UX.** The two-column layout collapses badly on phones.
  v1 ships a "view-only" responsive mode (parameters render as
  read-only chips, 3D view fills width) and defers full mobile
  editing. Acceptable?
- **Where does the matplotlib output live?** Trame supports both
  inline matplotlib and Vega/Plotly. Lean: matplotlib for v1
  (zero rewrite of the existing sheer-plan / cross-section code),
  migrate to Plotly later if interactivity becomes a need.

## Implementation Path

This RFC depends on RFC 0007's package extraction having landed
(or at least the `kayakgen.model` + `kayakgen.eval` modules
existing). Steps assume that.

1. **Add `kayakgen[web]` extra** in `pyproject.toml`: `trame`,
   `trame-vuetify`, `trame-vtk`, `trame-matplotlib`. (~10 lines.)
2. **`kayakgen/ui/web/state.py`** — declare the state schema, mapped
   to `Hull` fields. (~80 lines.)
3. **`kayakgen/ui/web/app.py`** — Trame layout: sliders, buttons, 3D
   view, plot tabs. (~250 lines.)
4. **`kayakgen/ui/web/controllers.py`** — handlers for slider change,
   reset, share-URL, export STL. Wire to `kayakgen.eval`. (~120 lines.)
5. **REST routes** — mount `/api/evaluate`, `/api/stl`, `/api/hulls`
   on the Trame server's underlying aiohttp app. (~80 lines.)
6. **`kayakgen serve` CLI subcommand** — Typer command, wraps
   `app.create_app().start()`. (~20 lines.)
7. **`Dockerfile`** at repo root, plus `.dockerignore`. (~30 lines.)
8. **Tests** — state round-trip, REST contract, mesh parity,
   one Playwright smoke test. (~150 lines.)
9. **Public demo deploy** — host on Fly.io / Railway / Render / a
   small VPS. (Operational task; out of code scope.)

Total net code ≈ 750 lines plus deps.

## Domain Modeling

The web frontend introduces no new domain concepts — it is a second
**presentation context** in `DDD.md` terms, alongside the desktop GUI.
Both consume the same `Hull` aggregate and the same `EvaluationResult`
read model from RFC 0007.

The REST API is an **anti-corruption boundary** between the public
HTTP surface and the internal Python types. Pydantic does double duty
here: the same models that validate `Hull` JSON on disk validate
request bodies coming over HTTP.

The job-queue stub for heavy CFD reserves a **domain event**:
`EvaluationRequested(hull_hash, evaluator_kind)`. The implementing
RFC will decide whether the queue is in-process, Redis-backed, or
something else. This RFC does not commit to the choice.
