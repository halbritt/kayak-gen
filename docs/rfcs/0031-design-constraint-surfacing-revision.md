# RFC 0031: Design Constraint Surfacing Revision

Status: accepted implementation target
Date: 2026-05-13
Context: supersedes RFC 0029 as the implementation target for the
design-constraint surfacing slice; RFC 0029 remains background for the broader
desired end state.

## Problem

RFC 0029 correctly identified the gap left by RFC 0006: the project has class
presets, waterline beam, and some advisory checks, but users still do not see a
consistent validity story across CLI, UI, sweep, and report surfaces.

The proposed RFC 0029 scope was too broad for one safe pass. It asked for full
surface parity, class drift, unsupported-field disclosure, sweep/report
propagation, desktop and web behavior, and structured metadata all at once.
Workflow 0040 also had a process-level hazard: first-pass review jobs could
return `needs_revision`, but the workflow had no declared review-stage
remediation route before the ledger and implementation jobs.

This RFC narrows the product slice so implementation can land without changing
geometry semantics, overclaiming future shape controls, or turning advisory
guidance into hard validation.

## Goals

- Define an additive structured design-validity metadata model.
- Preserve existing validation behavior and existing string warning behavior.
- Surface shared advisory and unsupported-state records from one model-facing
  evaluator.
- Make the first implementation pass cover CLI JSON, web payloads,
  desktop/web text parity, sweeps, and comparison reports without requiring UI
  redesign.
- Keep class-preset drift advisory and non-blocking.
- Make reserved fields visibly unsupported until they actually affect geometry
  or evaluation.
- Keep the implementation tied to
  `docs/design/kayak_hull_design_constraints.md` by section reference.

## Non-Goals

- Hard-locking hulls to class presets or advisory ranges.
- Implementing full rocker, deadrise, chine radius, flare, or LCB-driven
  volume redistribution.
- Rewriting resistance claim gates, CFD readiness semantics, closed-volume
  geometry, or solver dispatch.
- Adding optimizer scoring based on warnings.
- Redesigning the desktop or web layouts.
- Treating advisory warnings as proof of seaworthiness, fitness, or race
  performance.

## Proposal

### 1. Supersession boundary

RFC 0031 supersedes RFC 0029 as the implementation target. RFC 0029 remains a
useful statement of the broad destination, but this RFC is the accepted slice
for workflow 0042.

This RFC revises only the remaining RFC 0006 surfacing partials: shared
advisory text, class drift visibility, CLI/web/desktop/report propagation, and
unsupported-field disclosure. It does not revise the canonical class presets or
the constraints document itself.

### 2. Design-validity records

Add an append-only structured metadata record near the model/evaluator
boundary. Required fields:

- `code`: stable machine-readable identifier.
- `level`: `enforced`, `advisory`, or `unsupported`.
- `severity`: `error`, `warning`, or `info`.
- `message`: concise user-facing text.
- `source`: constraints-document section or RFC reference.
- `parameters`: hull fields involved in the finding.

Optional fields may include `value`, `bounds`, `selected_class`, and
`surface`. Unknown future fields must not make older consumers fail.

### 3. Finding families

The first implementation pass must support these families:

- Enforced model invariants already owned by `Hull`, including positive
  dimensions and `beam_wl_m <= beam_oa_m`. CLI validation remains
  authoritative. This RFC does not loosen Pydantic validation and does not
  require duplicating every Pydantic error as structured metadata.
- Advisory bands already represented by `design_advisory()`: `L/B_wl`, `Cp`,
  and displacement guidance from the constraints document.
- Class preset drift when a selected class is known and the hull leaves that
  class envelope.
- Unsupported reserved controls when a non-neutral value is supplied for a
  field that is stored but not fully honoured by current geometry or
  evaluation. Current examples are `LCB_frac`, `rocker_bow_m`, and
  `rocker_stern_m`.

Unsupported does not mean invalid. It means the value is accepted for schema
continuity or future work, but users must not read it as a full geometry or
hydrostatics control yet.

### 4. Compatibility

Existing warning strings remain valid. `design_advisory()` may become a
compatibility wrapper over the new evaluator, but callers that currently expect
`DesignAdvisory.warnings` must continue to work.

Structured metadata is additive in JSON. Existing consumers can ignore it.
Batch workflows must not start failing because advisory or unsupported records
are present.

### 5. Surface expectations

The first implementation pass must wire shared design-validity metadata through
these surfaces:

- `kayakgen evaluate` JSON for valid hulls.
- The web evaluation payload used by compact analysis views.
- Desktop and web warning text, derived from the same shared codes/messages for
  equivalent hulls.
- Sweep candidate records for completed candidates.
- Comparison summaries/reports so downstream filtering can see warning counts
  and records without treating advisory findings as Pareto failures.

Invalid input remains an input failure. A hull with `beam_wl_m > beam_oa_m`
must still be rejected by model validation or live-clamped by an interactive UI
before validation, with CLI validation as the final authority.

## Acceptance Criteria

- A shared design-validity type and evaluator exist with stable codes and
  focused tests.
- Existing string advisory warnings remain compatible.
- `kayakgen evaluate` and the web evaluation payload include design-validity
  metadata for valid hulls.
- Desktop and web warning text is derived from the same shared codes/messages
  for equivalent hulls.
- Sweeps preserve per-candidate design-validity metadata for completed
  candidates.
- Comparison reports preserve candidate design-validity metadata and warning
  counts without treating advisory findings as hard Pareto failures.
- Class preset defaults remain advisory-quiet.
- Representative out-of-range hulls emit structured advisories for `L/B_wl`,
  `Cp`, and displacement.
- Non-neutral reserved fields emit `unsupported` records until their
  geometry/evaluator support lands.
- Tests prove `beam_wl_m > beam_oa_m` remains enforced by model validation or
  UI clamping, with CLI validation still authoritative.

## Open Questions

- Should warning records eventually include numeric optimization penalties?
  Lean: defer. Stable codes are enough for surfacing and filtering.
- Should unsupported records appear when reserved fields hold neutral defaults?
  Lean: no. Emit them when the user supplies a non-neutral value or when a
  surface would otherwise imply the control is fully honoured.
- Should class drift be computed against every class or only a selected class?
  Lean: selected class first; automatic classification can be a later UX slice.

## Implementation Path

1. Add `kayakgen/model/validity.py` with `DesignValidityFinding`,
   `DesignValidityReport`, and `evaluate_design_validity(...)`.
2. Convert `design_advisory()` into a compatibility wrapper where practical,
   preserving current warning strings.
3. Add additive `design_validity` output to `EvaluationResult` or the nearest
   stable evaluation serialization boundary.
4. Wire CLI `evaluate` and web evaluation payloads.
5. Update desktop/web metrics helpers to render warning text from shared
   metadata.
6. Extend sweep and comparison records with additive validity metadata.
7. Add unsupported records for non-neutral reserved shape fields.
8. Add focused tests for schema stability, advisory parity, class defaults,
   invalid-beam enforcement, sweep/report propagation, and unsupported fields.
