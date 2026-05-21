author: implementer-claude-opus-4.7-001
schema_version: striatum.patch_summary.v1
kind: patch_summary
logical_name: patch_summary
workflow_id: 0056-rfc-0058-stage2-3-burndown
job_id: implement_nb1_clock_seam

# Patch Summary

## Changes

- Added an opt-in stepped-clock seam to `install_generate_state_listener`
  in `kayakgen/ui/web/generate_state_listener.py` (RFC 0058 workflow 0056
  D-16). Two new keyword args, both default to None:
  - `time_provider: Callable[[], float] | None` — clock used for coalesce
    timing; defaults to `time.monotonic`.
  - `clock_step: float | None` — when set, opts into stepped-clock mode:
    no background thread is started; tests drive iterations explicitly.
- Routed every `time.monotonic()` read inside the listener through the new
  `handle.clock` callable. `_wrap_manual_refresh` and `_refresh_jobs` now
  stamp `handle.last_refresh_at` via `handle.clock()`, so a stepped or
  frozen clock controls coalesce behavior deterministically.
- Exposed `tick_generate_state_listener(app, *, iterations=1)` as the
  driver for the stepped-clock seam. It runs the same loop body the
  wall-clock thread would run, minus the sleep, and no-ops cleanly when
  the listener was installed in wall-clock mode.
- Wall-clock default behavior is byte-stable: when neither new kwarg is
  passed, the constructor stores `time.monotonic` as the clock, leaves
  `clock_step=None`, and starts the same `_tick` thread the prior code
  started.

## Tests

- Extended `tests/test_generate_state_listener.py` (D-17). Added a
  `_SteppingClock` helper and `_ban_sleep` fixture-style monkeypatch that
  replaces `listener_module.time.sleep` with an asserting stub.
- Added seven stepped-clock variants — none of them use `time.sleep`:
  - `test_stepped_clock_install_does_not_start_thread`
  - `test_stepped_clock_running_cadence_refreshes_each_tick`
  - `test_stepped_clock_idle_cadence_refreshes_each_tick`
  - `test_stepped_clock_listener_refreshes_terminal_detail_panels_once`
  - `test_stepped_clock_listener_coalesces_nearby_manual_refresh`
    (uses a frozen clock so `now - last_refresh_at == 0 < coalesce
    window`)
  - `test_stepped_clock_reinstall_replaces_handle`
  - `test_tick_is_noop_when_listener_uses_wall_clock`
- All 14 original wall-clock tests are preserved verbatim (their
  `time.sleep` calls remain — D-17 explicitly keeps them so the seam can
  be validated against existing behavior).

## Verification

- `.venv/bin/python -m pytest tests/test_generate_state_listener.py -v`
  → 21 passed (14 original + 7 stepped-clock).
- `.venv/bin/python -m ruff check kayakgen/ui/web/generate_state_listener.py
  tests/test_generate_state_listener.py` → clean.

## Out of scope

- Did not touch `kayakgen/services/generative_jobs.py` (that file's
  modification belongs to `implement_cfd_in_loop_status`).
- Did not delete or migrate the existing wall-clock tests — D-17 keeps
  them as the seam's validation baseline.
- `clock_step` is currently a mode flag whose value documents the
  contract ("each iteration advances by clock_step"); the test owns the
  `time_provider` and is responsible for keeping the two consistent. A
  future workflow can tighten this if a stepped scenario benefits from
  the listener itself advancing a virtual clock.
