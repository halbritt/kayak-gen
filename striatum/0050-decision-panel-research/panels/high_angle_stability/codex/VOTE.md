---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: panelist-codex-gpt-5.5-007
schema_version: striatum.synthesis.v1
kind: synthesis
logical_name: vote
date: 2026-05-14

# High-Angle Stability Model Vote

Vote: Fixed-Trim Generated-Body V1

## Decision Sentence

Accept a first real generated-kayak high-angle `GZ` model only as a fixed-upright-trim hydrostatic comparator over `generated_hull_plus_deck_closed_body_v1`: require passing RFC 0024 generated-body diagnostics, a default `0..90 deg` by `5 deg` heel grid with caller-supplied monotonic grids echoed exactly, hull-fixed passive load-case CG, per-heel sinkage/displacement solving, closed waterline clipping/capping diagnostics, per-point residual/status metadata, grid-bounded summaries, sealed-deck/flooding warnings, and explicit no-safety/no-seaworthiness/no-design-fitness language; keep all real generated-kayak `GZ` arrays and summaries unavailable until those gates are implemented and tested.

## Evidence

- The local product boundary is not ambiguous: PRD, user guide, roadmap, RFC 0043, and the current evaluator all say real generated-kayak high-angle `GZ`, `GZ_max`, range of positive stability, capsize-range, and secondary-stability metrics remain unavailable until generated-body evidence and an accepted heeled-integration model exist (`docs/PRD.md`, `docs/USER_GUIDE.md`, `docs/ROADMAP.md`, `docs/rfcs/0043-high-angle-gz-successor.md`, `kayakgen/eval/stability.py`).
- RFC 0024 already defines the correct evidence gate: open display meshes, open CFD packages, and synthetic fixtures cannot emit real kayak `GZ`; generated bodies must pass closure, signed-volume, manifold, self-intersection, source-hash, coordinate, unit, tolerance, and closure-policy checks before values are allowed (`docs/rfcs/0024-high-angle-gz-generated-body-handoff.md`).
- RFC 0022 gives the first concrete body profile available to use: `generated_hull_plus_deck_closed_body_v1`, explicitly separate from display STLs and not a CFD-readiness claim (`docs/rfcs/0022-generated-closed-body-construction.md`).
- The research packet identifies Option B as the smallest real model that fits the current evidence spine: generated closed body, fixed upright trim, hull-fixed passive CG, per-heel sinkage solve, closed clipping/capping, grid-bounded summaries, and sealed-body warnings (`striatum/0050-decision-panel-research/research/high_angle_stability/RESEARCH.md`).
- Independent external check: kayak stability curves are righting-arm curves from CG/CB separation over heel, and the common kayak-review assumption fixes the paddler immobile relative to the boat, which supports hull-fixed passive CG as the v1 comparator rather than an active paddler model ([Guillemot Kayaks, accessed 2026-05-14](https://guillemot-kayaks.com/kayak-stability)).
- Independent external check: commercial stability tooling supports both free-trim and specified fixed-trim GZ calculation, and computes GZ at specified heel angles for a loading condition, so fixed trim is a legitimate named comparator mode even though free trim is a later, stronger equilibrium mode ([Maxsurf Stability Capability, accessed 2026-05-14](https://maxsurf.net/stability-capability)).
- Independent external check: regulatory intact-stability calculations may require free trim to zero trimming moment and include flooding considerations, which is evidence against hiding fixed trim or flooding assumptions as defaults ([46 CFR 28.570, eCFR, accessed 2026-05-14](https://www.ecfr.gov/current/title-46/chapter-I/subchapter-C/part-28/subpart-E/section-28.570)).
- Independent external check: IMO frames intact stability around GM, righting lever `GZ`, weather/free-surface effects, and watertight integrity, reinforcing that kayak-gen must not turn this geometry-based hydrostatic comparator into a safety or seaworthiness claim ([IMO Ship Design and Stability, accessed 2026-05-14](https://www.imo.org/en/ourwork/safety/pages/shipdesignandstability-default.aspx)).
- Independent external check: mesh volume and center-of-mass properties are only meaningful for watertight volume evidence; Trimesh explicitly warns that mass properties are unreliable when a mesh is not watertight, supporting the closed-body-before-integration gate ([Trimesh docs, accessed 2026-05-14](https://trimesh.org/trimesh.base.html)).

## Why Other Options Lose

- Option A, Keep Real GZ Unavailable, is the correct current runtime behavior but not a sufficient model decision. It preserves truthfulness, but it does not answer the design-gate question that must be settled before work can proceed.
- Option C, Free-Trim Per-Heel Model, is physically stronger for regulatory-style equilibrium, but it should be a named successor. It adds a coupled sinkage/trim solve, more non-convergence modes, and higher residual/reporting burden before the project has a first generated-body clipping path.
- Option D, Flooding/Downflooding Or Active-Paddler Model, is out of reach for v1. The current body profile has no cockpit openings, compartment flooding, water-on-deck progression, paddler body volume, or active human response model.
- A hull-only or cockpit-cut stability body loses for v1 because it creates a second body concept before the existing RFC 0022 generated body has been used. It may become the right successor if sealed full-deck curves prove misleading at high heel.

## Implementation Gates

- Keep existing unavailable output until the selected model is implemented behind RFC 0024 gates; no placeholder or fixture-derived `gz_m`, righting moments, or summary metrics may reach CLI, sweep, comparison, desktop, or web surfaces.
- Add additive per-heel status metadata before user-facing curves: heel angle, status, sinkage/waterplane offset, trim policy, displaced mass/volume, load mass, displacement error, relative residual, CG/CB world coordinates, `gz_m`, righting moment, longitudinal moment residual, tolerances, iteration count, and warnings.
- Define waterline clipping/capping diagnostics separately from body diagnostics. Passing generated-body closure is necessary but not sufficient for each heeled submerged volume.
- Report fixed-trim longitudinal moment residuals. If free-trim mode is later added, expose it under an explicit mode name with solved trim angle, moment residuals, iterations, and convergence warnings.
- Treat `max_gz_m`, `heel_at_max_gz_deg`, area, and range-of-positive-stability as grid-derived/grid-bounded unless a later decision accepts interpolation semantics.
- Emit sealed-body assumptions and warnings at minimum: `sealed_deck_profile_no_cockpit_opening`, `deck_immersion_assumption`, `flooding_not_modeled`, `downflooding_not_modeled`, `active_paddler_response_not_modeled`, and `not_seaworthiness_or_safety_claim`.

## No-Claims Language

This decision does not deliver real high-angle stability today. Until generated-body evidence, clipping/capping diagnostics, residual contracts, tests, and user-surface wiring land, kayak-gen must continue to show unavailable high-angle `GZ` results. When v1 does land, it is an unvalidated hydrostatic comparison curve, not a safety, seaworthiness, capsize-recovery, final design-fitness, calibrated performance, CFD, or production solver-readiness claim.

## Confidence

High.
