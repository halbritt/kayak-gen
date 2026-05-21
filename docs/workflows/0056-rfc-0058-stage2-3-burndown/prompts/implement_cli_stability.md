# Implement `kayakgen stability` CLI sub-app — RFC 0058 stage 3

Read RFC 0058 (section "CLI surface"), `STAGE_2_3_DECISIONS.md`
rows D-9 through D-12, and the existing `kayakgen/cli/main.py` +
`kayakgen/cli/runs_cli.py` (for sub-app registration style).

Land `kayakgen/cli/stability_cli.py` (new) with a Typer sub-app
named `stability_app` exporting four commands:

- `ingest-rig-run <manifest_path> --out <dir>` — Load the manifest
  JSON, validate it against `MeasuredStabilityFixture`
  (`kayakgen.eval.stability.measured_fixture`), write the canonical
  manifest to `<dir>/manifest.json`. Default `intended_use` for new
  fixtures: `"validation_candidate"`. Refuse to overwrite an
  existing manifest under the same `fixture_id`.
- `promote-fixture <fixture_id> --packet <path>` — Load the
  `StabilityFixturePromotionPacket` from `<path>`; validate it;
  read the fixture at `data/stability/fixtures/<fixture_id>/manifest.json`;
  if `promotion_target == "measured_stability_fixture"` and packet
  validation passes, update `intended_use="measured_stability_fixture"`
  and rewrite the canonical manifest. If `promotion_target == "rejected"`,
  rewrite with `intended_use="rejected"`. Otherwise no-op.
- `accept-fit <fit_record_path> --packet <path>` — Load both
  records; validate; copy the fit record verbatim to
  `data/stability/fits/<fit_id>.json`. Refuse to overwrite an
  existing record under the same `fit_id`.
- `residual-plot <fit_record_path> [--out <svg_path>]` — Load the
  fit record, render an SVG stub (see D-11) that contains the
  fit_id, hull_class, the four metric values, and the
  "validation_candidate vs reference" label. Use the vendored
  renderer pattern from RFC 0054 (`kayakgen/eval/calibration/*plot*`).
  No real curve drawing in this stage. Default output path
  `<fit_id>.svg` next to the input.

Land `kayakgen/cli/main.py` change: import `stability_app` and
register via `app.add_typer(stability_app, name="stability")`. This
single registration line is the only change to `main.py` in this
track.

Tests in `tests/test_cli_stability.py` (new) — use the
`typer.testing.CliRunner` pattern other CLI tests in this repo use.
Each command's test writes to `tmp_path`. Cover:

- `ingest-rig-run` happy path (validation candidate); refuses
  overwrite; refuses an invalid manifest;
- `promote-fixture` happy path (accept → fixture); refuses a packet
  that fails its own promotion-target validators; no-op on
  `validation_candidate`;
- `accept-fit` happy path; refuses overwrite; refuses a packet that
  is not `accepted` per its own validators;
- `residual-plot` writes a non-empty SVG that contains the fit_id
  and at least one metric value as text.

Requirements:

- The CLI commands write **only** to user-supplied paths inside
  `tmp_path` during tests; runtime behavior writes under
  `data/stability/{fixtures,fits}/...` (both gitignored).
- Add `data/stability/` to `.gitignore` if not already present.
- Run focused tests + ruff before publishing.

Write scope:
- `kayakgen/cli/stability_cli.py`
- `kayakgen/cli/main.py` (single `add_typer` line + import)
- `tests/test_cli_stability.py`
- `.gitignore` (single line addition, if needed)

Publish the required patch summary artifact under
`striatum/0056-.../implementation/cli_stability/PATCH_SUMMARY.md`.
