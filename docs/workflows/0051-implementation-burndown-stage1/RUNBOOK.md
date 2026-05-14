# Workflow 0051 Runbook

Purpose: burn down the first implementation stage unlocked by workflow 0050.

This workflow is implementation-only against already accepted RFCs and
workflow 0050 decisions. Do not reopen the design decisions. Do not claim
calibrated resistance, validated CFD, production solver readiness, hosted CFD,
public-service SLA, design fitness, or safety/seaworthiness.

Parallel implementation lanes:

- `implement_docs_status`: reconcile RFC/status docs after workflow 0050,
  including RFC 0009 status where current delivered behavior is already
  documented.
- `implement_ui_successors`: RFCs 0036-0039 UI cleanup successors.
- `implement_sweep_objectives`: RFC 0009 objective metadata prerequisite for
  search/optimization.
- `implement_readiness_report`: RFC 0040 readiness report and schema hardening
  that explains evidence without promoting ordinary packages to `cfd_ready`.
- `implement_openfoam_skeleton`: RFC 0041 OpenFOAM-v2512 `interFoam` profile,
  dependency detection, deterministic case rendering, unavailable/failed
  states, and raw fixture parser only.
- `implement_resistance_source_review`: RFC 0042 source-review packets and
  source-use mapping checks without fixture promotion.
- `implement_high_angle_v1`: RFC 0043 fixed-trim generated-body high-angle
  stability v1 gates and metadata, keeping user-facing unavailable behavior
  until evidence gates pass.

After the parallel lanes complete, run three independent reviews, a findings
ledger, a Codex remediation pass, and a final review.
