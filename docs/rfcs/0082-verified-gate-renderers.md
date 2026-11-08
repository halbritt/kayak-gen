# RFC 0082: Verified rendering for full and pre-push gates

Status: landed verified full/fast renderer admission
Date: 2026-11-08
Context: KAYGEN-19 / retrospective R4; D068.

## Problem

Separate worktrees, SQLite indexes and browser ports did not isolate NVIDIA
rendering resources. Concurrent native contexts exhausted GPU memory and one
suite crashed. Later Mesa/llvmpipe gates succeeded with actual capabilities and
no NVIDIA OpenGL mappings, but neither maintained gate path enforced that
distinction. The fast/pre-push subset also creates real VTK scenes.

## Goals and non-goals

Both existing gate entry points must establish their actual renderer and apply
its resource policy. Keep every full-suite check, the exact fast manifest,
four-default/zero-OpenFOAM skip policy, external interpreter support and
source-bound receipts. Renderer failure cannot be replaced with a successful
stub or a partial suite. GPU workload interruption, VRAM reservation, unlimited
software concurrency, cross-platform support and future driver compatibility
are not established by this change. Scientific claims remain unchanged.

## Proposal and D068

`scripts/full-gate.sh` and `scripts/fast-gate.sh` call dedicated maintained Python
entry points. `gate.py` owns their two fixed command plans and receipts;
`renderer.py` owns context evidence and the shared hardware lock. Source/process
helpers in `gate.py` remain importable without importing VTK or the renderer
module. There is no arbitrary-command or full-entry-point subset flag.

Select `--renderer software|hardware`, or `KAYAKGEN_GATE_RENDERER`; software is
the default. The software profile fixes the installed Mesa EGL vendor file,
`LIBGL_ALWAYS_SOFTWARE=1` and `VTK_DEFAULT_OPENGL_WINDOW=vtkEGLRenderWindow` in
both the disposable probe and check children. A real `Render()` supplies window
class, VTK version and OpenGL capabilities; `/proc/self/maps` supplies loaded
GL-library paths. Software admission requires Mesa llvmpipe/softpipe and no
NVIDIA OpenGL mapping. Declarations alone never establish admission. Unexpected
hardware or contradictory observations refuse before any test/lint command.

The hardware profile preserves the caller's renderer settings. It acquires
`~/.cache/kayakgen-release-gate.lock` before probing and holds it through every
check command. Supported hardware currently means observed NVIDIA capabilities
with corresponding loaded NVIDIA OpenGL libraries; software fallback refuses.
The lock uses the existing stable inode, releases on failure/interruption and
does not stop unrelated workloads. It only coordinates participating processes;
other GPU users and VRAM availability remain outside that advisory lease.

Verified software does not request the hardware lock. This permits concurrent
software gates and software test fixtures inside a hardware-gated suite without
recursive lock acquisition. Hardware gates should not recursively request the
same hardware lock. The current software profile depends on Linux EGL vendor
layout, `/proc` and the installed Mesa library. Unknown or changed profiles fail
explicitly instead of receiving an inferred compatibility claim.

### Actual probe and command outcomes

The probe runs in a child interpreter with a 30-second deadline. A nonzero or
native signal exit, timeout, invalid observation, missing Mesa support or
profile mismatch refuses the gate. `subprocess.run` reaps that probe on caught
exceptions; the existing gate signal handling still terminates only its owned
test command group. Uncatchable termination may leave a running receipt, which
remains incomplete. A successful probe establishes no complete-suite result.

The full plan stays complete pytest plus skip pin, then mandatory Ruff. The fast
plan stays Ruff, then its existing pytest subset. Its exact 11 ignored files
and two deselected node IDs move from shell text into `FAST_PYTEST_ARGS`.
Manifest tests still verify their existence/collection, while real caller
controls prove the fast skip pin instead of inspecting obsolete shell strings.
Both child environments clear inherited `PYTEST_ADDOPTS`.

### Receipt extension

`kayakgen-gate-receipt/1` remains source-bound. The dedicated entry points write
`gate: "full"` or `gate: "fast"`; fast evidence cannot satisfy a full requirement.
Renderer evidence now includes:

- `requested_mode`, `declared` and `effective` renderer settings.
- `actual`: observed window/VTK/OpenGL identity, capabilities, mapped GL libraries
  and the derived NVIDIA-OpenGL-presence flag.
- `probe`: argv, status, exit, duration and stderr.
- `coordination`: independent software or exclusive hardware policy, lock path
  when applicable and observed lease state.

Older receipts with `renderer.actual.status: "unobserved"` remain historical
evidence of that absence. They are not backfilled or upgraded to a profile.
Consumers still declare their own required source, gate kind and actual-renderer
predicates. Receipts are local evidence, not authenticated acceptance decisions.

## Acceptance criteria and verification

Real temporary Git repositories exercise both shell callers, actual software
observations and fixed child environments, unchanged source, fast exclusions and
the skip pin. Two software callers must reach a barrier inside their actual
pytest commands concurrently. Controlled actual Mesa/hardware mismatches and a
real probe SIGSEGV leave both plans unstarted and failed. Real-process lock
controls prove exclusion and release on caller failure. A bounded actual NVIDIA
probe checks capabilities and host-lock exclusion separately; it is not a
hardware full-suite pass. Frozen complete pytest followed by Ruff remains the
required source gate.

## Alternatives and open questions

Always serializing both suites retains unnecessary contention for proven Mesa
runs. Trusting software environment flags alone repeats the evidence gap.
Removing rendering tests weakens the release contract. Separate shell policy
wrappers would duplicate source, command and failure handling; the shared fixed
runner preserves one owner for those decisions.

Other graphics stacks, hardware reservation and stronger renderer observation
throughout every native call need separate evidence before support expands.

## Implementation path and domain modeling

One coherent operational landing: actual-probe tracer, caller integration,
failure/concurrency controls, documentation, then frozen full pytest and Ruff.
A **gate renderer profile** is operational admission and resource ownership; it
does not add a hull-domain aggregate or a scientific readiness/claim state.
