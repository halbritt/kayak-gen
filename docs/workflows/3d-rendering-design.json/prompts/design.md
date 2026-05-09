# Job: Design the 3D Rendering Implementation

## Context

Read the research findings at:
  docs/workflows/3d-rendering-design.json/RESEARCH.md

Also read:
  generator.py   — KayakGenerator class; _get_slice_points(), generate_stl()
  gui.py         — KayakGUI class; sliders, 2D plots, update_plots()
  docs/PRD.md    — product requirements

## Task

Produce a concrete technical design for adding a live interactive 3D
rendering panel to the kayak generator GUI, using the library recommended
in RESEARCH.md.

The design must answer these questions precisely:

### 1. Library choice
- Name, version pin, pip install command
- Any system-level dependencies (Qt, VTK, etc.) and how to install them

### 2. Integration architecture
- Does the 3D view live in the same matplotlib figure, a separate window,
  or an embedded widget? Justify the choice.
- How does the user switch between or arrange the 2D + 3D views?

### 3. Geometry pipeline
- What data does the 3D renderer need (vertices, faces, normals, colors)?
- Where in the code does this data get computed — in KayakGenerator, in
  KayakGUI, or in a new helper?
- Specify any changes needed to generator.py to expose mesh data more
  efficiently (e.g., returning vertex/face arrays instead of writing STL).

### 4. Update strategy
- How does the 3D view refresh when a slider changes?
- Is geometry rebuilt from scratch or updated incrementally?
- Is there throttling/debouncing? If so, what threshold (ms)?

### 5. Camera and user controls
- What rotation/zoom/pan controls does the user get?
- Any preset views (top, front, iso)?

### 6. Visual treatment
- Hull color/material vs deck color/material
- Lighting model (ambient, diffuse, specular?)
- Waterline indicator (z=0 plane or line)?

### 7. Implementation plan
- Ordered list of implementation steps
- Estimate of lines of code added/changed
- Any new files to create

## Output

Write a handoff artifact at:
  docs/workflows/3d-rendering-design.json/DESIGN.md

Use the following front matter (required by striatum):

```
---
kind: handoff
logical_name: design
---
```

The document must be complete enough that an implementer can start
writing code without asking follow-up questions.
