# RFC 0064: Outstanding-RFC cleanup

Status: landed
Date: 2026-05-31
Context: Triggered by the post-RFC-0063 index review. As of 2026-05-31
the RFC index carries 14 RFCs whose status is either `partial` or
`proposed` even though the work they describe has either (a) already
landed at the safe-slice + downstream successor coverage that the
original RFC required, (b) been explicitly superseded by a later RFC
that took over the residual, or (c) been shelved by an operator
decision recorded in `docs/DECISION_LOG.md`. The accumulated
ambiguity makes "what's actually open?" hard to answer at a glance.

Stability-rig work (RFC 0043 stage 4 + RFC 0056 fixture promotion)
remains deferred per the operator's standing decision; this RFC does
**not** touch those.

## Problem

A reader of `docs/rfcs/README.md` cannot tell at a glance which of the
14 non-cleanly-landed RFCs represent genuinely open work versus
administrative drift. Each individual RFC file's `Status:` line is
stale relative to the README, and the README's claims do not point at
the successor RFC or decision-log row that actually carries the
residual. The cleanup-by-attrition pattern (each RFC's residual gets
absorbed by an unrelated later RFC without flipping the predecessor's
status) is a known antipattern flagged by RFC 0059's docs-decision-drift
audit lane.

## Goals

- Disposition every non-cleanly-landed RFC except 0043 / 0056
  (stability rig — deferred) and 0001 (template).
- For each, name the successor RFC or decision-log row that carries
  the residual (or declare the RFC complete-as-stated if the
  safe-slice met the original goal).
- Flip the `Status:` line on each dispositioned RFC file and update
  the matching `docs/rfcs/README.md` index row so reader and
  authoritative file agree.
- Leave the codebase byte-stable: no code change is in scope. The
  cleanup is purely doc-and-index hygiene.

## Non-Goals

- Re-opening or extending any of the dispositioned RFCs.
- Stability-rig work (RFC 0043 stage 4, RFC 0056 stage-4 promotion)
  stays deferred per the operator's standing decision.
- Calibration data acquisition itself (D006) is still open as an
  operator-action follow-up; RFC 0054 already owns the tooling, so
  the data-acquisition tracking lives in the decision log, not in a
  separate RFC.
- Reopening D023 (hosted public demo deferred indefinitely).

## Proposal

The fourteen dispositions below close every open RFC except the
stability-rig pair. Each row is verified against the codebase by the
2026-05-31 three-agent fan-out (residual checks against
`kayakgen/...` paths and recorded in this conversation's task
trail). Dispositions:

| RFC | Topic | Final Status | Rationale |
|-----|-------|--------------|-----------|
| 0004 | Plumb bow (`bow_rake`) | superseded by RFC 0028 | safe-slice `bow_rake` landed on `Hull`; exact plumb-stem closure semantics (independent `stern_rake`, cap construction, diagnostics) owned by RFC 0028 which itself is now complete |
| 0006 | Hull design constraints | landed | `kayakgen/model/classes.py` carries the four canonical class presets; `beam_wl_m` validation lives on `Hull`; richer parameter-rail surfacing absorbed by RFC 0031 (validity metadata), RFC 0048 (distribution_v2 controls), and RFC 0061 (`HullParameterMetadata` slider labels) |
| 0008 | Portable web frontend via Trame | superseded by RFC 0032 | web-analysis safe-slice landed in `kayakgen/ui/web/`; hosted-public-demo boundary owned by RFC 0032; D023 closed the hosted operation question indefinitely |
| 0009 | Sweep and candidate run records | superseded by RFC 0057 | `SweepSpec` / `CandidateRecord` / `SweepRunRecord` + the deterministic runner landed; `pending` candidate lifecycle + generative-jobs records absorbed by RFC 0057; objective + optimizer integration in RFC 0044 / 0047 |
| 0012 | Resistance model calibration | superseded by RFC 0054 + D006 | calibration-campaign tooling (`kayakgen calibration` sub-app + tank/inclining/AcceptedFitRecord schemas) landed in RFC 0054; physical kayak-envelope measured-resistance source still gated on D006 author outreach (tracked in `docs/research/CALIBRATION_DATA_FINDINGS_2026-05-16.md`) |
| 0014 | Generalized trim + high-angle GZ | superseded by RFC 0043 | trim-equilibrium solver + StabilityResult trim fields + CLI surface landed; high-angle `GZCurve` unavailability boundary and downstream surfacing owned by RFC 0043 |
| 0015 | CFD solver dispatch and job artifacts | superseded by RFC 0041 | `CfdJobSpec` / `CfdRunRecord` / local job-store + `kayakgen cfd` subcommands landed; real OpenFOAM-v2512 `interFoam` opt-in succeeded path owned by RFC 0041 |
| 0017 | First real CFD adapter | superseded by RFC 0041 | already noted in the README; `Status:` line flipped to match |
| 0018 | Web CFD job routes | landed | `/api/cfd/...` routes + browser CFD panel landed; hosted workers / SSE live progress are explicit non-residuals per D023 (no hosted demo) |
| 0019 | Resistance calibration fixtures | superseded by RFC 0042 | already noted in the README; `Status:` line flipped to match |
| 0020 | High-angle GZ and secondary stability | superseded by RFC 0024 + RFC 0043 | already noted in the README; `Status:` line flipped to match |
| 0028 | Plumb-stem closure semantics | landed | independent `stern_rake` + cap construction (`_ring_cap_center` in `kayakgen/eval/closed_volume/generated_body.py`) + plumb-aware diagnostics complete; manufacturing thickness / watertight promotion are explicit non-residuals |
| 0029 | Design constraint surfacing | superseded by RFC 0031 | already noted in the README; `Status:` line flipped to match |
| 0030 | Web hosted browser acceptance | deferred per D023 | public hosted demo deferred indefinitely; no successor planned |
| 0033 | Workspace UI rework | superseded by RFC 0034 + RFC 0035 | safe-slice three-region web shell + semantic theme + advisory record landed; dynamic presets + validity badges + read-model wiring absorbed by RFC 0034; later cleanup by RFC 0035 |
| 0040 | Closed-volume solver readiness roadmap | superseded by RFC 0041 + RFC 0045 | generated-body hardening + snappyHexMesh evidence harness (opt-in env-gated) landed; real solver path picked up by RFC 0041; ordinary-package readiness promotion via mesh-evidence binding owned by RFC 0045 |
| 0042 | Resistance calibration fixture successor | superseded by RFC 0054 + D006 | source-review packet validators + Edinburgh acquisition + extractor + D025 promotion to `validation_fixture` landed; calibration-fixture promotion still gated on D006 measured kayak-envelope source; tooling tracked by RFC 0054 |

Eight RFCs flip to `superseded by RFC NNNN` with a single successor
named; four flip to `superseded by RFC NNNN + RFC MMMM` where two
successors share the residual; two flip to `superseded by RFC NNNN + D NNN`
where tooling lives in a later RFC but a decision-log row carries
the operator-action half; one (RFC 0030) flips to `deferred per
D023`. Three (RFC 0006, 0018, 0028) flip to plain `landed` because
the safe-slice or local-only scope was the goal — no successor took
over because nothing was left to take over.

## Acceptance Criteria

- After this RFC lands, the only non-`landed` / non-`superseded` /
  non-`deferred` rows in `docs/rfcs/README.md` are RFC 0043 (stage 4
  stability) and RFC 0056 (fixture promotion gated on stage 4).
  Verify by `grep -E "^\| \[0[0-9]{3}" docs/rfcs/README.md | grep -ivE "landed|superseded|deferred|template"`.
- Every dispositioned RFC's file `Status:` line agrees with its row
  in `docs/rfcs/README.md` (same status keyword, same successor
  citation).
- No code change. `git diff --stat` for this RFC's landing covers
  only `docs/rfcs/*.md` files.

## Open Questions

- Should RFC 0012 + RFC 0042 keep a separate "deferred — gated on
  D006" line in the index, or is the `superseded by RFC 0054 + D006`
  formulation enough? My recommendation: the latter, because the
  decision-log already carries the open D006 tracking surface; a
  second open RFC row is duplicate ambient state. The decision is
  not load-bearing — flip later if a reader misses it.

## Implementation Path

- Step 1 — Flip `Status:` on each dispositioned RFC file
  (`docs/rfcs/00XX-*.md`) to match the disposition table above.
- Step 2 — Flip the matching row in `docs/rfcs/README.md` to the
  same status keyword + successor citation.
- Step 3 — Add this RFC 0064 row to the README index.
- Step 4 — Update `CHANGELOG.md` with one line: "RFC 0064 landed —
  burned down 14 outstanding RFC dispositions; stability-rig pair
  (0043, 0056) stays deferred".
- No CI gates beyond the standard markdown lint; no pytest run.

## Domain Modeling

This RFC adds no domain concepts. It is a **boundary clarification**
(per `docs/DDD.md § "Adding to the model"`) on the documentation
layer — the RFC-index aggregate becomes self-consistent with the
RFC-file aggregate. The decision-log surface (`docs/DECISION_LOG.md`)
remains the authoritative carrier for operator-action follow-ups
(D006 calibration data, D023 hosted-demo deferral).
