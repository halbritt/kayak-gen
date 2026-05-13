I have sufficient context to produce the traceability artifact. Writing it now.

---

Verdict intent: accept_with_findings

# Review Traceability: 0039 Plumb-Stem Closure Semantics

## Scope

This is the `reviewer_traceability` artifact for workflow `0039-plumb-stem-closure-semantics`. The mandate is to map RFC 0028 acceptance criteria onto:

1. The four RFC 0004 deferrals it explicitly closes.
2. Implementation surfaces in `kayakgen/` that must change or that already host the legacy slice.
3. Tests that currently exist or are absent.
4. Explicit non-goals and the load-bearing dependency on RFCs 0022–0024.

I did not call `striatum`, did not mutate code, and did not update `OPERATOR_REPORT.md`.

## Sub-Agent Help Used

None spawned. The operator instruction asks for the maximal *useful* number of parallel workers; for a traceability map across two short RFCs (0004 ~170 lines, 0028 ~160 lines), one matching test file (`tests/test_plumb_bow.py`), one geometry module (`kayakgen/model/geometry.py`), and one model file (`kayakgen/model/hull.py`), serial inspection in the main session is faster than spawning agents with overlapping read sets. The peer `reviewer_ops` artifact already used four disjoint sub-agents on the broader code/tests/CLI surface, and its findings are cited below rather than re-derived.

## Sources Reviewed

- `AGENTS.md`
- `docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md`
- `docs/workflows/0039-plumb-stem-closure-semantics/roles/reviewer_traceability.md`
- `docs/workflows/0039-plumb-stem-closure-semantics/prompts/review_traceability.md`
- `docs/rfcs/0004-plumb-bow.md`
- `docs/rfcs/0028-plumb-stem-closure-semantics.md`
- `docs/rfcs/0022-generated-closed-body-construction.md` (RFC 0028 depends on it)
- `docs/USER_GUIDE.md`
- `kayakgen/model/hull.py`
- `kayakgen/model/geometry.py`
- `kayakgen/eval/mesh_diagnostics.py`
- `kayakgen/eval/closed_volume.py`
- `tests/test_plumb_bow.py`
- Peer review artifacts under `striatum/0039-plumb-stem-closure-semantics/{domain,ops}/`.

`SOURCES.md` lists two stale paths (`kayakgen/geometry/loft.py`, `kayakgen/mesh/diagnostics.py`); the live code is `kayakgen/model/geometry.py` and `kayakgen/eval/mesh_diagnostics.py`. This is captured below as TRACE-001 and matches the peer `reviewer_ops` finding OPS-001.

## RFC 0004 Deferral → RFC 0028 Resolution Map

RFC 0028 enumerates four deferred semantics (`docs/rfcs/0028-plumb-stem-closure-semantics.md:9-22`). Each is mapped here to: which RFC 0004 wording it replaces, the RFC 0028 acceptance criterion that closes it, the implementation surface, and the test coverage state.

### Deferral D1 — Exact endpoint section area for `rake = 0.0`

- **RFC 0004 wording closed:** `docs/rfcs/0004-plumb-bow.md:57-60` ("Exact endpoint non-zero area is deferred until explicit end-cap semantics are designed") and `:141-144` Acceptance "Deferred: STL export currently produces open hull and deck surfaces… It does not produce a closed watertight hull-plus-deck solid or explicit non-degenerate end-cap polygons."
- **RFC 0028 resolution:** `docs/rfcs/0028-plumb-stem-closure-semantics.md:82-94` requires the *closed-body* path to keep a non-zero terminal section for `rake = 0.0`, with the open inspection surfaces explicitly allowed to retain the legacy zero-area tip. Acceptance criteria `:128-131` pin the requirement for bow and stern.
- **Implementation surface:** `kayakgen/model/geometry.py:122-153` (the `_get_area_fraction` + `_plumb_transition_decay` + `_end_decay` triple) and `:215-244` (`mesh`) currently produce the open surface with a zero-area collapse at `|x_norm| ≥ 0.9999`. No closed-body builder exists yet; the only closed-volume code path is the explicit synthetic mesh in `kayakgen/eval/closed_volume.py` (which RFC 0022 supersedes for generated bodies). The new builder declared by RFC 0028 §4 is the load-bearing surface.
- **Tests today:** `tests/test_plumb_bow.py:55-61` samples `x = -0.45 * L`, *inside* the plumb transition zone, not the endpoint. This honors the RFC 0004 acceptance wording but does not yet exercise RFC 0028's `x = -L/2` / `x = +L/2` requirement. The peer `reviewer_ops` OPS-004 flags the same gap.
- **Status:** correctly framed in RFC 0028; not yet implemented or tested. Implementation belongs to a follow-on workflow scoped against RFC 0022 (closed-body construction).

### Deferral D2 — Asymmetric bow/stern rake

- **RFC 0004 wording closed:** `docs/rfcs/0004-plumb-bow.md:52-53` ("`bow_rake` applies independently to bow and stern; a single scalar controls both (symmetric). A future RFC may split them.") and Open Question `:155-158` ("Should bow and stern rake be independently controllable? Deferred to RFC 0006.")
- **RFC 0028 resolution:** §2 (`docs/rfcs/0028-plumb-stem-closure-semantics.md:67-80`) introduces `stern_rake` and pins `bow_rake` as a symmetric compatibility alias. Acceptance criterion `:124-125` requires both independent input and legacy-input round-trip without geometry change. Acceptance `:132-133` mandates a mixed (plumb bow + raked stern) test.
- **Implementation surface:** `kayakgen/model/hull.py:43` declares `bow_rake` only; `model_config = ConfigDict(extra="forbid")` at `:27` causes JSON containing `stern_rake` to be rejected today. `kayakgen/model/geometry.py:152, :163, :171, :253, :258, :279` all consume `self.hull.bow_rake` as a symmetric scalar over `abs(x)`-based decay. The geometry must learn to select side-specific rake under the X convention. This redirects RFC 0004's "Deferred to RFC 0006" pointer to RFC 0028 — note that RFC 0006 (`docs/rfcs/0006-design-constraints.md`) is unrelated to rake; that pointer in RFC 0004 is stale, which is itself a small traceability error in RFC 0004 that 0028 effectively retires.
- **Tests today:** `tests/test_plumb_bow.py` covers only symmetric `bow_rake`. No `stern_rake` round-trip test, no asymmetric geometry test, no legacy-JSON compatibility test. OPS-002 and OPS-003 capture this in code terms.
- **Status:** scope is correctly captured by RFC 0028; tests and `Hull`/loft changes are not yet implemented.

### Deferral D3 — Coordinate and sign conventions

- **RFC 0004 wording closed:** Not stated explicitly in RFC 0004 — the document references "near `x = -L/2`" and "stations near `x = -L/2`" (`docs/rfcs/0004-plumb-bow.md:54-60`, `:138-144`) without formally pinning the X convention. The convention has lived implicitly in `kayakgen/model/geometry.py` (e.g., `:122-127`, `:219`, `:247-258`).
- **RFC 0028 resolution:** §1 (`docs/rfcs/0028-plumb-stem-closure-semantics.md:46-66`) pins X bow-to-stern (bow `x = -L/2`, stern `x = +L/2`), Z upward, port/starboard symmetry implicit, and defines rake as dimensionless fullness in `[0, 1]` with reverse rake out of scope. Acceptance criterion `:127` requires documentation and tests to pin these conventions for cap winding and signed volume.
- **Implementation surface:** the conventions already match the loft (`kayakgen/model/geometry.py:122-153, :219, :246-259`), as confirmed by the peer `reviewer_domain` artifact. What is missing is *documented*, *test-pinned*, and *user-guide-visible* affirmation. `docs/USER_GUIDE.md:52-55` describes `bow_rake` but does not call out X direction or stem endpoints; OPS-005 flags this.
- **Tests today:** the X convention is implicit in tests (`tests/test_plumb_bow.py:49`'s `last5 = keel[keel[:, 0] <= -0.475 * L]` assumes bow is negative X). There is no direct convention-pinning test (e.g., `assert bow_x < stern_x`, or normal-orientation assertions on a cap).
- **Status:** correctly scoped by RFC 0028; aligns with current code; needs documentation and explicit convention tests.

### Deferral D4 — Closed-body ownership and dependency boundaries

- **RFC 0004 wording closed:** `docs/rfcs/0004-plumb-bow.md:141-144` Acceptance "Deferred: STL export currently produces open hull and deck surfaces… It does not produce a closed watertight hull-plus-deck solid…" and `:152-156` Open Question on hard vertical face / explicit end-cap polygon.
- **RFC 0028 resolution:** §4 Dependency Boundaries (`docs/rfcs/0028-plumb-stem-closure-semantics.md:107-121`) places closed-body construction in a new builder layer above `kayakgen.model.Hull` and `kayakgen.geometry`, below presentation, with mesh diagnostics owning the watertight/closed claims. Acceptance criteria `:134-138` require open exports to keep their open-surface labels unless an explicit closed-body command/profile is selected, and require diagnostics-not-rake to decide readiness.
- **Implementation surface:** the boundary RFC 0028 names is exactly what RFC 0022 (`docs/rfcs/0022-generated-closed-body-construction.md:46-79`) builds — the `generated_hull_plus_deck_closed_body_v1` profile. Today, `kayakgen/eval/closed_volume.py:1-7` is explicitly limited to caller-supplied synthetic meshes ("This module … does not build closed bodies from generated ``Hull`` surfaces and it never promotes a body to ``cfd_ready``"). `kayakgen/eval/mesh_diagnostics.py:240-267` returns at most `stl_surface` for the open hull/deck mesh — the open-surface boundary RFC 0028 wants preserved is already in place.
- **Tests today:** `tests/test_plumb_bow.py:78-87` asserts open STL surface generation at `bow_rake=0` succeeds with the same mesh shape as raked; this preserves the open-export contract. No closed-body-from-`Hull` tests exist. `kayakgen/eval/mesh_diagnostics.py:240-267` and its tests do not yet promote anything generated past `stl_surface`, which matches the RFC 0028 boundary; OPS-006 flags a separate concern (finite-but-bad meshes still being labeled `stl_surface`), which is adjacent but not blocking the traceability of D4.
- **Status:** RFC 0028 correctly bounds the boundary work to RFC 0022. The actual construction work belongs to workflow 0033 (`striatum/0033-generated-closed-body-construction/`), already opened in tree; that is consistent with the dependency line at `docs/rfcs/0028-plumb-stem-closure-semantics.md:5-7`.

## Acceptance Criterion Trace Matrix

| AC# | RFC 0028 acceptance (lines `:124-138`) | Closes deferral | Implementation surface | Test surface | Status |
|---|---|---|---|---|---|
| AC1 | Independent bow/stern rake; legacy `bow_rake` JSON preserves geometry | D2 | `kayakgen/model/hull.py:27, :43`; loft consumers in `kayakgen/model/geometry.py:152, :163, :171, :253, :258, :279` | New round-trip test missing; `tests/test_hull_roundtrip.py` does not yet cover `stern_rake` | Not implemented |
| AC2 | Pin X-coord, orientation, cap winding, signed volume in docs and tests | D3 | `docs/USER_GUIDE.md:47-55`; `kayakgen/model/geometry.py:122-153, :246-259` | No convention/winding test; cap doesn't exist yet | Not implemented |
| AC3 | `bow_rake = 0.0` → non-zero terminal bow section at `x = -L/2` (closed body) | D1 | New closed-body builder (per RFC 0022) | Endpoint test missing; current `tests/test_plumb_bow.py:55-61` samples `-0.45 * L` | Not implemented |
| AC4 | `stern_rake = 0.0` → non-zero terminal stern section at `x = +L/2` (closed body) | D1 + D2 | New closed-body builder (per RFC 0022) | Missing | Not implemented |
| AC5 | Mixed plumb-bow/raked-stern produces asymmetric geometry without changing default | D2 + D1 | Loft (geometry.py decay), and the closed-body builder | Missing | Not implemented |
| AC6 | Open hull/deck STL exports remain labeled "open inspection surfaces" unless closed-body command/profile is explicit | D4 | `kayakgen/cli/main.py` (mesh-package output), `kayakgen/eval/mesh_diagnostics.py:250-267`, `kayakgen/eval/mesh_package.py` | `tests/test_cli.py:151-173` asserts open-surface warning under `watertight-solid` profile | Partially in place |
| AC7 | Diagnostics — not rake settings — decide closed-volume/watertight readiness | D4 | `kayakgen/eval/mesh_diagnostics.py:240-267`; `kayakgen/eval/closed_volume.py` | Existing readiness tests; OPS-006 notes a gap on finite-but-bad meshes | Partially in place |

## Non-Goal Trace

RFC 0028 explicitly excludes (`docs/rfcs/0028-plumb-stem-closure-semantics.md:38-43`):

- New rocker/flare/tumblehome/reverse-rake/multi-chine controls. Reverse rake is also excluded by the `[0, 1]` range at `:64-66`. This is consistent with `kayakgen/model/hull.py:43` (`ge=0, le=1`) and with RFC 0004's Non-Goals at `:62-65`.
- Declaring generated bodies CFD-ready. This is consistent with `kayakgen/eval/closed_volume.py:5-6` ("never promotes a body to ``cfd_ready``"), `mesh_diagnostics.py:240-267` (`stl_surface` ceiling), and RFC 0022's `cfd_readiness_policy: "never_claim_cfd_ready"` at `closed_volume.py:71-72`.
- Replacing existing hull/deck inspection STL surfaces. This is consistent with `tests/test_plumb_bow.py:78-87` continuing to validate the open inspection mesh shape at `bow_rake=0`.

No non-goal is contradicted by the proposal text or the existing implementation contract.

## Cross-RFC Dependency Trace

- RFC 0028 declares it "depends on the generated closed-body work from RFCs 0022-0024" (`:5-7`). RFC 0022 supplies the `generated_hull_plus_deck_closed_body_v1` profile and the cap/sheerline/deck-join policy framework. RFC 0028 reuses that profile's machinery for the exact-plumb endpoint case rather than inventing a parallel one — this is correct: AC3/AC4 cannot be satisfied without RFC 0022's builder, and RFC 0028's §4 dependency boundary references exactly that layer.
- RFC 0028 retires the RFC 0004 "Deferred to RFC 0006" pointer for asymmetric rake (RFC 0006 is design-constraints surfacing, not rake). The retirement is implicit rather than explicit; consider an editorial note in RFC 0004 once 0028 lands.
- RFC 0028 keeps RFC 0010 (`cfd-ready-mesh-contract`) as the readiness authority via §4 ("Mesh diagnostics, not rake settings, decide…"). This is consistent with the codified `_readiness()` ceiling.

## Findings

### TRACE-001 — Workflow `SOURCES.md` references stale paths

`docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md:8-9` lists `kayakgen/geometry/loft.py` and `kayakgen/mesh/diagnostics.py`. Neither exists in the tree (see `Glob kayakgen/**/*.py`). The live code is `kayakgen/model/geometry.py` and `kayakgen/eval/mesh_diagnostics.py`. A traceability reviewer following SOURCES literally would not find the rake decay or readiness ceiling, both of which are load-bearing for the trace.

Required action: update `docs/workflows/0039-plumb-stem-closure-semantics/SOURCES.md` to the live paths. Matches OPS-001.

### TRACE-002 — RFC 0004 still points asymmetric rake to RFC 0006

`docs/rfcs/0004-plumb-bow.md:155-158` says asymmetric bow/stern rake is "Deferred to RFC 0006." RFC 0006 (`design-constraints`) is unrelated; RFC 0028 is the actual heir. This is a one-line traceability defect in RFC 0004 that 0028 quietly retires.

Required action: when RFC 0028 lands, add a status note in RFC 0004 redirecting the asymmetric-rake Open Question to RFC 0028 (matches the workflow 0010/0019 status-note pattern already used in RFC 0004).

### TRACE-003 — Acceptance criteria do not name a test file or fixture

RFC 0028's acceptance criteria (`:124-138`) are well-defined geometrically but do not say *where* the asymmetric or endpoint tests live. The peer `reviewer_ops` artifact already names `tests/test_plumb_bow.py` plus new tests against the closed-body builder, but RFC 0028 leaves this implicit. For traceability of "the work is done," a downstream reviewer cannot read RFC 0028 alone and verify coverage.

Required action: add an Implementation Path bullet to RFC 0028 (or accept this finding as a notes-only docket) listing the expected test files: roundtrip (`tests/test_hull_roundtrip.py`), loft asymmetry (`tests/test_plumb_bow.py` or a new `tests/test_stern_rake.py`), and closed-body endpoint/cap winding (a new test module against the RFC 0022 builder). Non-blocking.

### TRACE-004 — Open Question on rake threshold needs a traceability anchor

RFC 0028 Open Question `:142-146` leans against applying exact endpoint area for any `rake < 0.05`, preferring exact-`0.0` semantics for deterministic tests. The acceptance criteria already mirror this (`:128-131` say `bow_rake = 0.0` / `stern_rake = 0.0` exactly). Suggest making the lean a hard rule in the AC body so future reviewers don't reopen the threshold debate.

Required action: tighten the Open Question into an explicit acceptance clause ("exact endpoint area is required only at `rake == 0.0`") or strike the Open Question as already decided. Editorial only.

### TRACE-005 — Mixed-rake AC needs explicit "default unchanged" pin

AC5 (`docs/rfcs/0028-plumb-stem-closure-semantics.md:132-133`) says mixed cases must "produce asymmetric geometry without changing the default hull." Today the only default-pin is the STL payload SHA in `tests/test_plumb_bow.py:23-30` (`bd3ba7d4…`). A `stern_rake` default of `1.0` plus the legacy `bow_rake = 1.0` must continue to hit that SHA, but neither RFC 0028 nor the workflow SOURCES says so.

Required action: when RFC 0028 lands, require the golden payload test to be reaffirmed under the new defaults. Matches the spirit of RFC 0004's "Landed: with `bow_rake = 1.0` (default), the package geometry preserves the legacy output" criterion.

## Positive Checks

- Every RFC 0004 deferral is addressed by exactly one RFC 0028 acceptance criterion (D1→AC3+AC4, D2→AC1+AC5, D3→AC2, D4→AC6+AC7). No deferral is left dangling.
- RFC 0028's non-goals are consistent with RFC 0004's non-goals and with current code: reverse rake is out of bounds in both documents and in `Hull.bow_rake` validation.
- The dependency on RFC 0022 is named explicitly in RFC 0028's context line (`:5-7`) and re-asserted in §4; the workflow tree already contains a parallel workflow `0033-generated-closed-body-construction/` for that work.
- The open inspection-surface contract from RFC 0004 is preserved verbatim by AC6, and existing tests (`tests/test_plumb_bow.py:78-87`, `tests/test_cli.py:151-173`) already lock it in.
- Coordinate convention proposed by RFC 0028 §1 matches the implicit convention already in `kayakgen/model/geometry.py` and confirmed by the peer `reviewer_domain` artifact.

## Recommendation

The workflow can proceed with the recorded findings. RFC 0028 cleanly closes the four RFC 0004 deferrals, correctly hands the implementation surface to the RFC 0022 builder, and preserves the open-export and readiness-gate contracts that the legacy slice depends on. None of the findings block acceptance — TRACE-001 is a SOURCES hygiene fix (also flagged by OPS-001), TRACE-002 is a one-line redirect in RFC 0004, and TRACE-003/004/005 are editorial pins that would make downstream traceability stronger but are not preconditions for landing.
