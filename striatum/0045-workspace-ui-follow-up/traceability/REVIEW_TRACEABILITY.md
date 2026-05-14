---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Traceability Review — RFC 0034 Workspace UI Follow-Up

## Verdict Intent

`accept_with_findings`

RFC 0034 maps cleanly to workflow 0044 final-review findings F1–F6 and to the
RFC 0033 §2/§4/§5/§8 acceptance criteria those findings track. The follow-up
preserves RFC 0033's no-new-backend-capability boundary, names the safe-now
slice the workflow 0044 ledger marked as residual, and does not expand into
new domain capability (hosted CFD, calibrated drag, watertight `cfd_ready`,
high-angle GZ, multi-variant overlays, mesh authoring API).

The findings below are implementation-scope ambiguities that should be
deduplicated into the ledger and resolved during build, not packet blockers.
None requires a remediation cycle: the RFC scaffold parses, the workflow
graph is consistent, and reviewers can begin first-pass evaluation against
this RFC immediately.

## Coverage Mapping

### Workflow 0044 final-review findings → RFC 0034 scope

| 0044 finding | 0034 coverage | Notes |
| --- | --- | --- |
| F1 — preset does not reseed or narrow sliders | §Proposal 1, §Acceptance 1, §Goals 1 | One-for-one. RFC 0034 reaffirms reseed + range narrowing + auto-flip to `custom`. |
| F2 — validity badge is static placeholder | §Proposal 2, §Acceptance 2, §Goals 2 | One-for-one. RFC 0034 pins the exact RFC 0033 §2 badge string set. |
| F3 — Resistance card omits sweep table and target row | §Proposal 3, §Acceptance 3, §Goals 3 | One-for-one. Read model already exists at `kayakgen/ui/web/controllers.py:200-259`. |
| F4 — Mesh tab does not render live diagnostics | §Proposal 4, §Acceptance 4, §Goals 4 | One-for-one. Welded-primary counts and readiness already exposed by `mesh_diagnostics_lines_from_state` and `mesh_package_view_model`. |
| F5 — Toolbar Export menu is incomplete | §Proposal 5, §Acceptance 5, §Goals 5 | RFC 0034 leaves Hydro JSON / Stability JSON / Mesh package implementation choices to ledger via Open Questions — see T1. |
| F6 — forbidden-string grep is narrower than RFC 0033 §8 | §Proposal 6, §Acceptance 6, §Goals 6 | RFC 0034 promises to broaden, but the explicit allowance set is hand-waved — see T2. |
| F7 — patch summary/changelog mismatch (cosmetic) | Excluded | Remediation correctly excludes; cosmetic only. |
| F8 — desktop region/test-id parity (deferred) | §Non-Goals | Correctly preserved as explicit deferral. |

### RFC 0033 §8 forbidden-copy list → RFC 0034 §Proposal 6 / §Acceptance 6

The RFC 0033 §8 canonical no-go set, drawn from the §"Acceptance Criteria"
list it references, comprises: `GZ_max`, `heel_angle_max_deg`,
bare `cfd_ready` outside `not watertight cfd_ready`, and `hosted`,
`cloud`, `worker queue`, `OpenFOAM`, `SU2` outside the no-hosted-worker
notice. The workflow 0044 F6 follow-up expands this checklist with
`calibrated drag`, `final prediction`, and `design fitness`. RFC 0034 §6
says reviewers should test "the full RFC 0033 §8 no-go list" with
"explicit allowances only for permitted negations such as `no hosted
worker is running` and `not watertight cfd_ready`," but does not
enumerate the allowance set — see T2.

### RFC 0033 acceptance criteria still open after workflow 0044 → RFC 0034 acceptance

| RFC 0033 acceptance bullet | Workflow 0044 status | RFC 0034 acceptance bullet |
| --- | --- | --- |
| Preset reseeds + narrows sliders (§2) | Open (F1) | "Selecting a web class preset changes the relevant slider values and slider bounds…" |
| Validity badge mirrors `_classify` set (§2) | Open (F2) | "The web validity badge changes with hull state and uses only the accepted RFC 0033 badge strings." |
| Resistance sweep table with target row (§4) | Open (F3) | "The Resistance card displays the fixed sweep speeds, target-speed row, and `kt \| Fn \| Rv N \| Rw N \| Rt N` data from the read model." |
| Mesh tab live diagnostics + readiness (§4) | Open (F4) | "The Mesh tab displays hull/deck diagnostics and package readiness using welded-primary counts and existing readiness vocabulary." |
| Toolbar `Export ▾` full menu (§5) | Open (F5) | "Export controls include Hull STL, Deck STL, Hydro JSON, Stability JSON, and Mesh package entries, with unavailable states honest." |
| §8 forbidden-copy grep assertion contract | Open (F6) | "Tests cover the full RFC 0033 §8 forbidden-copy list and preserve existing browser acceptance." |
| Three-region shell + region test ids | Landed | (Out of RFC 0034 scope; correctly outside.) |
| Persistent claim/readiness/CFD chip copy | Landed | (Out of RFC 0034 scope; correctly outside.) |
| `kayakgen/ui/theme.py` color-authority | Landed | (Out of RFC 0034 scope; correctly outside.) |
| Desktop `Cm` + `Export STLs` touch-ups | Landed | (Out of RFC 0034 scope; correctly outside.) |
| `evaluation_summary(state)` read model | Landed | (Out of RFC 0034 scope; correctly outside.) |

## Findings

Severity order: highest (T1) first.

### T1 — Export menu §5/§Acceptance 5 leaves three behaviors undefined

RFC 0034 §Proposal 5 and §Acceptance 5 promise Export menu entries for
`Hydro JSON`, `Stability JSON`, and `Mesh package`, but the RFC's
§"Open Questions" admits the implementation choice is unresolved:
"Whether Hydro JSON and Stability JSON should download from a browser
blob or first land as local server artifacts" and "Whether Mesh
package export should invoke existing server-local package creation
immediately or remain a disabled entry until a workflow explicitly
accepts web-side package authoring."

Today the controller surface in `kayakgen/ui/web/controllers.py` exposes
binary STL bytes (`stl_bytes_for_part`, lines 521-533), a full evaluation
payload via `/api/evaluate` (line 1425), but no Hydro JSON, Stability
JSON, or mesh-package author route. The workflow 0044 ledger pins
"Web-side mesh-package authoring API beyond wrapping current
server-local `kayakgen mesh-package` semantics" as an explicit deferral
and the remediation packet (`REMEDIATION.md > Caveats`) restates that
boundary.

This is enough for reviewers and the ledger to converge, but the RFC
itself should not leave three forbidden-vs-safe choices in
`accept_with_findings` scope without naming the conservative default.

Recommendation for ledger:

- `Hydro JSON` and `Stability JSON` can land safely as browser-blob
  downloads sourced from the existing `evaluate_hydrostatics(...)` and
  fixed-body equilibrium read models, so no new REST shape is needed.
- `Mesh package…` should remain a disabled entry with an honest
  unavailable tooltip in this slice. Web-side package authoring is on
  the 0033 deferral list; the ledger should not promote it from
  inside this follow-up.
- Implementer must keep `/api/stl`, `/api/evaluate`, `/api/cfd/*`, and
  `/api/hulls/*` JSON shapes unchanged, per RFC 0033 §"Compatibility".

Severity: implementation-scope ambiguity. Route to ledger.

### T2 — RFC 0034 §6 inherits §8 forbidden-copy contract without enumerating allowances

RFC 0034 §Proposal 6 broadens the forbidden-copy grep to "the full RFC
0033 §8 no-go list" with "explicit allowances only for permitted
negations such as `no hosted worker is running` and `not watertight
cfd_ready`." The current narrow assertion lives at
`tests/test_web_layout.py:94-100` and only covers `GZ_max`,
`heel_angle_max_deg`, and `cfd_ready` count. The workflow 0044 F6 list
explicitly named `OpenFOAM`, `SU2`, `cloud`, `worker queue`,
`calibrated drag`, `final prediction`, `design fitness` as additions.

Three traceability hazards remain for the implementer:

1. RFC 0034 says "such as" rather than naming the allowance set, so the
   permitted-negation list is ambiguous. RFC 0033 acceptance criteria
   already imply: `not watertight cfd_ready`, `no hosted worker is
   running` (note: `hosted` strictly only outside that notice), and
   `Raw comparative filter; not final prediction` (so `final
   prediction` outside that exact phrase is forbidden).
2. `kayakgen/ui/theme.py:226-232` contains a `validated_design_fitness`
   ChipSpec vocabulary entry — defined but never rendered. The new
   grep test must either (a) scope strictly to *rendered* UI output
   (`kayakgen/ui/web/app.py`, controller `lines` helpers, desktop
   visible labels) or (b) delete the unused vocabulary entry. The
   workflow 0044 final review used option (a) implicitly when it
   confirmed "No hits outside the allowed notice."
3. The strings `final prediction` and `cfd_ready` appear inside
   *permitted* negations in the existing static layout copy. The grep
   must therefore be implemented as "string X may only appear inside
   sanctioned phrase Y," mirroring the existing
   `test_forbidden_high_angle_and_mesh_claim_copy_does_not_creep_into_static_layout`
   pattern rather than a simple `not in` check.

Recommendation for ledger: pin the full forbidden set and the matching
permitted-negation set as test fixtures in `tests/test_web_layout.py`,
scoped to the rendered app source plus controller-emitted text
helpers, and exclude `kayakgen/ui/theme.py` chip-vocabulary tables
from the grep target (or remove the unused
`validated_design_fitness` vocabulary entry).

Severity: implementation-scope precision. Route to ledger.

### T3 — Validity-badge string set is not what `_classify` actually returns

RFC 0034 §Acceptance 2 limits the web badge to the RFC 0033 strings
`In <class> envelope`, `Custom — sub-touring`, `Custom — beyond elite`,
or `Custom (L/B_wl=X.X)`. RFC 0033 §2 itself names the same set and
says the kind is "derived from existing logic in `desktop._classify`."

`desktop._classify` at `kayakgen/ui/desktop.py:362-376` actually
returns the matched `KayakClass.label` (e.g., `"Touring sea kayak"`)
when a hull is inside an envelope, and only the `Custom` strings
otherwise. There is no `In <class> envelope` string anywhere in the
code today, and the desktop adds a trailing ` preset` decoration when
a preset is active (`desktop.py:395-396`).

So RFC 0034's web badge cannot be a direct copy of `_classify` — the
implementer must either:

- Add a small web helper that maps a matched `KayakClass` to the
  literal `In <class.name> envelope` string (per RFC 0033 wording), or
- Reuse `_classify` and accept that the badge displays the human
  label (e.g., `Touring sea kayak`), which would diverge from the RFC
  0033/0034 acceptance wording.

Recommendation for ledger: pick the first option (new web helper) so
the badge string set exactly matches the acceptance criteria; do not
rebind `desktop._classify`'s output to the web rail without an
intermediate normalization step.

Severity: implementation-scope ambiguity. Route to ledger.

### T4 — "Manual slider change flips preset to custom" is unscoped on web

RFC 0034 §Proposal 1 and §Acceptance 1 require manual slider edits to
switch the selected class preset back to `custom`, mirroring the
desktop semantics (`KayakGUI._on_class_select` companion behavior at
`kayakgen/ui/desktop.py:395-396` keeps `_active_class_name`).

The current web rail at `kayakgen/ui/web/app.py:613-689` binds the
class preset via `v_model=("class_preset",)` and the sliders via
`v_model=(key,)` independently. There is no listener that flips
`class_preset` to `"custom"` when a slider changes; symmetrically,
there is no preset `on_change` that reseeds slider values or narrows
slider ranges. The 0044 ledger P0 grouping captured rail structure
but not these two coupling behaviors.

Two ambiguities follow:

1. "Manual edit" must be defined as "any change to a slider that is
   currently bound to a class preset envelope." Edits to view-only
   `target_speed_kt` should NOT flip to `custom`. RFC 0034 should
   make this distinction explicit (or the ledger should pin it).
2. Slider-range narrowing is per-slider state; when the user flips
   back to `custom`, the ledger should specify whether the ranges
   revert to the global slider definition or stay narrowed.

Recommendation for ledger: define "manual edit" as a change to any
slider listed in `HULL_STATE_FIELDS` (i.e., exclude
`target_speed_kt`), and reset ranges to `SLIDER_DEFS` defaults on
`custom`.

Severity: implementation-scope ambiguity. Route to ledger.

### T5 — Mesh tab card binding leaves quality-report part scope implicit

RFC 0034 §Proposal 4 and §Acceptance 4 wire `mesh_diagnostics_lines_from_state`
and `mesh_package_view_model` into the Mesh tab. The controller
already returns per-part diagnostics keyed by part name (`hull`,
`deck`) in `mesh_package_view_model(...).diagnostics` (lines 379-399)
and accepts a `part="hull"` argument for the live diagnostics helper
(`mesh_diagnostics_lines_from_state`, lines 309-335).

The current Mesh tab cards in `kayakgen/ui/web/app.py:788-819` render
two structurally identical "Hull diagnostics" and "Deck diagnostics"
cards plus the package readiness card. RFC 0034 does not say how the
two helpers are split across those cards — specifically:

- Whether "Hull diagnostics" should bind to
  `mesh_diagnostics_lines_from_state(state, part="hull")` (live mesh
  diagnostics) or to the manifest's `hull` quality-report data when a
  package is selected.
- Whether welded-primary counts and warnings displayed in the package
  readiness card should be the per-part summary from the manifest or
  a re-evaluation from current state.

Both interpretations are valid; the difference is observable in the
case where the user mutates sliders but has not rebuilt the package.

Recommendation for ledger: when no `mesh_package_ref` is set, bind
diagnostics cards to `mesh_diagnostics_lines_from_state(...)` live;
when a package is selected, prefer the manifest's quality-report data
and label staleness explicitly. Acceptance criteria mention "welded
primary counts" and "existing readiness vocabulary" so either choice
satisfies them, but the ledger should pick one to keep tests
deterministic.

Severity: implementation-scope ambiguity. Route to ledger.

### T6 — RFC 0033 §"Acceptance Criteria" still names "`uncalibrated_comparative` chip on every `Rt`" but RFC 0034 §Proposal 3 says "the card keeps the chip"

RFC 0033 acceptance criterion `Resistance card carries the persistent
caption "Raw comparative filter; not final prediction." and tags every
`Rt` value with the `uncalibrated_comparative` claim chip` is stricter
than RFC 0034 §Proposal 3's `the card keeps the
uncalibrated_comparative chip and raw comparative warning`. The
current static card carries one chip at the card scope (`kayakgen/ui/web/app.py:782-786`).

When `resistance_table_view_model` is wired into the card per RFC
0034 §Proposal 3, the implementer needs to decide whether the chip is
attached per-row (matching RFC 0033's "every `Rt` value") or remains
at card scope (matching the RFC 0034 phrasing). The data model
supports both: `ResistanceMetadata.claim_state` is a single
card-scope value and `resistance_table_view_model` returns
`metadata` once at top level (`kayakgen/ui/web/controllers.py:253-258`),
so the per-row chip would simply re-render the same value.

Recommendation for ledger: keep the chip at card scope to match the
existing landed behavior and `tests/test_web_browser.py:307-397`
acceptance copy, but ensure that for any future per-row claim variance
(e.g., RFC 0012 calibration acceptance) the chip moves to per-row.
Card-scope rendering is the safer near-term default; RFC 0034 should
be read as relaxing the RFC 0033 per-`Rt` wording rather than
contradicting it.

Severity: cosmetic / wording. Route to ledger.

## Acceptance Criteria Coverage Assessment

- **§Acceptance 1 (preset reseed + narrow + auto-`custom`)** — covered
  by §Proposal 1; needs T4 clarification on "manual edit" and range
  reversal during ledger.
- **§Acceptance 2 (validity badge string set)** — covered by
  §Proposal 2; needs T3 clarification on the `_classify`-vs-RFC-string
  mismatch.
- **§Acceptance 3 (resistance card from read model)** — fully covered;
  T6 is wording-only.
- **§Acceptance 4 (mesh tab from live diagnostics + readiness)** —
  covered by §Proposal 4; needs T5 clarification on live-vs-manifest
  binding when a package is selected.
- **§Acceptance 5 (Export menu full set with honest unavailable
  states)** — covered by §Proposal 5; T1 highlights three undefined
  behaviors the ledger must pin.
- **§Acceptance 6 (forbidden-copy tests + browser acceptance)** —
  covered by §Proposal 6; T2 highlights the missing permitted-negation
  enumeration.
- **§Acceptance 7 (docs/changelog describe only current safe
  behavior)** — covered by §Goals last bullet and §Proposal coverage of
  the export menu's "disabled or clearly unavailable" framing.

## Scope Hygiene

### Missing scope

None blocking. The follow-up enumerates exactly the workflow 0044
final-review F1–F6 follow-up items. The cosmetic F7 mismatch is
correctly excluded (the patch summary already lives at
`striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md` and
is now historical). F8 (desktop region/test-id parity) is correctly
restated as an explicit deferral in §Non-Goals.

### Overbroad scope

None. RFC 0034 keeps RFC 0033's no-new-backend-capability boundary,
names the deferrals (`§Non-Goals`) consistent with the ledger's
explicit deferral list, and routes Mesh package authoring through the
§"Open Questions" section rather than promoting it.

The remediation packet (`REMEDIATION.md > Caveats`) is explicit about
leaving Hydro JSON / Stability JSON / Mesh package implementation
choices to first-pass reviewers and the ledger; T1 is the
implementation-scope finding that captures this.

### Domain boundaries

RFC 0034 does not touch domain meaning. The `Advisory` value object,
claim-state enum, mesh-readiness enum, and resistance metadata stay
unchanged; the RFC §"Domain Modeling" section says so explicitly.
This matches the workflow 0044 ledger's "Required Implementation
Guidance" boundary and the RFC 0031 advisory compatibility constraint.

## Concrete Source References

- `docs/rfcs/0034-workspace-ui-follow-up.md` — RFC under review.
- `docs/rfcs/0033-workspace-ui-rework.md:55-72` (§Goals), `:280-285`
  (§8 forbidden-claim guard), `:299-335` (acceptance criteria).
- `striatum/0044-workspace-ui-rework/final/FINAL_REVIEW.md:18-94`
  (findings F1–F8), `:172-198` (residual risk).
- `striatum/0044-workspace-ui-rework/ledger/FINDINGS.md:65-263`
  (priorities), `:312-326` (explicit deferrals).
- `striatum/0044-workspace-ui-rework/implementation/PATCH_SUMMARY.md:81-91`
  (explicit deferrals, including no web-side mesh authoring API).
- `striatum/0045-workspace-ui-follow-up/review_remediation/REMEDIATION.md:11-49`
  (verdict routing clarification + export behavior caveats).
- `docs/workflows/0045-workspace-ui-follow-up/workflow.json:50-181`
  (job graph, cycles, write scopes).
- `kayakgen/ui/web/app.py:613-695` (preset radio + static badge),
  `:778-786` (static resistance card), `:788-819` (static mesh cards),
  `:623-632` (toolbar Export STLs only).
- `kayakgen/ui/web/controllers.py:200-259`
  (`resistance_table_view_model`), `:262-306` (`evaluation_summary`),
  `:309-335` (`mesh_diagnostics_lines_from_state`), `:338-411`
  (`mesh_package_view_model`), `:521-533` (`stl_bytes_for_part`),
  `:1425-1436` (REST route registrations — no Hydro/Stability/mesh
  JSON routes today).
- `kayakgen/ui/desktop.py:362-376` (`_classify`), `:395-396` (preset
  decoration).
- `kayakgen/ui/theme.py:226-232` (unused
  `validated_design_fitness` chip vocabulary entry — relevant to T2).
- `kayakgen/model/classes.py:23-94` (`KayakClass` ranges/defaults used
  by §Proposal 1/§Acceptance 1).
- `tests/test_web_layout.py:94-100` (current forbidden-string
  assertion footprint — narrower than RFC 0033 §8 set per F6).

## Commands and Checks Run

- Direct file reads for the workflow packet, RFC 0033, RFC 0034, the
  workflow 0044 final review, ledger, and patch summary, plus the
  remediation packet for this follow-up.
- Targeted greps against `kayakgen/ui/` for `_classify`, the §8
  forbidden-copy strings, current export endpoint definitions, and
  the existing read models (`resistance_table_view_model`,
  `mesh_diagnostics_lines_from_state`, `mesh_package_view_model`,
  `evaluation_summary`).
- Cross-checked the workflow.json job graph, cycle policy, and write
  scopes to confirm `review_traceability` lands only the artifact at
  `striatum/0045-workspace-ui-follow-up/traceability/REVIEW_TRACEABILITY.md`.
- No Striatum mutation commands were run, no commits were made,
  `.striatum/` was not touched, no runtime code or tests were edited,
  and no author/byline metadata was written into this artifact.

## Sub-Agent and Parallel-Helper Use

This pass used parallel file reads and greps from the main session
rather than spawning helper subagents — the traceability surface (one
RFC, one predecessor RFC, one final review, one ledger, one patch
summary, one remediation, and ~5 implementation source files) fit
inside the main context, and the workflow packet only requested
maximal helper use "if available." Parallel tool calls were used to
read independent source/test/doc files concurrently. No background
agents, monitors, or schedules were started.
