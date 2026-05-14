---
schema_version: "striatum.synthesis.v1"
artifact_kind: "synthesis"
---

author: operator [self-declared: operator-0047-rfc-scope]
kind: synthesis
run: run_489eb28aa3e0453b916113addacd02e3
session: sess_e945ff0b620b4e1bacbdde5c3e0bde7d
job: job_run_489eb28aa3e0453b916113addacd02e3_rfc_scope
lease: lease_7b1dd3e8cb584e02830e89b1a805c866
date: 2026-05-14

# RFC Scope - Workflow 0047 UI Follow-Up Cleanup

## Summary

Drafted proposed RFC 0035 as a narrow successor to workflow 0045 and
0046 final-review findings. The scope is UI cleanup and maintenance
only: validity-badge/class semantics, preset edit wording, dead or
duplicated web UI state/export logic, slider-label CSS and accessibility
follow-ups, desktop slider fallback maintenance, focused tests, and
docs/changelog alignment.

No runtime behavior was implemented in this RFC/scope lane.

## Files Changed

- `docs/rfcs/0035-ui-follow-up-cleanup.md` - new proposed successor RFC.
- `docs/rfcs/README.md` - added RFC 0035 to the index and current UI
  direction notes.
- `CHANGELOG.md` - recorded workflow 0047 RFC/scope progress as docs and
  scaffold work only.
- `docs/workflows/0047-ui-follow-up-cleanup/OPERATOR_REPORT.md` -
  recorded RFC/scope progress and validation status.
- `striatum/0047-ui-follow-up-cleanup/rfc_scope/RFC_SCOPE.md` - this
  synthesis artifact.

## Source Findings

- Workflow 0045 final review F1: web validity badge is keyed to the
  selected preset, unlike desktop class detection across all classes.
- Workflow 0045 final review F2: `_state_matches_preset_seed` appears
  effectively unreachable in normal hull-parameter listener flow.
- Workflow 0045 final review F3: presets narrow only the five canonical
  hull fields, while edits to other hull-shaping fields still switch the
  rail to `custom`; this needs explicit semantics and docs/tests.
- Workflow 0045 final review F4: `EXPORT_MENU_ROWS` defines the export
  menu contract, but `_render_export_menu` restates labels and disabled
  flags inline.
- Workflow 0045 final review F5: `_state_snapshot` duplicates ad-hoc web
  state keys across the app/controller boundary.
- Workflow 0046 final review M1: desktop slider label fallback still uses
  a manual offset when the installed Matplotlib lacks `label_location`;
  keep it bounded and remove it when the version floor allows.
- Workflow 0046 final review M2: web slider rows now use a wrapper
  `Div` with `role="group"` and an `aria-label`; successor review should
  confirm the accessibility semantics are intentional and tested.
- Workflow 0046 final review M3: `PARAMETER_RAIL_CSS` re-emits root
  theme tokens already supplied by the Vuetify/theme path.

## Deferrals

- Desktop parity rewrite, Qt-native slider rewrite, and broader desktop
  layout redesign remain out of scope.
- New backend capabilities, new REST route shapes, hosted CFD, hosted
  workers, cloud storage, and real solver adapters remain out of scope.
- OpenFOAM/SU2 integration, calibrated drag, accepted final prediction,
  final design fitness, and new resistance validity envelopes remain out
  of scope.
- Real high-angle `GZ`, `GZ_max`, `heel_angle_max_deg`, and capsize-range
  stability claims remain out of scope.
- Web-side mesh-package authoring beyond existing safe export entries
  and local/CLI guidance remains out of scope.
- Watertight-solid readiness and bare `cfd_ready` promotion remain out
  of scope.

## Verification

- Passed: `git diff --check`.
- Attempted: `striatum workflow validate
  docs/workflows/0047-ui-follow-up-cleanup/workflow.json`.
  The command reached the Striatum CLI but exited with
  `daemon_unreachable` because
  `/run/user/1000/striatum/striatumd.sock` was unavailable. I did not
  start the daemon or run any Striatum mutation command.

## Notes For Reviewers

- RFC 0035 intentionally does not read as an implementation ledger. The
  workflow 0047 review lanes should decide which items are safe-now and
  which should remain notes.
- The proposed badge semantics move the web badge toward desktop's
  all-class detection while preserving the RFC 0033/RFC 0034 badge
  vocabulary and no-new-capability boundary.
- Export, mesh, CFD, resistance, and stability copy must continue to use
  unavailable/raw/unvalidated wording where applicable.
