---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

## Verdict

`accept_with_findings`. The workflow/RFC scaffold is internally consistent and
has enough context for ledger handoff. The findings below are implementable
RFC 0023 code, test, documentation, and evidence gaps rather than workflow or
RFC corrections.

## Findings

### High: RFC 0023 manifest and evidence shape is absent

RFC 0023 requires volume-mesh evidence with `body_ref`, source hull hash,
generated-body diagnostic hash, deterministic mesher inputs, output artifact
checksums, and readiness reasons (`docs/rfcs/0023-watertight-volume-mesh-handoff.md:69`).
It also limits manifest additions to `body_ref`, diagnostic refs,
`volume_mesh_artifacts`, `volume_mesh_diagnostic`, `evidence_hashes`, and
`readiness_authority`, and says `cfd_ready` must be derived from verified
generated-body, self-intersection, and volume-mesh diagnostics
(`docs/rfcs/0023-watertight-volume-mesh-handoff.md:91`).

The current `MeshPackageManifest` still has `extra="forbid"` and only the
pre-RFC-0023 hull/profile/readiness/path fields
(`kayakgen/eval/mesh_package.py:35`). `write_mesh_package()` writes only
`hull.json`, per-part quality reports, hull/deck STLs, and the legacy manifest
fields (`kayakgen/eval/mesh_package.py:83`). Focused tests assert that old
shape and relative writer output, but do not cover RFC 0023 extension fields or
hashes (`tests/test_mesh_package.py:33`, `tests/test_mesh_package.py:107`).

Impact: a generated closed body plus volume mesh cannot be represented as a
deterministic package, and stale/cross-body evidence cannot be checked through
manifest hashes.

### High: no successful watertight volume-mesh handoff can pass dispatch

RFC 0023 acceptance requires a passing volume-mesh diagnostic to promote only
the matching generated body and matching profile (`docs/rfcs/0023-watertight-volume-mesh-handoff.md:137`).
The current package writer always caps the watertight-solid profile at
`stl_surface` because it still emits separate open surfaces
(`kayakgen/eval/mesh_package.py:156`). Dispatch delegates evidence acceptance
to `closed_volume.dispatch_evidence_satisfies_profile()`
(`kayakgen/eval/cfd/jobs.py:849`), but that function validates the diagnostic
and then always returns `False`, including for `required_mesh_readiness ==
"cfd_ready"` (`kayakgen/eval/closed_volume.py:453`).

The CLI path has no inputs for a generated body, self-intersection diagnostic,
or volume-mesh diagnostic; `kayakgen mesh-package` accepts only a hull JSON,
output directory, and surface solver profile (`kayakgen/cli/main.py:118`).
Repository search found no implementation symbols for `volume_mesh`,
`evidence_hashes`, or `readiness_authority` outside the RFC/workflow text.

Impact: current code is conservative and does not falsely promote open or
synthetic evidence, but RFC 0023's positive handoff path is not implemented.

### High: stale, forged, and outside-package refs are not enforceably rejected

RFC 0023 requires dispatch to reject diagnostics that reference a different
`body_ref`, hull hash, profile, tolerance set, stale volume-mesh diagnostics,
or mismatched artifact checksums (`docs/rfcs/0023-watertight-volume-mesh-handoff.md:113`).
Current dispatch validates only solver profile, readiness ordering, and
referenced file existence (`kayakgen/eval/cfd/jobs.py:730`). Artifact refs are
resolved as `(mesh_dir / ref).is_file()` and diagnostics are read from
`mesh_dir / ref` without path-bound validation or checksum comparison
(`kayakgen/eval/cfd/jobs.py:752`, `kayakgen/eval/cfd/jobs.py:791`).

`_profile_diagnostic_refs()` gathers `quality_reports` plus any manifest string
under a key containing "diagnostic" (`kayakgen/eval/cfd/jobs.py:826`), but the
manifest schema has no RFC 0023 diagnostic/hash fields to compare. `_job_id()`
hashes only `manifest.hull_hash`, mesh profile, solver profile, speed, density,
and viscosity; it does not include manifest refs, diagnostic hashes, artifact
hashes, or package location (`kayakgen/eval/cfd/jobs.py:963`).

Impact: after a positive evidence path is added, two packages with identical
hull/profile/fluid inputs but different referenced artifacts can collide in the
same deterministic job directory, and forged absolute or `../` refs can escape
the package if the target file exists.

### Medium: focused tests prove blanket rejection, not RFC 0023 discrimination

The existing CFD tests cover rejection of a hand-edited `cfd_ready` manifest,
forged quality-report content, synthetic closed-volume diagnostics, and a
generated closed-body diagnostic supplied through quality-report files
(`tests/test_cfd_jobs.py:269`, `tests/test_cfd_jobs.py:303`,
`tests/test_cfd_jobs.py:349`, `tests/test_cfd_jobs.py:409`). Those tests all
pass through the same broad "profile-scoped closed-volume diagnostic evidence"
rejection while `dispatch_evidence_satisfies_profile()` rejects every
`cfd_ready` request.

Missing focused coverage:

- successful handoff fixture with matching generated body, self-intersection,
  volume-mesh diagnostic, hashes, and profile;
- generated closed body with passing self-intersection but missing volume-mesh
  diagnostic remains below `cfd_ready`;
- stale diagnostic hash and stale volume-mesh hash rejection;
- cross-body/cross-hull/cross-profile/cross-tolerance rejection;
- absolute and parent-directory manifest ref rejection in core CFD dispatch;
- changed evidence changes deterministic refs or job identity where applicable.

### Medium: CLI/API explanations are too coarse for the handoff workflow

RFC 0023 asks for CLI/JSON output that explains why a package is below
`cfd_ready` (`docs/rfcs/0023-watertight-volume-mesh-handoff.md:162`). The
current `mesh-package` CLI prints only the manifest path and readiness level
(`kayakgen/cli/main.py:139`), even though the manifest contains detailed
readiness reasons. `cfd prepare` prints the raw exception string on failure
(`kayakgen/cli/main.py:177`); for current watertight packages the readiness
ordering failure fires before any richer evidence-class message
(`kayakgen/eval/cfd/jobs.py:743`). CLI tests assert only the readiness level or
one broad rejection string (`tests/test_cli.py:210`, `tests/test_cli.py:343`).

Impact: operators cannot distinguish missing volume mesh, stale hash, profile
mismatch, forged path, or synthetic evidence from the CLI once RFC 0023 evidence
classes are introduced.

## Evidence reviewed

- Workflow instructions: `docs/workflows/0034-watertight-volume-mesh-handoff/SOURCES.md`,
  `docs/workflows/0034-watertight-volume-mesh-handoff/prompts/review_ops.md`,
  runbook, role prompt, and workflow metadata for the review lane.
- Product contract sources: `docs/rfcs/0010-cfd-ready-mesh-contract.md`,
  `docs/rfcs/0015-cfd-solver-dispatch-and-jobs.md`,
  `docs/rfcs/0016-closed-volume-geometry.md`, and
  `docs/rfcs/0023-watertight-volume-mesh-handoff.md`.
- Implementation sources: `kayakgen/eval/mesh_package.py`,
  `kayakgen/eval/cfd/jobs.py`, `kayakgen/eval/closed_volume.py`,
  `kayakgen/eval/mesh_diagnostics.py`, and `kayakgen/cli/main.py`.
- Focused tests: `tests/test_mesh_package.py`, `tests/test_cfd_jobs.py`,
  `tests/test_cli.py`, `tests/test_closed_volume.py`, and targeted generated
  closed-body separation coverage in `tests/test_generated_closed_body.py`.
- One read-only helper pass independently checked the clarified verdict
  contract and concurred that the scaffold is ledger-ready with implementable
  findings.

## Validation and read-only commands run

- `sed -n` on `AGENTS.md`, the required workflow source/prompt files, RFCs, and
  the workflow runbook/role files.
- `nl -ba ... | sed -n ...` on relevant implementation and test sections for
  line-level evidence.
- `rg -n "VolumeMesh|volume_mesh|body_ref|evidence_hash|readiness_authority|cfd_ready|watertight_solid_resistance|stale|forg|synthetic|self_intersection|closed_volume_diagnostic" ...`
- `find striatum/0034-watertight-volume-mesh-handoff -maxdepth 3 -type f | sort`
  to confirm existing review artifacts.
- `git status --short`.
- One read-only helper/sub-agent pass for independent verdict semantics.

## Residual risks

- No focused product tests were executed during this revision; the review is
  static/read-only.
- I did not validate Striatum run/session/job/lease state beyond the workflow
  files and visible repo artifacts; no `.striatum` state was edited.
- Other lane artifacts already exist under
  `striatum/0034-watertight-volume-mesh-handoff/`; this revision only writes the
  requested `ops/REVIEW_OPS.md`.
- Current behavior is safer than false promotion because watertight `cfd_ready`
  is rejected everywhere. The remaining risk is that RFC 0023 cannot yet land
  without adding the positive evidence path and the hash/path-bound rejection
  checks above.
