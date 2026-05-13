---
schema_version: "striatum.finding.v1"
artifact_kind: "finding"
verdict_intent: "accept_with_findings"
---

# Traceability review — workflow 0042

Workflow: `0042-design-constraint-surfacing-revision`
Job: `review_traceability`
Role: `reviewer_traceability`
Scope: RFC 0031 ↔ RFC 0029 ↔ RFC 0006 partials ↔ constraints document ↔
implementation surfaces ↔ tests ↔ workflow remediation routing.

Verdict intent: accept_with_findings

## Summary

RFC 0031 cleanly supersedes RFC 0029 as the workflow 0042 implementation
target. The accepted slice maps to the still-open RFC 0006 surfacing partials
and to existing constraints-document bands without expanding into deferred
geometry or solver work. Workflow 0042 has a declared review-remediation route
that addresses the explicit workflow-0040 process-level blocker called out in
RFC 0031. There is a traceable path from the prior workflow-0040 blocker to
actionable implementation and re-review without overstating unimplemented
work. Findings below are non-blocking guidance for the ledger and implementer.

## Mapping

### RFC 0031 supersession of RFC 0029

- RFC 0031 body declares "supersedes RFC 0029 as the implementation target
  for the design-constraint surfacing slice; RFC 0029 remains background"
  (`docs/rfcs/0031-design-constraint-surfacing-revision.md:5-8`).
- RFC 0031 header is now `Status: accepted implementation target` and
  §1 "Supersession boundary" repeats the scope split
  (`docs/rfcs/0031-design-constraint-surfacing-revision.md:1-4,56-65`).
- RFC index marks RFC 0031 as `accepted implementation target` and RFC 0029
  as `proposed background, superseded by RFC 0031 for implementation`
  (`docs/rfcs/README.md:45,47,119-123`).
- `review_remediation` recorded the supersession-status repair as a
  scaffold remediation
  (`striatum/0042-design-constraint-surfacing-revision/review_remediation/REMEDIATION.md:27-38`).

This boundary is consistent across RFC body, index, and remediation log.

### RFC 0031 ↔ RFC 0006 partials

RFC 0006's workflow-0019 status note enumerates the remaining partials
(`docs/rfcs/0006-design-constraints.md:15-27`):

| RFC 0006 partial | RFC 0031 disposition |
| --- | --- |
| Yellow dismissible desktop banner UX | Out of scope — RFC 0031 Non-Goal: "Redesigning the desktop or web layouts" (`docs/rfcs/0031-...md:48-49`); §5 surfaces wording only. |
| Manual visual confirmation | Out of scope — RFC 0031 does not touch geometry or visualization. |
| Shared L/B_wl / Cp / displacement advisories | In scope — §3 advisory family explicitly cites these (`docs/rfcs/0031-...md:88-91`). |
| Coherent web-side clamp/advisory parity | In scope — §5 "Desktop and web warning text … derived from the same shared codes/messages for equivalent hulls" (`docs/rfcs/0031-...md:117-123`). |
| Future shape parameters (rocker, deadrise, chine radius, fully honoured LCB_frac) | In scope as `unsupported` records — §3 lists `LCB_frac`, `rocker_bow_m`, `rocker_stern_m` (`docs/rfcs/0031-...md:92-100`). Deadrise/chine radius/flare remain deferred per §0 Non-Goals. |

Deferrals (geometry, solver, calibration, GZ, optimizer scoring, layout
redesign) are explicit in `docs/rfcs/0031-...md:42-52`. They are echoed in
`docs/workflows/0042-design-constraint-surfacing-revision/RUNBOOK.md:31-33`
and `review_remediation/REMEDIATION.md:55-68`.

### Constraints-document sections

The constraints document continues to carry the load-bearing numbers RFC
0031 surfacing must agree with:

- §3 length envelopes — class presets at
  `kayakgen/model/classes.py:53-94` round-trip these.
- §4 L/B_wl bands — `kayakgen/model/advisory.py:46-49` enforces 8.0–15.5
  guidance strings.
- §7 displacement bands — `kayakgen/model/advisory.py:56-60` uses
  0.075–0.180 m³ at seawater density.
- §8 Cp envelope — `kayakgen/model/advisory.py:51-54` uses 0.50–0.65.
- §9 generator parameter envelope — pinned in
  `docs/rfcs/0006-design-constraints.md:84-114` and inherited by the class
  preset ranges.

RFC 0031 §3 refers to these guidance bands collectively but does not
enumerate section numbers per finding family. The existing docstring on
`kayakgen/model/advisory.py:33-39` is the de facto section register.

### Surface requirements

RFC 0031 §5 "Surface expectations" calls out five surfaces (`docs/rfcs/
0031-...md:114-125`). Current state in the package:

| Surface | Today | RFC 0031 expectation |
| --- | --- | --- |
| `kayakgen evaluate` CLI JSON | Not yet emitting structured design-validity records (no validity hits found in `kayakgen/eval/`). | Additive `design_validity` in evaluation serialization (RFC §5 first bullet; Acceptance §3 bullet 3). |
| Web evaluation payload | `kayakgen/ui/web/controllers.py:106-121,148-170` exposes `advisory_warnings` strings only. | Additive structured records derived from shared evaluator (RFC §5 bullet 2). |
| Desktop warning text | `kayakgen/ui/desktop.py:325-360` renders `advisory.warnings` strings directly. | Same shared codes/messages for equivalent hulls (RFC §5 bullet 3). |
| Sweep candidate records | `kayakgen/search/sweep.py` candidate records do not currently carry advisory metadata. | Per-candidate additive design-validity (RFC §5 bullet 4). |
| Comparison summaries/reports | `kayakgen/search/compare.py` does not currently surface advisory records. | Preserve advisory records and warning counts without treating them as Pareto failures (RFC §5 bullet 5). |

All five surfaces remain to be wired by the implementer; the workflow's
`implement_findings` job covers them under
`docs/workflows/0042-design-constraint-surfacing-revision/workflow.json:139-159`.

### Tests

Existing coverage that the RFC 0031 slice must extend or preserve:

- `tests/test_classes.py` — preset round-trip and advisory presence.
- `tests/test_web.py` — web-side advisory payload presence.
- `tests/test_hull_roundtrip.py` — model validation invariants.

RFC 0031 §8 Implementation Path lists "focused tests for schema stability,
advisory parity, class defaults, invalid-beam enforcement, sweep/report
propagation, and unsupported fields" (`docs/rfcs/0031-...md:172-174`).
Acceptance criteria (`docs/rfcs/0031-...md:129-148`) explicitly require:

- Shared validity type/evaluator with focused tests.
- `beam_wl_m > beam_oa_m` enforced or live-clamped, with CLI authoritative
  — currently enforced at `kayakgen/model/hull.py:73-81`.
- Sweep and comparison-report propagation tests.
- Non-neutral reserved-field `unsupported` record tests.

The expected test surface is reachable from the existing structure; no new
test framework is required.

### Workflow remediation routing

RFC 0031 §0 Problem statement cites the workflow-0040 hazard: "first-pass
review jobs could return `needs_revision`, but the workflow had no declared
review-stage remediation route" (`docs/rfcs/0031-...md:17-20`).

Workflow 0042 fixes this:

- `review_revision_policy.root_review_needs_revision: declared_cycle`
  (`docs/workflows/0042-.../workflow.json:51-54`).
- A `review_remediation` synthesis job runs first and emits a remediation
  artifact (`workflow.json:56-78`).
- Per-review cycles route `needs_revision` back to `review_remediation`
  with `max_iterations: 1`; `review_ops` carries `allow_same_lane: true`
  because both run on `codex` (`workflow.json:183-188`).
- `final_review → implement_findings` cycle covers final-gate revisions
  (`workflow.json:187`).

Workflow 0040 (`docs/workflows/0040-design-constraint-surfacing/workflow.
json:116-123`) only has a single final-review cycle and no remediation
node, confirming the gap RFC 0031 calls out.

Recent workflows 0033 and 0039 use the same single-final-cycle shape
(`docs/workflows/0033-...workflow.json:228-234`, `docs/workflows/0039-...
workflow.json:122-124`), so workflow 0042's `declared_cycle` pattern is a
deliberate addition for this slice rather than copy-paste drift.

### From 0040 blocker to actionable next steps

The path is:

1. Workflow 0040 scaffolded but never ran — `striatum/0040-design-
   constraint-surfacing/` is absent on disk and `SOURCES.md:23-26` notes
   the missing review artifacts.
2. RFC 0029 stayed `proposed background` while RFC 0031 narrowed the
   product slice and added the remediation route.
3. Workflow 0042 carries that route plus the three review lanes and the
   downstream ledger/implement/final jobs.
4. `review_remediation` has already published its packet
   (`striatum/0042-.../review_remediation/REMEDIATION.md`), so the three
   review lanes (this artifact among them) can publish independently.

The path is traceable. The accepted slice does not promise watertight
geometry, calibrated resistance, high-angle `GZ`, or solver dispatch
(consistent with `docs/USER_GUIDE.md:359-403`).

## Findings

### F1 — Pin constraints-document section references per finding family (advisory severity: warning)

RFC 0031 §3 lists finding families ("`L/B_wl`, `Cp`, and displacement
guidance from the constraints document") without naming the sections, while
`kayakgen/model/advisory.py:33-39` already cites §3/§4/§8/§9. The
implementer should keep the `source` field on each structured record
pinned to a constraints-document section (e.g., §4 for L/B_wl, §7 for
displacement, §8 for Cp) so the rationale travels with the record.

Correction needed (ledger/implementer): for each `code` in the new
`evaluate_design_validity()` output, set `source` to the explicit
constraints-document section (`docs/design/kayak_hull_design_constraints.
md` §3, §4, §7, §8, §9) or RFC identifier rather than a generic doc
pointer.

### F2 — Clarify "non-neutral" sentinels for unsupported reserved fields (advisory severity: warning)

RFC 0031 Open Question §2 leans toward emitting `unsupported` records when
a reserved field carries a non-neutral value, but the body §3 does not pin
sentinels. Current defaults are `LCB_frac = 0.50`, `rocker_bow_m = 0.0`,
`rocker_stern_m = 0.0` (`kayakgen/model/hull.py:58-60`). Workflow 0042's
ledger should pin: neutral means `LCB_frac == 0.50` and rocker fields
`== 0.0`; any other supplied value emits an `unsupported` record. Without
that pin, parity tests between desktop, web, CLI, and sweeps cannot be
written deterministically.

Correction needed (ledger): record the exact neutral values for
`LCB_frac`, `rocker_bow_m`, and `rocker_stern_m` so unsupported records
fire consistently across surfaces and tests.

### F3 — Keep solver/calibration warning channels separate from design-validity (advisory severity: warning)

Existing UI controllers concatenate `*advisory.warnings,
*resistance.metadata.warnings` (`kayakgen/ui/web/controllers.py:170`).
RFC 0031 scopes the new validity record set to design-side
enforced/advisory/unsupported guidance and does not subsume resistance
claim-gate or CFD raw-result warnings (Non-Goal: "Rewriting resistance
claim gates, CFD readiness semantics, …",
`docs/rfcs/0031-...md:46-49`). The implementer must not silently fold
`resistance.metadata.warnings` or `kayakgen.eval.claims`/`calibration`
records into the new `design_validity` channel.

Correction needed (implementer): keep `design_validity` records distinct
from solver/calibration warning streams; surfaces may render both but must
not blur the source.

### F4 — RFC 0006 desktop banner UX remains explicitly deferred (advisory severity: info)

RFC 0031 Non-Goal "Redesigning the desktop or web layouts"
(`docs/rfcs/0031-...md:48-49`) means the RFC 0006 yellow-dismissible-
banner UX (`docs/rfcs/0006-design-constraints.md:170-184`) does not close
under this workflow. The ledger should record this deferral so the RFC
0006 status note is not retroactively promoted from `partial` to
`landed`.

Correction needed (ledger): keep the RFC 0006 banner UX explicitly named
as deferred in the workflow 0042 OPERATOR_REPORT/ledger output; do not
restate RFC 0006 as fully landed when this slice closes.

### F5 — Constraints document §10 CFD-objective contract is not in scope (advisory severity: info)

RFC 0006 §5 references a `gz_curve` placeholder and a `Fn_at` reservation
in the hydrostatics read model (`docs/rfcs/0006-design-constraints.md:158-
168`). RFC 0031 does not extend or modify that contract — it only adds
the additive `design_validity` channel. The implementer should leave the
existing evaluation read model intact and not infer that closure of RFC
0031 closes the §10 CFD-objective contract (`docs/design/
kayak_hull_design_constraints.md:244-264`); that contract still depends
on RFC 0020/0023/0024 work that the AGENTS.md "current direction" note
keeps deferred (`AGENTS.md:77-90`).

Correction needed (implementer/final reviewer): the additive
`design_validity` keys must not change or replace existing hydrostatic /
resistance keys, and final-gate language must avoid implying §10 closure.

## Required actions

These belong in the ledger and should ride downstream rather than recycle
through `review_remediation`:

- Adopt F1 by pinning per-family `source` values to constraints-document
  sections.
- Adopt F2 by recording neutral sentinels for `LCB_frac`, `rocker_bow_m`,
  and `rocker_stern_m`.
- Adopt F3 by keeping solver/calibration warning channels distinct from
  `design_validity`.
- Adopt F4 by preserving the RFC 0006 banner-UX deferral in the operator
  report.
- Adopt F5 by leaving the hydrostatics read-model contract and §10
  CFD-objective scope unchanged.

## Residual risk

- **Surface drift over time.** Even with shared codes/messages, the
  desktop and web renderers can drift if either surface adds inline
  warning text that bypasses the shared evaluator. Parity tests (called
  out in RFC 0031 §8) mitigate this.
- **"Non-neutral" interpretation creep.** Without an explicit ledger pin
  (F2), future contributors may differ on which `LCB_frac` values count
  as user-supplied; this would silently change unsupported-record
  behavior.
- **Implicit promotion of RFC 0006.** Future PR descriptions may
  conflate "design-validity surfacing landed" with "RFC 0006 fully
  landed" (F4). Keeping RFC 0006 partial in the index until the banner
  UX and full LCB volume redistribution land is the safer posture.
- **Hidden geometry assumptions.** None observed in this slice; RFC 0031
  Non-Goals already exclude geometry, solver, calibration, and high-angle
  `GZ` work.

## Sub-agent and parallel help used

I used parallel file reads (no read-only sub-agents spawned) to load the
required references, the workflow definitions for 0040/0033/0039/0042,
the supporting `kayakgen/model/` and `kayakgen/ui/` modules, the existing
`tests/` inventory, the workflow-0042 prompts/roles directory, and the
already-published `review_remediation` artifact. Cross-checks covered the
RFC index status, the workflow.json edges and cycles, the advisory
implementation, and the absence of prior workflow-0040 review artifacts on
disk.
