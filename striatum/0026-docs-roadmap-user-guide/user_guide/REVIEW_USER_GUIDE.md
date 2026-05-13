author: operator [self-declared: operator-user-guide-review]

# User guide review - workflow 0026

Verdict intent: accept_with_findings

## Findings

### U-001 - The guide should start with the shortest useful path

A new user needs a concrete path from clone/install to generated hull files and
evaluation JSON before seeing RFC context.

Required action: include quick start steps for editable install, creating a
default hull JSON, generating STL, and evaluating hydrostatics/resistance.

### U-002 - CLI command coverage should match current commands

The current CLI exposes `init`, `generate`, `evaluate`, `mesh-check`,
`mesh-package`, `stability`, `sweep`, `compare`, `view`, `serve`, and `cfd`
subcommands.

Required action: document these commands at task level with examples and
outputs/caveats. Do not document commands that do not exist.

### U-003 - Web and desktop docs need dependency caveats

Desktop and web entry points are useful but optional extras. Users need to know
when to install `.[desktop]`, `.[web]`, or browser tooling.

Required action: include desktop/web sections with extras and headless/server
caveats. Avoid claiming full desktop/web parity or hosted demo availability.

### U-004 - Mesh/CFD guide must describe readiness levels honestly

Users can package open wetted-surface meshes and prepare local CFD jobs, but
current generated packages are not watertight `cfd_ready` solids and no real
solver is integrated.

Required action: include examples for `mesh-package` and `cfd prepare/status/run`,
explain `cfd_surface_candidate` versus `cfd_ready`, and state that
unavailable/mock profiles are for workflow plumbing.

### U-005 - Troubleshooting should cover expected current limitations

Many current "failures" are expected limitations: missing GUI/web extras, local
CFD profile unavailable, watertight profile rejection, no high-angle GZ, and no
calibration fixture.

Required action: add a concise troubleshooting/limitations section with these
known states and next-step pointers.
