---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Traceability review - workflow 0034 watertight volume mesh handoff

Scope: map RFC 0010, RFC 0015, RFC 0016, and RFC 0023 acceptance requirements
to current `kayakgen/eval/closed_volume.py`, `kayakgen/eval/mesh_package.py`,
`kayakgen/eval/cfd/jobs.py`, `kayakgen/cli/main.py`, and the corresponding
tests. RFC 0023 is in the "proposed" state; no production code has been
written for it yet, so this review establishes a pre-implementation baseline.

## Verdict

`accept_with_findings`. No current code path promotes any body to
`cfd_ready` or otherwise trusts a manifest readiness string without an
evidence gate. The findings below describe the gaps the implementer must
close before RFC 0023 can land, and the structural risks the implementation
must avoid.

## RFC traceability matrix

### RFC 0010 - CFD-ready mesh contract (landed, package profile)

| Requirement | Where | Status |
| --- | --- | --- |
| `MeshDiagnostics`, `MeshReadiness`, `MeshSolverProfile`, readiness levels | `kayakgen/eval/mesh_diagnostics.py`, `mesh_package.py` | Landed |
| `mesh-check` CLI | `kayakgen/cli/main.py` `mesh_check` | Landed |
| `mesh-package` CLI writes manifest, hull JSON, quality reports, STL | `mesh_package.write_mesh_package`, `cli/main.py` `mesh_package` | Landed |
| Default hull is never falsely labeled `cfd_ready` while boundaries remain | `mesh_package._package_readiness` (open profile caps at `cfd_surface_candidate`; watertight profile caps at `stl_surface`) | Landed; tested in `tests/test_mesh_package.py` |
| Named `watertight_solid_resistance_v1` profile boundary | `mesh_package.watertight_solid_profile` | Landed for RFC 0024 boundary |

RFC 0010's open question "what geometry contract produces a closed combined
hull/deck solid?" is being answered piecewise: RFC 0016 added the
generated-body diagnostic; RFC 0023 is the next step to turn that into a
solver handoff.

### RFC 0015 - CFD solver dispatch and jobs (partial local-dispatch landed)

| Requirement | Where | Status |
| --- | --- | --- |
| Serializable `CfdJobSpec`, `CfdRunRecord`, `SolverProfile` | `kayakgen/eval/cfd/jobs.py` | Landed |
| Local-filesystem queue with per-job directory | `prepare_local_job`, `run_local_job` | Landed |
| `cfd prepare` refuses missing mesh packages and readiness-below-profile | `_validate_mesh_package` | Landed; tested |
| Unavailable adapter records `status=unavailable` | `UnavailableSolverAdapter` | Landed |
| Mock failed-command produces `status=failed` with `error_kind=command_failed` | `MockFailingLocalCommandAdapter` | Landed |
| Raw/unvalidated semantics on all records | `RawUnvalidatedClaimFields`, `result_semantics="raw_unvalidated"` | Landed |
| CLI `cfd prepare/status/run/profiles` | `cli/main.py` | Landed |
| Real OpenFOAM/SU2/hosted execution; watertight solid handoff | not implemented | Deferred per RFC 0015 §"Deferred" |

### RFC 0016 - Closed-volume geometry (safe slice + generated body landed)

| Requirement | Where | Status |
| --- | --- | --- |
| Serializable `ClosedVolumeBody` with explicit-synthetic body type | `closed_volume.ClosedVolumeBody`, `explicit_synthetic_body` | Landed |
| Closure policy records cap/deck-join/waterline/normals/tolerances | `ClosedVolumePolicy`, `ClosedVolumeTolerances` | Landed |
| `closed_volume` readiness requires zero raw and welded boundary/nonmanifold edges, finite geometry, positive signed volume | `_readiness_reasons`, `_diagnose_arrays` | Landed |
| RFC 0021 self-intersection diagnostic check (required for the generated-body profile) | `_diagnose_self_intersections`, `_policy_requires_self_intersection`, RFC 0021 profile | Landed |
| Generated hull+deck builder with bow/stern endpoint caps, sheerline strip, signed-volume reorientation | `generated_hull_plus_deck_body`, `_generated_hull_plus_deck_mesh`, `_add_generated_endpoint_closures` | Landed |
| `cfd_ready` never claimed for any closed-volume diagnostic | `ClosedVolumeDiagnostics.cfd_ready: Literal[False]` and `dispatch_evidence_satisfies_profile` returning `False` unconditionally | Landed |
| Dispatch rejects forged watertight manifests | `_solver_profile_requires_watertight_evidence` + `_watertight_dispatch_evidence` + `dispatch_evidence_satisfies_profile` | Landed; covered by four forged-readiness tests in `tests/test_cfd_jobs.py` |

### RFC 0023 - Watertight volume mesh and `cfd_ready` handoff (proposed; no code)

| Requirement | Where | Status |
| --- | --- | --- |
| Volume-mesh artifact generated from the exact generated body | not present | Missing |
| Volume-mesh diagnostic data model (mesher name/version/digest, output refs/checksums, cell/boundary metrics, invalid/inverted/zero-volume cell counts, quality summaries, body-surface match flag, readiness result) | not present | Missing |
| Manifest extensions: `body_ref`, `closed_volume_diagnostic`, `self_intersection_diagnostic`, `volume_mesh_artifacts`, `volume_mesh_diagnostic`, `evidence_hashes`, `readiness_authority` | `MeshPackageManifest` does not declare any of these | Missing |
| Package writer derives `cfd_ready` for `watertight_solid_resistance_v1` only from in-memory or verified-referenced diagnostics, never from a caller-supplied readiness string | `_package_readiness` derives readiness from in-memory `MeshDiagnostics` only; the watertight branch unconditionally caps at `stl_surface` because no closed body or volume-mesh diagnostic is plumbed through | Pre-condition holds, full requirement missing |
| Dispatch rejection of forged/stale/cross-body/synthetic evidence and missing/malformed/below-threshold volume-mesh evidence | Forged hand-edited `cfd_ready` rejected today; cross-body/stale-hash and synthetic-vs-generated rejection cases for the *accepted* watertight path are not exercised because no acceptance path exists | Partial: rejection side covered, no accept path yet |
| CLI/JSON output that explains why a package is below `cfd_ready` (Step 5) | `cli/main.py` `mesh-package` prints only `({readiness.level})`; `cfd prepare` prints status and a generic raw warning | Missing |
| Tests: success fixture, missing-volume-mesh, self-intersection blocker, stale hashes, synthetic-evidence rejection | Forged hand-edit + synthetic + generated-body rejection tests exist; passing-handoff and stale-hash tests do not | Partial |

## Findings, ordered by severity

### F1 (high, structural) - `dispatch_evidence_satisfies_profile` is an unconditional rejection stub

`kayakgen/eval/closed_volume.py:453-471` validates evidence parsing and then
always returns `False`, even for an RFC 0021/0022 closed-volume diagnostic
that would otherwise satisfy a future watertight handoff. This is the only
admission gate `_watertight_dispatch_evidence` (`cfd/jobs.py:791-823`) calls,
so today *no* dispatch can be accepted under the watertight readiness branch.

Implication for RFC 0023: the implementer must extend this validator into a
real evidence accept path that (a) verifies `body_ref` and
`source_hull_hash` against the manifest, (b) verifies that diagnostics were
produced under the same profile/tolerances as the volume mesher, and (c)
verifies that a passing `volume_mesh_diagnostic` exists with thresholds
above profile minimums. The accept-side change must not remove any of the
current reject-side guarantees - in particular the function must continue
to reject diagnostics whose `cfd_ready` field is `False` and reject
synthetic profiles for the generated handoff.

### F2 (high) - Manifest evidence is currently discovered by substring heuristic, not typed fields

`cfd/jobs.py:826-846` collects diagnostic refs by walking the serialized
manifest and picking up any string value whose ancestor key path contains
"diagnostic". This works defensively today because `quality_reports`
already get included unconditionally, but it is the wrong shape for the
RFC 0023 evidence index. The manifest must add explicit, typed fields
(`closed_volume_diagnostic`, `self_intersection_diagnostic`,
`volume_mesh_diagnostic`, `volume_mesh_artifacts`, `evidence_hashes`,
`readiness_authority`) and the dispatch validator must consume those
explicit fields rather than a heuristic.

If the heuristic is left in place after RFC 0023 lands, a malicious or
careless manifest could add a key named e.g. `diagnostics_note` whose
string value is parseable as `ClosedVolumeDiagnostics`, slipping into the
evidence walk under whatever accept rules F1 defines.

### F3 (high) - No checksum/hash binding between manifest, body, and diagnostic artifacts

`MeshPackageManifest` (`mesh_package.py:35-52`) records only `hull_hash`
and bare filenames for hull JSON, quality reports, and surfaces. Quality
reports are deserialized by `_watertight_dispatch_evidence` but never
checked against a checksum recorded in the manifest. RFC 0023 explicitly
requires `evidence_hashes` so that diagnostic JSON cannot be swapped out
post-hoc, and so that the body identity used by the volume mesher matches
the body identity used by the closed-volume diagnostic. Implementer must
add a content-hash field for every referenced artifact and verify it at
dispatch.

Note that today this is partially mitigated because
`dispatch_evidence_satisfies_profile` returns `False` regardless of
content; once F1 introduces an accept path, F3 becomes load-bearing.

### F4 (medium) - The dispatch readiness comparison still reads from the manifest

`cfd/jobs.py:743-750` compares `manifest.readiness.level` against
`solver_profile.required_mesh_readiness`. A forged `cfd_ready` readiness
string is currently neutralized because
`_solver_profile_requires_watertight_evidence` (`cfd/jobs.py:780-788`)
triggers the watertight evidence gate whenever any of three conditions
hold, including `manifest.readiness.level == "cfd_ready"` or
`requires_watertight=True` on the *manifest's* solver profile.

This works today because the only path that satisfies the evidence gate is
"never". RFC 0023 implementers must keep this behavior coherent after F1:
the readiness comparison must remain a necessary but not sufficient
condition, and the watertight branch must keep firing on
`required_mesh_readiness == "cfd_ready"` and on the
`watertight_solid_resistance_v1` profile name. Do not relax
`_solver_profile_requires_watertight_evidence` while widening the accept
path in `dispatch_evidence_satisfies_profile`.

### F5 (medium) - Package writer has no path to derive `cfd_ready` from evidence

`_package_readiness` (`mesh_package.py:127-171`) only looks at
`MeshDiagnostics` per part. The watertight branch hard-codes
`stl_surface` with two static reasons ("watertight solid profile requires
a closed combined hull/deck volume", "current package writer emits separate
open surfaces"). RFC 0023 requires the writer to accept a closed-volume
diagnostic and a volume-mesh diagnostic as inputs (RFC 0023 §"Manifest and
Readiness Changes" - "the package writer must derive readiness from
evidence in memory or from verified referenced artifacts"). Implementer
must add a second writer path - or extend `write_mesh_package` -
that accepts the generated body, runs the volume mesher, and folds the
in-memory diagnostics into the readiness decision before serializing the
manifest.

### F6 (medium) - CLI does not explain why a package is below `cfd_ready`

RFC 0023 Implementation Path Step 5 calls for CLI/JSON output that names
the rejected evidence class. Today `mesh-package` prints only `wrote …
(readiness.level)` and `cfd prepare` prints `status: …` plus the global
raw-CFD warning. Reasons collected in `MeshReadiness.reasons` /
`MeshPackageManifest.warnings` exist in the manifest but are never
echoed. This is the surface where forged-readiness rejection should
clearly name the missing/blocking evidence class to the operator.

### F7 (low) - Generated-body diagnostic profile name mismatch with RFC 0023

RFC 0023 talks about `watertight_solid_resistance_v1` as the handoff
profile, while the closed-volume module uses
`generated_hull_plus_deck_closed_body_v1` for the body-level diagnostic
profile and `watertight_solid_resistance_v1` for the mesh-package solver
profile. The mapping is consistent today (mesh profile vs. body
diagnostic profile are two different fields) but the dispatch validator
will need to compare body-diagnostic profile **against** mesh-package
profile **against** solver profile. The implementer should record the
intended mapping in code (e.g. a constant table) rather than scatter
string literals.

### F8 (low) - `dispatch_evidence_satisfies_profile` silently swallows the parsed evidence

The function parses evidence into `ClosedVolumeDiagnostics` but discards
the result before returning. After F1, the implementer should keep the
parsed model and base accept/reject on its typed fields (specifically
`profile_name`, `body_type`, `readiness.level`, `cfd_ready` (must be
`False` for the body-level diagnostic),
`self_intersection_status`, `source_hull_hash`, and the body's policy).
Logging the rejection reason back to the caller would also let F6's CLI
explanation surface specific evidence rejection classes.

## Evidence reviewed

- `docs/rfcs/0010-cfd-ready-mesh-contract.md`
- `docs/rfcs/0015-cfd-solver-dispatch-and-jobs.md`
- `docs/rfcs/0016-closed-volume-geometry.md`
- `docs/rfcs/0023-watertight-volume-mesh-handoff.md`
- `kayakgen/eval/closed_volume.py` (full file)
- `kayakgen/eval/mesh_package.py` (full file)
- `kayakgen/eval/cfd/jobs.py` (full file)
- `kayakgen/cli/main.py` lines 95-200
- `tests/test_cfd_jobs.py` watertight/forged sections (lines 250-470)
- `tests/test_mesh_package.py` watertight assertions (lines 10-114)
- Module list under `kayakgen/eval/` confirming no `volume_mesh.py`

## Read-only commands executed

- `Grep` over `volume_mesh|volume-mesh|VolumeMesh` - no source or test
  hits (only RFC and workflow docs reference it). Confirms RFC 0023 has
  zero implementation code today.
- `Grep` over `cfd_ready|watertight|forged|hand[_-]edit|requires_watertight`
  in `tests/` - confirmed forged-manifest, forged quality-report, RFC 0021
  passing-synthetic, and generated-body rejection cases all exist in
  `tests/test_cfd_jobs.py` lines 269-451.
- `Glob` over `kayakgen/eval/**/*.py` - confirmed no `volume_mesh` module
  alongside `mesh_diagnostics.py`, `mesh_package.py`, `closed_volume.py`,
  and `generated_closed_body.py`.

## Residual risks

- Until F1-F3 are addressed, RFC 0023 cannot land because there is no
  accept path; once they are addressed, the temptation to relax the
  manifest readiness comparison (F4) or the substring heuristic (F2) is
  real and should be explicitly forbidden in the ledger's safe slice.
- The current dispatch validator is conservative-by-default (returns
  `False`); the implementation must preserve that default for any
  manifest field it does not recognize, rather than treating unknown
  evidence as benign.
- `_diagnostic_refs_from_mapping` uses a 4-level recursive walk that may
  also pick up strings inside `solver_profile` once additional diagnostic
  fields are added. The new typed manifest fields should be the *only*
  source of refs once RFC 0023 lands; the heuristic should be removed
  rather than extended.
- `tests/test_cfd_jobs.py` exercises forged hand-edit on a manifest whose
  underlying parts are open surfaces. Once F5 introduces a closed-volume
  package writer path, the test matrix must add: (a) successful watertight
  handoff fixture, (b) missing volume-mesh diagnostic rejection, (c)
  cross-body hash mismatch rejection, (d) stale volume-mesh artifact
  rejection (checksum mismatch), (e) synthetic-body-as-generated-handoff
  rejection. RFC 0023 §"Acceptance Criteria" lists these explicitly.
