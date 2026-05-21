# Implement NB-1 stepped-clock seam — workflow 0054 successor

Read `striatum/0054-rfc-0057-stage-4-ui-polish/ledger/FINDINGS_LEDGER.md`
(section NB-1), `STAGE_2_3_DECISIONS.md` rows D-16 and D-17, and
the existing `kayakgen/ui/web/generate_state_listener.py`.

Add an optional stepped-clock seam so tests can assert cadence,
terminal-refresh, teardown, reinstall, and coalescing behavior
without real `time.sleep` waits.

Land:

- `install_generate_state_listener(app, *, time_provider=None, clock_step=None, ...)`:
  - `time_provider: Callable[[], float] | None` — defaults to
    `time.monotonic`. When provided, the listener uses it for every
    `time.monotonic()` read inside the loop.
  - `clock_step: float | None` — when set, the listener uses a
    stepped sleep that advances a fake clock by `clock_step` seconds
    per iteration instead of `time.sleep(...)`. `clock_step is None`
    → existing behavior (real sleep).
- Refactor the inner-loop sleeps + monotonic reads through these
  two parameters. Wall-clock test paths stay byte-stable: the new
  parameters default to None / monotonic, so existing tests
  continue to pass without changes.

Tests in `tests/test_generate_state_listener.py` (existing — extend
rather than replace):

- Add `_StepClock` helper that returns the next monotonic-style
  value from a list. Use it to drive at least one stepped-clock
  variant per existing cadence/terminal-refresh/coalesce/reinstall
  test (do NOT delete the existing wall-clock tests).
- Each stepped-clock test asserts the listener fires the expected
  callback sequence without calling `time.sleep` (verify by
  monkeypatching `time.sleep` to raise and confirming the test
  still passes when `clock_step` is set).

Requirements:

- The seam is opt-in. `install_generate_state_listener(app)` with no
  new keywords behaves exactly as before.
- No change to the listener's public callback contract.
- Run focused tests + ruff before publishing.

Write scope:
- `kayakgen/ui/web/generate_state_listener.py`
- `tests/test_generate_state_listener.py`

Publish the required patch summary artifact under
`striatum/0056-.../implementation/nb1_clock_seam/PATCH_SUMMARY.md`.
