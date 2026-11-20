# RFC 0090 — Local OpenFOAM release provenance

Status: landed per-run OpenFOAM release provenance
Date: 2026-11-20
Context: RFCs 0041, 0045 and 0046, decision D083

## Problem and goals

The v2512-specific profile and release verifier rejected v2606 even when the
operator selected it. The historical probe also used shell variables as
surrogates for build and API output. A CFD run needs to identify the binary
that produced its results.

## Proposal and implementation

Use `openfoam-interfoam-local` to select the installation at run time. Resolve
the explicit bashrc, active environment or newest installed package once, then
source that installation for the probe and commands. Read the OpenCFD release
and build from `interFoam -help`. Use the observed release as the pin for
installed-release verification. A stored v2512-specific profile requires v2512.

The evidence and package commands use the same closed-body station count.
Binding snapshots the five checked mesh files into the package. Dispatch checks
their hashes and uses the package mesh with the job's water properties and
inlet speed. `setFields` initializes the water field before `interFoam` runs.

## Acceptance criteria

The real v2606 mesh and solver produce passing mesh diagnostics and parseable
force samples. Mesh evidence records its release, and the run records its
release and build. Inconsistent release evidence blocks dispatch. Archived
v2512 evidence with a solver-reported version remains readable.

## Domain modeling and scope

The release belongs to the mesh evidence and solver execution audit. The case
template retains its own format identifier. CFD results retain the
`raw_unvalidated` claim state and empty accepted uses. Physical calibration
is a separate measurement task.
