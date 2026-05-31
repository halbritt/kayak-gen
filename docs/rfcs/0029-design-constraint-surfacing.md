# RFC 0029: Design Constraint Surfacing and Validity Metadata

Status: superseded by RFC 0031 (closed by RFC 0064)
Date: 2026-05-13
Context: closes deferred RFC 0006 GUI/web/CLI surfacing and validity metadata;
source reference is `docs/design/kayak_hull_design_constraints.md`.

## Problem

RFC 0006 adopted canonical kayak and surfski design ranges, presets, waterline
beam, and a hydrostatics read model. The implementation now has package-level
presets and advisory checks, but the user-facing validity story is incomplete:

- Some limits are enforced by model validation, some are advisory, and some
  shape parameters are named but not yet honored by the loft.
- The desktop GUI, web UI, CLI, sweep output, and reports do not yet expose the
  same validity metadata.
- Class presets can seed values, but warnings for out-of-class or
  cross-parameter combinations need consistent wording.
- Future shape parameters such as rocker, deadrise, chine radius, and LCB need
  stable unsupported/deferred states so users do not mistake stored fields for
  full geometry controls.

## Goals

- Define a shared validity metadata model with `enforced`, `advisory`, and
  `unsupported` states.
- Surface the same design warnings in CLI JSON, desktop GUI, web UI, sweeps,
  and comparison reports.
- Preserve class presets while making out-of-class combinations visible rather
  than silently accepted.
- Define how future shape parameter boundaries appear before they are fully
  honored by geometry.
- Keep parameter-space guidance tied to the constraints document rather than
  restating all domain research in UI code.

## Non-Goals

- Hard-locking users into class presets.
- Completing rocker, deadrise, chine radius, flare, or full LCB-driven volume
  redistribution.
- Turning advisory constraints into proof of seaworthiness, fitness, or race
  performance.
- Rewriting the desktop or web layout beyond adding consistent validity
  surfaces.

## Proposal

### 1. Validity levels

Every surfaced constraint is classified as one of three levels:

- `enforced`: invalid input that model validation rejects or live-clamps. This
  includes numeric type/range errors and invariants such as
  `beam_wl_m <= beam_oa_m`.
- `advisory`: plausible but suspicious or outside a selected class envelope.
  This includes L/B waterline warnings, Cp envelope warnings, displacement
  sanity checks, and class preset drift.
- `unsupported`: accepted/stored for schema continuity but not fully honored by
  the current geometry, evaluator, UI, or solver pipeline.

Metadata records include:

- `code`: stable machine-readable identifier.
- `level`: `enforced`, `advisory`, or `unsupported`.
- `severity`: `error`, `warning`, or `info`.
- `surface`: list of affected surfaces such as `model`, `cli`, `desktop`,
  `web`, `sweep`, `report`, or `cfd`.
- `message`: concise user-facing text.
- `source`: constraints document section or RFC identifier.
- `parameters`: field names involved in the finding.

### 2. Enforced constraints

The model boundary owns enforced constraints. UI code may preemptively clamp or
disable controls, but CLI validation remains authoritative.

Required enforced constraints include:

- `beam_wl_m <= beam_oa_m`.
- Positive dimensions for length, beam, draft, and deck height.
- `Cp`, `Cm`, rake fields, flatness fields, and box-ratio fields inside their
  accepted numeric domains.
- No unsupported solver/profile promotion based on advisory-only metadata.

Errors should be serializable in the same validity format when possible so
batch workflows can aggregate failures.

### 3. Advisory constraints

Advisory checks are warnings, not blockers. Required advisory families:

- Global design-space warnings from constraints section 9, including length, beam,
  draft, and Cp envelopes.
- L/B waterline bands from constraints section 4 and class-specific ranges.
- Displacement sanity bands from constraints section 7.
- Preset drift warnings when a selected class no longer matches the current
  hull.
- Exploratory-resistance and raw-CFD warnings when reports display results
  outside accepted calibration/validation gates.

Desktop and web should render these as non-modal warning/info surfaces. CLI,
sweep, and comparison outputs should include them as structured metadata.

### 4. Unsupported and future shape parameters

Fields that exist for schema or RFC continuity but are not fully honored must
carry explicit unsupported metadata until implemented. Current examples include:

- `LCB_frac` as a stored/read-model value not yet a complete loft volume
  redistribution control.
- `rocker_bow_m` and `rocker_stern_m` where present but not yet complete
  independent rocker geometry.
- Future deadrise, chine radius, flare, and section archetype controls before
  they alter generated sections.

Unsupported does not mean invalid. It means "stored or reserved, but not a full
geometry/evaluation control yet." UI labels, CLI JSON, and reports should make
that distinction.

### 5. Surface parity

All primary surfaces consume the same validity metadata:

- CLI `evaluate`, `stability`, `mesh-check`, `mesh-package`, `sweep`, and
  `compare` output JSON include validity records when available.
- Desktop GUI shows current warnings near metrics without requiring users to
  inspect stdout.
- Web UI shows the same warning set and does not diverge from desktop wording.
- Preset controls in desktop and web show class drift and out-of-class warnings
  consistently.
- Reports summarize warning counts and preserve per-candidate records.

## Acceptance Criteria

- A shared validity metadata structure exists and is covered by tests.
- Enforced, advisory, and unsupported levels are documented in code-facing and
  user-facing docs.
- `beam_wl_m > beam_oa_m` remains an enforced error or live-clamped state, with
  CLI validation as the final authority.
- L/B waterline, Cp, displacement, and class preset warnings are surfaced in CLI
  JSON and at least one interactive UI, then parity gaps are tracked explicitly.
- Desktop and web use the same warning codes/messages for equivalent hulls.
- Stored-but-deferred shape fields carry unsupported metadata until the geometry
  actually honors them.
- Sweeps and comparison reports preserve validity metadata for downstream
  filtering without treating advisory warnings as hard failures.

## Open Questions

- Should advisory warnings have numeric severity scores for optimization
  ranking? Lean: defer; codes and levels are sufficient for the UI/reporting
  closure this RFC targets.
- Should interactive UIs allow users to hide repeated warnings? Lean: allow
  dismissal per current hull state only; warnings reappear when affected
  parameters change.

## Implementation Path

1. Add a small validity metadata type and a shared constraint-evaluation
   function near the model/evaluator boundary.
2. Convert existing advisory checks to emit stable codes and sources.
3. Wire CLI JSON, sweeps, comparison reports, desktop metrics, and web metrics
   to the shared metadata.
4. Add unsupported metadata for reserved shape fields.
5. Add parity tests that compare CLI/desktop-helper/web-helper warning records
   for representative hulls and class presets.
