# Role: Integrator

Run after every `implement_*` author track has published its patch summary.
Wire the new modules into the existing Generate tab in
`kayakgen/ui/web/app.py`, add a panel-level integration test, and run the
full repo suite minus the env-gated OpenFOAM smoke.

Do not re-implement any track's logic. If a track's module is missing, has
the wrong public surface, or fails its own focused tests, raise a
`needs_revision` against that track rather than patching around it.

Stay strictly inside the integrator's write scope. The forbidden-claim
scan, ui-theme orphan scan, and import-boundary scan must remain green.
