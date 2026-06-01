author: reviewer-claude-opus-4.7-002

# Build Review — Threat Model (RFC 0043 stage 4 CLI-completion)

Verdict: accept

Scope: fresh, document-only review of the packet inputs (registry + evaluator
+ high-angle contracts + accepted_fit + measured_fixture + CLI + hull +
two web call sites; the §7 gate test suite). I ran the §7 gate
(`pytest tests/test_stability_fit_registry.py
tests/test_measured_stability_acceptance.py
tests/test_measured_stability_ingest.py
tests/test_claim_state_measured_promotion.py tests/test_cli_stability.py
tests/test_resolve_analytical_claim_label.py -q` → **89 passed in 0.72s**)
and `ruff check kayakgen/ tests/` (**All checks passed!**). I did not
consult ledgers, prior-round notes outside the inputs list, or repository
state beyond inputs.

## Trust boundaries and attack surfaces

| # | Boundary | Trust posture | Defense |
|---|---|---|---|
| T1 | `data/stability/fixtures/<id>/manifest.json` (untrusted disk bytes) | Bytes only — content is acceptance-gated | Schema (RFC 0056) + loader gates 1-3b (smoothness, trace resolution, operator-bound widths, rights) |
| T2 | `data/stability/fixtures/<id>/promotion.json` (untrusted disk bytes) | Must parse + hash-bind manifest | Gates 4-7 (parse, sha256 vs canonical manifest bytes, target=measured, reviews all accepted) |
| T3 | `data/stability/fits/*.json` (untrusted disk bytes) | Must cite fixture + match runtime | Gates 8-11 (fixture citation by id+sha, hull-class binding, heel overlap, evaluator version, strict accepted) |
| T4 | `Hull.hull_class` (operator-authored field) | Optional; safe default `None` | `resolve_analytical_claim_label` isinstance-string check → unset stays unvalidated |
| T5 | Registry memoization cache | Per-process, key must invalidate on any gated-evidence change | `_dir_fingerprint` walks ALL files under fits + sibling fixtures tree (not only `*.json`); cache key includes `(root, mtime_ns, entry_count, evaluator_version)` |
| T6 | `ANALYTICAL_EVALUATOR_VERSION` runtime constant | Pinned in `evaluator.py:50` | Gate 10 equality check; constant is in the cache key |

The central invariant — "fixture presence does not flip the label; only the
full chain does" — is enforced by `load_stability_fit_registry` running every
gate against on-disk bytes on every load (subject to a correctly-keyed cache).

## Discharged findings from the prior codex threat_model review

The packet brief flags three findings to confirm discharged. All three are
discharged in this build and locked down by tests:

1. **Cache invalidates on trace-evidence deletion** (codex P1 / handoff Rev. 1
   P1). `kayakgen/eval/stability/registry.py:442-478` (`_dir_fingerprint`)
   walks `path.glob("*")` AND `fixtures.rglob("*")` over every entry (any
   extension, files + dirs). The cache key also carries `entry_count` to
   defend against sub-mtime-granularity races on tmpfs. Regression:
   `tests/test_claim_state_measured_promotion.py:474`
   `test_registry_cache_invalidates_when_trace_evidence_disappears` — stages
   a passing triple, calls `load_stability_fit_registry` (registers cache),
   deletes `fixtures/<id>/cal/pre.csv`, then calls the loader again with NO
   `clear_registry_cache()` and asserts the fit is dropped. Discharges
   codex's "specific threat path from the handoff" requirement verbatim.

2. **Real-Hull production-path flip goes through `load_stability_fit_registry`**
   (handoff Rev. 1 P2). The resolver-only test
   `tests/test_resolve_analytical_claim_label.py:139-154`
   (`test_real_hull_with_hull_class_flips_under_covering_fit`) is preserved
   for resolver-matching logic, AND a real production-path test landed at
   `tests/test_resolve_analytical_claim_label.py:201-224`
   (`test_real_hull_flips_through_load_stability_fit_registry`) that stages
   the full triple on disk via `stage_acceptance_triple`, resolves through
   `reg.load_stability_fit_registry(root)` (the same loader the evaluator at
   `evaluator.py:407-409`, the frontier view at
   `generate_frontier_view.py:582`, and the spec form at
   `generate_spec_form.py:909` all consume via `_loaded_fit_registry()`),
   and asserts the flip. A negative twin at line 227
   (`test_real_hull_stays_unvalidated_when_registry_drops_fit`) confirms a
   stale evaluator-version gate drop keeps a real Hull unvalidated through
   the same path.

3. **Fit-vs-fixture hull-class binding gate (gate 8a)** (handoff Rev. 1 P2).
   `kayakgen/eval/stability/registry.py:297-311` rejects any fit whose
   `hull_family_scope.hull_class != manifest.hull_identity.hull_class` with
   `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH` (`registry.py:62`). The CLI
   `accept-fit` enforces the same gate before writing the record
   (`stability_cli.py:383-392`). Tests:
   - `tests/test_stability_fit_registry.py:281-296`
     `test_gate_fit_hull_class_fixture_mismatch` — registry-level rejection
     of a sea_kayak fixture + sprint_k1 scope fit.
   - `tests/test_claim_state_measured_promotion.py:333-371`
     `test_registry_drops_fit_when_scope_hull_class_diverges_from_fixture` —
     plus the resolver guarantee that a sprint hull stays unvalidated even
     when the dropped fit's scope nominally covered it.
   - `tests/test_claim_state_measured_promotion.py:374-425`
     `test_accept_fit_refuses_hull_class_fixture_mismatch` — CLI-level
     refusal via `CliRunner`.
   - Reason completeness:
     `tests/test_stability_fit_registry.py:413`
     `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH` is in the
     `test_every_reason_has_a_next_action` emitted-reason set; the
     `REASON_NEXT_ACTION` template lands at `registry.py:86`.

## Original threat-model walk over the build

### `hull_class` plumbing — over-broad / wrong / attacker-controlled

The packet asks specifically: "can a wrong, over-broad, or attacker-controlled
hull_class let a fit flip a hull it should not cover?"

- **Wrong / mismatched class on the fit side.** Gate 8a (above) makes the
  registry refuse a fit whose scope hull_class disagrees with the
  fixture's `hull_identity.hull_class`. So a fit scoped to `sprint_k1` cannot
  load against a `sea_kayak` measurement, and vice versa.
- **Over-broad envelope on the fit side.** `HullFamilyScope.design_hash_envelope`
  is operator-authored and can list any number of design hashes within the
  same hull_class. This is by design: the envelope IS the calibration's
  hull whitelist. The threat-model boundary is "no flip outside the
  envelope" — `resolve_analytical_claim_label`
  (`high_angle_contracts.py:71-79`) iterates only accepted records whose
  `scope.hull_class == hull.hull_class` AND `hull.design_hash() in
  scope.design_hash_envelope`. A hull whose design_hash is NOT in any
  loaded fit's envelope stays unvalidated, even if classes match. Covered
  by `tests/test_resolve_analytical_claim_label.py:90`
  `test_design_hash_outside_envelope_stays_unvalidated`.
- **Attacker-controlled hull_class.** `Hull.hull_class` is a Pydantic field
  on a frozen=False model authored by the operator at hull creation; it is
  not network-driven and the production frontends construct `Hull` from
  operator form state (`generate_spec_form.py`). No untrusted-input path
  sets it. Even if a malicious actor crafted a `Hull` JSON with a chosen
  class, gate 8a still requires a fit's `hull_family_scope.hull_class` to
  match the FIXTURE's `hull_identity.hull_class`, and the fixture is gated
  on the SHA-bound manifest. So forcing a flip requires either compromising
  the fixture manifest bytes (sha mismatch, gate 5) OR landing a fit whose
  envelope already lists the attacker's design_hash (operator-curated).
- **Unset hull_class.** `Hull.hull_class` defaults to `None`
  (`kayakgen/model/hull.py:67-79`). `resolve_analytical_claim_label`
  (`high_angle_contracts.py:66-69`) checks `isinstance(hull_class, str)`;
  `None` short-circuits to `unvalidated_hydrostatic_comparison`. The
  docstring on the field explicitly names this as the threat-model safety
  invariant. Covered by `tests/test_resolve_analytical_claim_label.py:157`
  `test_real_hull_without_hull_class_stays_unvalidated` and
  `tests/test_claim_state_measured_promotion.py:89`
  `test_claim_label_unchanged_for_hull_with_no_hull_class`.

### `promote-fixture` does not mutate the manifest

`kayakgen/cli/stability_cli.py:188-251` reads the manifest bytes once,
validates the packet, hashes the parsed manifest with
`fixture_canonical_sha256`, refuses on hash mismatch, refuses overwrite
unless byte-identical (`promote-fixture` clean no-op path), and writes only
`promotion.json`. Line 250 is a defense-in-depth `assert
manifest_path.read_text(encoding="utf-8") == manifest_bytes` after the
write, so any future regression that introduced a manifest write would
trip in tests.

### `accept-fit` refusal coverage

`accept-fit` (`stability_cli.py:254-431`) enforces, in order, every gate
the registry enforces, with the same `REASON_*` codes, so a fit that would
land but be dropped at load is refused at write time instead. The refusal
path enumerated:

- Unpromoted fixture (`promotion_target != "measured_stability_fixture"`) →
  `REASON_FIXTURE_NOT_PROMOTED` (`stability_cli.py:354-359`).
- sha256 mismatch between packet's `fixture_ref.fixture_sha256` and on-disk
  manifest hash → `REASON_FIXTURE_SHA256_MISMATCH` (`:346-352`).
- Evaluator version mismatch → `REASON_EVALUATOR_VERSION_MISMATCH`
  (`:404-410`).
- Strict-skipped (`strict=False`) record → `REASON_STRICT_CHECK_SKIPPED`
  (`:412-417`). The schema validator at `accepted_fit.py:148-185` also
  forbids constructing a strict record whose metrics breach thresholds; a
  loosened strict record is rejected by the schema before reaching the CLI.
- Hull-class binding (gate 8a) → `REASON_FIT_HULL_CLASS_FIXTURE_MISMATCH`
  (`:383-392`).
- Manifest / promotion missing on disk → `REASON_FIXTURE_MANIFEST_MISSING`
  / `REASON_PROMOTION_PACKET_MISSING` (`:308-319`).

Test coverage in `tests/test_cli_stability.py` (sweep of the new
signature + structured-JSON refusal shape) + the targeted refusal tests
in `tests/test_measured_stability_acceptance.py` (per `inputs[]` not
named in the packet but reachable from the suite which passed § 7).

### Registry cache safety

- Cache key:
  `(str(fits_root.resolve()), max_mtime_ns, entry_count, evaluator_version)`
  (`registry.py:397-398`). The version is in the key — a stale runtime
  cannot re-use a tuple cached under the matching version. Locked by
  `tests/test_claim_state_measured_promotion.py:428`
  `test_registry_cache_invalidates_on_evaluator_version_change`.
- `_dir_fingerprint` (`registry.py:442-478`) walks the fits dir AND the
  sibling fixtures tree, every entry, all extensions. Deleting any
  tracked file drops `entry_count` regardless of mtime granularity.
- `with_diagnostics=True` reads bypass the cache (`:399-400`,
  `:435-436`), so the diagnostic side-channel is always fresh — a tool
  asking "why did this fit drop?" is not handed a stale answer.

### Pure resolver caveat

`resolve_analytical_claim_label` (`high_angle_contracts.py:60-79`) is a
pure function over any iterable. A *direct* in-process caller can still
hand it a hand-built `StabilityFitRecord` and get a validated label
without touching the loader gates. This is the codex residual note, and
it is correct as-stated: the boundary is "all production call sites must
go through the loader." All three production sites do
(`evaluator.py:407-409`, `generate_frontier_view.py:582`,
`generate_spec_form.py:909`). The unit tests that build records
in-process for resolver coverage are clearly labeled as such.

### Two web call sites read the loader (not the constant)

`grep` confirms `EMPTY_STABILITY_FIT_REGISTRY` is no longer imported by
either web module; both `generate_frontier_view.py:582` and
`generate_spec_form.py:909` route through `_loaded_fit_registry()` whose
body is the same mtime-memoized lazy accessor as the evaluator's. A Trame
session that runs `promote-fixture` / `accept-fit` mid-flight sees the
flip on the next refresh without a process restart. Behaviour locked by
`tests/test_claim_state_measured_promotion.py:256`
`test_generate_frontier_view_color_token_flips_under_loaded_registry`
and `:241` `test_evaluator_flips_result_semantics_under_loaded_registry`
(both flow through `_loaded_fit_registry()`).

## Confirmations checklist (packet brief)

- [x] Full hash-bound chain is the only flip path (manifest + promotion.json
      + strict-accepted fit + evaluator-version match + hull_family_scope
      coverage).
- [x] `hull_class` plumbing: wrong / over-broad / attacker-controlled paths
      blocked by gate 8a + envelope membership + Pydantic field author.
- [x] Unset `hull_class` keeps the label unvalidated (default `None` +
      `isinstance(str)` guard).
- [x] `promote-fixture` does not mutate the manifest (read-only +
      defense-in-depth assert).
- [x] `accept-fit` refuses unpromoted / sha-mismatch / version-mismatch /
      strict-skipped fixtures with the matching `REASON_*` code.
- [x] Tests cover the threat surface including the cache-eviction-on-trace-
      evidence-deletion regression in
      `tests/test_claim_state_measured_promotion.py` and the fit-vs-fixture
      hull-class binding test in `tests/test_stability_fit_registry.py`.
- [x] Real-Hull production-flip test exercises `load_stability_fit_registry()`
      (not a stub).
- [x] Prior codex threat_model review findings (cache invalidation,
      production-path coverage, hull-class binding gate + completeness set)
      are all discharged.
- [x] §7 gate ran clean (`pytest … -q` → 89 passed in 0.72s; `ruff check
      kayakgen/ tests/` → All checks passed).

## Residual observations (no verdict impact)

- **R1. `resolve_analytical_claim_label` is intentionally a pure resolver.**
  Direct in-process callers can hand it any iterable. The defense is
  "production call sites route through `load_stability_fit_registry`,"
  which the three sites verifiably do. A future RFC could narrow this by
  requiring the resolver to accept only a sentinel returned by the loader,
  but doing so now would couple types unnecessarily and add no real safety
  given the call-site discipline. Noting for future-RFC tracking only.
- **R2. `runtime_evaluator_version` override is a test-only kwarg.** It is
  reachable from any caller, so an in-process attacker who can call the
  loader can bypass gate 10 by passing the fit's own version. This is the
  same pure-resolver-as-iterable shape as R1 and out of scope for stage 4;
  flagging only so a future RFC can decide whether to lock the kwarg behind
  a sentinel.
- **R3. Cache fingerprint uses `entry_count` for tmpfs sub-mtime races.**
  Sound, and called out in the registry docstring. If a workflow ever
  swap-renames evidence files (delete + create within the same tick *and*
  preserving the count *and* without advancing the parent dir mtime), the
  cache could theoretically miss. Pathological and not a realistic
  attacker path; noting because the comment chain made it sound load-
  bearing and worth flagging in tracker hygiene.

## Verdict rationale

Every gate in §B of the synthesis is encoded in
`load_stability_fit_registry` and re-checked at the CLI before any record
lands on disk. Every previously-flagged codex threat_model finding is
discharged with a named regression test. The full §7 gate passes (89/89)
and ruff is clean. The `hull_class` plumbing — including the unset-default
safety case, the strict fit↔fixture binding, and the over-broad/cross-class
attack path — is the load-bearing surface and is correctly defended on
both the registry side and the `accept-fit` CLI side. The two web call
sites no longer reach for the empty-registry constant; they route through
the loader. The residual observations are notes for tracker hygiene only;
none reduces the stage-4 safety surface.

Accept.
