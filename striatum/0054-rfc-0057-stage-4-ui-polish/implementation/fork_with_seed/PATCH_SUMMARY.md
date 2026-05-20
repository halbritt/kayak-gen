author: implementer-codex-gpt-5.5-007

# Fork With New Seed Patch Summary

## Scope

- Verified `kayakgen/services/generative_jobs_fork.py` provides the fork primitive for search jobs by cloning the persisted source spec, patching `algorithm.seed` for `nsga2` or `ehvi`, and starting a new job through the active manager.
- Verified `GenerativeJob.forked_from` records source-job lineage and survives terminal job updates.
- Verified `kayakgen/ui/web/controllers.py` exposes `POST /api/generative-jobs/{job_id}/fork` with `{"new_seed": int}` validation and conservative `raw_unvalidated` response semantics.
- Verified `kayakgen/ui/web/generate_fork_button.py` provides the Trame "Fork with new seed" button helper and deterministic seed increment helper.
- Verified `tests/test_generative_jobs_fork.py` covers primitive success, sweep refusal, route success, bad seed payloads, missing source jobs, and sweep-source route refusal.

## Verification

- `.venv/bin/pytest tests/test_generative_jobs_fork.py` — 6 passed in 4.13s.
