# RFC 0045: Ordinary-Package Solver-Readiness Promotion

Status: landed kayakgen mesh-evidence + mesh-package --bind-evidence (hash-bound; defaults unchanged)
Date: 2026-05-16
Context: successor to RFC 0040 stage 2 (snappyHexMesh evidence harness)
and RFC 0023 (watertight `cfd_ready` fixture handoff). The cowboy
2026-05-16 session landed
`kayakgen/eval/snappy_hex_mesh.py:SnappyHexMeshEvidence` plus the real
executor under `kayakgen/eval/cfd/openfoam_v2512_interfoam/`, both behind
opt-in env knobs. Decisions D003, D011, D012, and D022 are the gating
authority.

## Problem

Today an *ordinary* generated mesh package (produced by
`kayakgen mesh-package` against a `default-open-wetted-surface` or
`watertight-solid` profile) cannot be promoted to `cfd_ready`. The
narrow fixture-backed RFC 0023 path remains the only `cfd_ready` route.

That is conservative-by-design: ordinary packages historically had no
real volume-mesh evidence. After the cowboy 2026-05-16 work that is no
longer true — `snappy_hex_mesh_volume_mesh_diagnostic` can translate a
fully-bound `SnappyHexMeshEvidence` record into a `VolumeMeshDiagnostic`
that the existing readiness gate already accepts.

The remaining gap is the *binding* path. A user who runs
`kayakgen mesh-package` does not get a `SnappyHexMeshEvidence` attached
to the manifest. They have to run a separate, undocumented sequence
(generate closed-body STL → render OpenFOAM case → run snappy → bind
evidence → assemble a watertight manifest) before
`watertight_solid_resistance_v1` readiness can be reported.

This RFC scopes the binding path without changing what `cfd_ready`
means or relaxing any existing claim gate.

## Goals

- Provide an explicit, audited way for a user to attach
  `SnappyHexMeshEvidence` to an ordinary generated mesh package so the
  package can report `cfd_ready` for matching solver profiles.
- Preserve the D003 / D011 / D012 / D022 conservatism: only fully-bound,
  `evidence_recorded` `SnappyHexMeshEvidence` plus a passing checkMesh
  plus v2512 provenance unlocks the promotion; partial evidence yields
  `None` from the translator and the package stays below `cfd_ready`.
- Keep the env-gated execution path for the actual binary invocation.
  The promotion itself is gated on evidence presence, not on env knobs.
- Make the audit trail explicit: which generated body, which closed-body
  hash, which snappy case digest, which polyMesh checksum, which
  checkMesh summary, which provenance probe.
- Continue to refuse open-surface and synthetic bodies as solver input.

## Non-Goals

- No relaxation of `cfd_ready` semantics.
- No new readiness level or new readiness label.
- No promotion of mock or fixture evidence.
- No promotion via `validation_fixture` evidence — that path is RFC
  0042 / D013 territory and addresses a different claim (validation,
  not solver readiness).
- No real OpenFOAM `succeeded` path change. RFC 0041 / D012 / D022
  remain authoritative for that.
- No web UI surfaces for evidence binding. Web stays a viewer.

## Dependencies

- RFC 0023 fixture-handoff readiness (`cfd_ready` shape).
- RFC 0040 generated-body matrix hardening + snappyHexMesh evidence
  harness contract.
- `kayakgen/eval/snappy_hex_mesh.py:snappy_hex_mesh_volume_mesh_diagnostic`
  (translator from evidence to diagnostic).
- `kayakgen/eval/cfd/openfoam_v2512_interfoam/runner.py:run_meshing_stage`
  (real binary execution producing the polyMesh).
- Decisions D003, D011, D012, D022.

## Proposal

### Surface

A new CLI subcommand `kayakgen mesh-evidence` runs the meshing stage
against a closed-body STL and emits a serialized `SnappyHexMeshEvidence`
record:

```bash
kayakgen mesh-evidence hull.json --out runs/mesh-evidence/touring
```

The runner reuses
`kayakgen.eval.cfd.openfoam_v2512_interfoam.runner.run_meshing_stage`.
Without the OpenFOAM env knobs set, the command refuses to run and
prints the env-knob requirements. With the env knobs set, it produces
`SnappyHexMeshEvidence` JSON, a copy of the polyMesh artifacts, and a
provenance manifest.

A new `kayakgen mesh-package ... --bind-evidence <path>` flag attaches
a previously-produced evidence record to a newly-rendered watertight
mesh package. The mesh-package builder calls
`snappy_hex_mesh_volume_mesh_diagnostic` and writes the resulting
`VolumeMeshDiagnostic` into the package manifest. Without
`--bind-evidence`, behavior is byte-identical to today (default
`open-wetted-surface` profile, no `cfd_ready`).

### Promotion gate

Promotion happens entirely through `snappy_hex_mesh_volume_mesh_diagnostic`,
which is conservative by construction:

- Returns `None` unless `dispatch_state == "evidence_recorded"`,
  `check_mesh.passed`, all required dictionary hashes are present,
  v2512 provenance is accepted, and the body identity matches the input
  STL.
- When non-`None`, the resulting `VolumeMeshDiagnostic` carries the
  body-ref hash, polyMesh artifact checksums, patch metadata, and the
  provenance probe; the existing watertight readiness gate then admits
  `cfd_ready` if and only if the manifest, profile, and diagnostic
  match.

This is the same chain RFC 0023 already uses for the
fixture-backed path. The only delta is that ordinary packages can now
flow through it.

### Hash bindings

Three hashes must all agree at evidence-attach time:

- `closed_body.body_ref_hash` (output of
  `generated_hull_plus_deck_closed_body()`)
- `SnappyHexMeshEvidence.body_ref_hash` (written during snappy execution)
- The `polyMesh` artifact checksums computed at handoff

Mismatch at any join refuses promotion with a structured rejection code:

- `closed_body_hash_mismatch`
- `snappy_evidence_body_mismatch`
- `polymesh_artifact_drift`

### What lands and what does not

Lands:
- `kayakgen mesh-evidence` CLI subcommand.
- `kayakgen mesh-package --bind-evidence` flag.
- Hash-binding validation + structured rejection codes.
- Tests:
  - happy path: generate body → run snappy → bind evidence → package
    reports `cfd_ready` against `watertight_solid_resistance_v1`.
  - mismatch tests for each of the three rejection codes.
  - default `kayakgen mesh-package` invocation unchanged.

Does not land:
- No new readiness level or label.
- No automatic snappy execution from `kayakgen mesh-package`. The user
  must explicitly run `kayakgen mesh-evidence` first.
- No web UI for evidence binding.
- No relaxation of the env-gated OpenFOAM-v2512 binary requirement; the
  binding step still needs the toolchain. Without it,
  `kayakgen mesh-evidence` refuses to run.

## Acceptance Criteria

- Default `kayakgen mesh-package` JSON output is byte-equal to today
  when `--bind-evidence` is absent.
- `kayakgen mesh-evidence` against a default `Hull()` produces a
  `SnappyHexMeshEvidence` with `dispatch_state == "evidence_recorded"`
  under `KAYAKGEN_OPENFOAM_LOCAL_RUN=1`; refuses without it.
- A subsequent `kayakgen mesh-package hull.json --solver-profile
  watertight-solid --bind-evidence <path>` produces a package with
  `cfd_ready=True` and the bound `VolumeMeshDiagnostic` in the manifest.
- A mismatch between the evidence body hash and the rendered package's
  body hash refuses promotion with `closed_body_hash_mismatch`.
- A tampered polyMesh checksum refuses promotion with
  `polymesh_artifact_drift`.
- `claim_state` everywhere remains as before; no new state is added.

## Open Questions

- Should the bound evidence and the package manifest co-locate on disk
  (mesh-package directory contains a copy of the evidence) or stay
  separate (manifest references an absolute path)?
- Should the evidence record store a copy of the rendered case
  dictionaries (for full reproducibility) or just their hashes?
- Should we surface a `kayakgen mesh-evidence --resume` to skip
  re-execution if a matching cache exists?

## Implementation Path

1. Add the `kayakgen mesh-evidence` CLI subcommand wrapping
   `kayakgen.eval.cfd.openfoam_v2512_interfoam.runner.run_meshing_stage`
   plus the existing evidence builder.
2. Wire `kayakgen mesh-package --bind-evidence` into the manifest
   writer; bind via `snappy_hex_mesh_volume_mesh_diagnostic`.
3. Add hash-binding validation with structured rejection codes.
4. Land unit tests for the happy and mismatch paths.
5. Update `docs/USER_GUIDE.md` with the new subcommand and flag.

## Domain Modeling

Boundary clarification. This RFC does not add a new aggregate root or
value object. It plumbs an existing aggregate (mesh package) through an
existing service (`snappy_hex_mesh_volume_mesh_diagnostic`) and exposes
that connection in the CLI. The promotion semantics, claim states, and
readiness gates are unchanged.

Cite `DDD.md § "Adding to the model"`: this is a *use-case* wiring
existing aggregates, not a structural change.
