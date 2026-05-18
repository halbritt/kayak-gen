# Role: Reviewer — Tests and operational behavior

Review tests, determinism, failure modes, and API/CLI compatibility.
Stage-4-specific concerns:

- Auto-poll cadence must be cancellable; no test should depend on
  wall-clock sleeps that vary between fast and slow runners.
- Subprocess-default flip must not break existing tests that constructed
  the in-process manager directly; the public class names stay.
- Log redaction must produce byte-stable output for inputs that contain
  no absolute paths.
- Fork-with-seed must not race on the source job's `job.json` writes
  (atomic-replace pattern landed in stage 3).
- Form-builder integration tests should drive the Trame controller
  callbacks rather than the rendered widget tree, mirroring the existing
  `tests/test_generative_jobs_web.py` style.

The full repo suite minus the env-gated OpenFOAM smoke must remain green.
The forbidden-claim, ui-theme orphan, import-boundary, and
services-boundary scans must all pass.
