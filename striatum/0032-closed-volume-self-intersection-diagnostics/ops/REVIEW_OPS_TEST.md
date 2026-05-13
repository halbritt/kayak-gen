author: operator [self-declared: operator-0032-ops]

# Ops/Test Review - Workflow 0032 Closed-Volume Self-Intersection Diagnostics

Verdict intent: accept_with_findings

## Scope Read

Read `AGENTS.md`, `docs/workflows/0032-closed-volume-self-intersection-diagnostics/SOURCES.md`, `docs/workflows/0032-closed-volume-self-intersection-diagnostics/prompts/review_ops_test.md`, RFCs 0004, 0016, and 0021, workflow 0027's operator report, `kayakgen/eval/closed_volume.py`, `kayakgen/eval/cfd/jobs.py`, `kayakgen/eval/mesh_package.py`, `kayakgen/cli/main.py`, `tests/test_closed_volume.py`, `tests/test_cfd_jobs.py`, and CLI tests around mesh package / CFD behavior.

Focused test commands attempted:

```text
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -m pytest -p no:cacheprovider tests/test_closed_volume.py tests/test_cfd_jobs.py -q
PYTHONDONTWRITEBYTECODE=1 python3 -m pytest -p no:cacheprovider tests/test_closed_volume.py tests/test_cfd_jobs.py -q
PYTHONDONTWRITEBYTECODE=1 python3 - <<'PY' ...closed-volume smoke import...
```

Result: not executable in this worktree. `.venv/bin/python` is absent, system Python has no `pytest`, and the import smoke check fails at `ModuleNotFoundError: No module named 'pydantic'`.

## Findings

### O-001 - The RFC 0021 schema transition must preserve RFC 0016 honesty

Current `ClosedVolumeDiagnostics` has no self-intersection fields and forbids extra fields (`kayakgen/eval/closed_volume.py:105`). `diagnose_closed_volume_body()` currently promotes a valid synthetic tetrahedron to `closed_volume` solely from closure, manifold, finite, degenerate, and positive signed-volume checks (`kayakgen/eval/closed_volume.py:151`), and the existing round-trip test locks that behavior for `explicit_synthetic_closed_volume_v1` (`tests/test_closed_volume.py:30`). RFC 0021 requires serialized self-intersection status, algorithm identity, tolerance, and pair count, and says existing RFC 0016 fixtures may remain valid only if they are honest about `not_checked` under the older policy (`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:44`, `docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:54`).

Required action: add an explicit compatibility plan in code and tests. Either keep `explicit_synthetic_closed_volume_v1` as a legacy profile with `self_intersection_status: not_checked`, or introduce a new RFC 0021 profile whose `closed_volume` readiness requires `passed`. Add JSON round-trip tests for old-profile diagnostics and new-profile diagnostics so missing or `not_checked` self-intersection evidence cannot silently satisfy the new profile.

### O-002 - Deterministic fail fixtures need closed, manifold self-intersections

Current closed-volume tests cover a valid tetrahedron, an open tetrahedron, a nonmanifold duplicate-face case, reversed orientation, and invalid face indices (`tests/test_closed_volume.py:30`, `tests/test_closed_volume.py:57`, `tests/test_closed_volume.py:72`, `tests/test_closed_volume.py:91`, `tests/test_closed_volume.py:105`). They do not yet cover the specific RFC 0021 failure mode: a closed edge-manifold body that intersects itself while passing the old RFC 0016 checks. RFC 0021 also requires body-level treatment across parts, so a hull/deck-style cross-part intersection must be a body failure even if each part is locally manifold (`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:68`).

Required action: add deterministic synthetic fixtures whose closure/manifold/signed-volume checks pass before the self-intersection check runs. At minimum, keep a non-self-intersecting closed fixture with `self_intersection_status == "passed"` and `self_intersection_pair_count == 0`, add a deliberately intersecting closed fixture with stable nonzero pair count and bounded example pairs, and add or shape that fixture so at least one intersection is between different `ClosedSurfacePart` entries. Avoid open bow-tie fixtures where boundary or nonmanifold failures mask the self-intersection diagnostic.

### O-003 - Ambiguous and tolerance behavior needs blocking tests

RFC 0021 makes self-intersection tolerance part of serialized output and says ambiguous cases may be classified as `inconclusive`; both `failed` and `inconclusive` block readiness for any profile that adopts the RFC (`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:46`, `docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:62`). The current tolerance model only serializes vertex-weld, degenerate-face, and signed-volume tolerances (`kayakgen/eval/closed_volume.py:24`).

Required action: add `self_intersection_tolerance_m` to the policy/diagnostic output and test that `failed` and `inconclusive` both produce invalid readiness under the RFC 0021 profile. If the first implementation deliberately avoids producing `inconclusive`, still add model/readiness coverage proving an inconclusive diagnostic cannot be accepted as `closed_volume`.

### O-004 - The intersection search needs an explicit performance envelope

The current topology diagnostics are bounded by linear edge counting and tolerance welding (`kayakgen/eval/closed_volume.py:301`, `kayakgen/eval/closed_volume.py:364`). RFC 0021 allows a conservative broad-phase bounding-box algorithm and bounded example reporting (`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:52`, `docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:62`). A naive all-triangle-pairs implementation would be acceptable for tiny tetrahedron fixtures but risky for future generated closed bodies.

Required action: implement a deterministic broad phase before triangle-triangle tests, skip only adjacency that is explicitly defined by shared vertices or edges, and bound retained example pairs. Add a focused stress-style test with many non-overlapping triangles or components that proves the broad phase returns zero intersections without material runtime growth, and assert the serialized example list is capped.

### O-005 - `cfd_ready` rejection must remain true even for passed self-intersection evidence

The current safe slice is conservative: closed-volume diagnostics carry `cfd_ready: false`, `dispatch_evidence_satisfies_profile()` always returns `False`, and watertight dispatch requires profile-scoped diagnostic evidence before it can proceed (`kayakgen/eval/closed_volume.py:129`, `kayakgen/eval/closed_volume.py:210`, `kayakgen/eval/cfd/jobs.py:459`). Mesh packages for generated hulls still report separate open surfaces and stay below `cfd_ready` for the watertight profile (`kayakgen/eval/mesh_package.py:154`), with CLI coverage for that boundary (`tests/test_cli.py:136`, `tests/test_cli.py:201`). RFC 0021 explicitly says self-intersection success is necessary future evidence, not sufficient CFD evidence (`docs/rfcs/0021-closed-volume-self-intersection-diagnostics.md:73`).

Required action: add a regression that forges or references a valid RFC 0021 closed-volume diagnostic with `self_intersection_status == "passed"` and still verifies `prepare_local_job(..., unavailable_watertight_solid_profile())` rejects any `cfd_ready` claim. If a CLI surface is added for closed-volume diagnostics, add CLI tests that generated open-surface packages and display STL output are not promoted to `closed_volume` or `cfd_ready`.

## Positive Coverage

The current implementation already has the right diagnostic-only bias. It does not build generated closed bodies, it keeps `cfd_ready` false on closed-volume diagnostics, it rejects forged watertight dispatch evidence, and generated mesh packages remain separate open hull/deck surfaces. That makes the RFC 0021 safe slice acceptable if the implementation adds self-intersection evidence without changing those boundaries.
