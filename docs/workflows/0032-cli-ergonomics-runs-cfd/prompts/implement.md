# Implement — workflow 0032 (R4 + R5)

Read `SOURCES.md`,
`docs/audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md` (R4 and R5
sections), the cited AUD-O-004 / AUD-O-005 / AUD-O-006 entries in
`docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md`,
and the current source in `kayakgen/cli/runs_cli.py` and
`kayakgen/cli/main.py`.

## R4 — runs CLI headers + filter docs

Edit `kayakgen/cli/runs_cli.py`:

1. Add an optional `--header / --no-header` flag (default
   `--no-header`) to both `runs_list_command` and `runs_jobs_command`.
   When `--header` is set, print one `#`-prefixed header line listing
   the column names of the rows the command already writes, before
   emitting the row loop. Example for `runs list`:

   ```
   # run_id  kind    created_at      out_dir
   <row1>...
   ```

   Do NOT change the row format. The header columns must match the
   exact tokens the row loop already emits.

2. Extend the `--filter` flag help on `runs_query_command` and (if
   the command exposes `--filter`) `runs_jobs_command` to enumerate
   the keys the implementation actually honors. Read the
   `candidates` table schema in
   `kayakgen/services/artifact_store.py` and the filter loop in
   `runs_query_command`. Document the actual honored set; if the
   implementation accepts arbitrary keys and quietly drops unknown
   ones, document that. Do not invent restrictions.

3. Update `docs/USER_GUIDE.md` `### runs` (around line 525) — add
   one short paragraph documenting `--header` and the filter-key
   vocabulary, plus one short code example. Keep it tight.

## R5 — CFD CLI polish

Edit `kayakgen/cli/main.py`:

1. `mesh-evidence` env-var refusal (around lines 273-291): after
   the existing `KAYAKGEN_OPENFOAM_LOCAL_RUN` block, append exactly
   one line of stderr output:

   ```
   Alternatively, the RFC 0046 profile flag (kayakgen cfd prepare --allow-real-solver-execution) or a persistent setting in ~/.config/kayakgen/cfd.json can opt in; mesh-evidence currently honors only the env-knob mechanism. See docs/USER_GUIDE.md '### cfd run' for precedence.
   ```

   Do not change the existing `binding_code:` / `mesh-evidence
   refuses to run:` lines.

2. `cfd prepare` success echo (around lines 438-441): after the
   existing `wrote <job_dir>` / `status: <status>` /
   `CFD_RAW_RESULTS_WARNING` echoes, append exactly one line of
   stdout:

   ```
   Next: kayakgen cfd run <job_dir>. The real-solver path requires an RFC 0046 opt-in (--allow-real-solver-execution, ~/.config/kayakgen/cfd.json, or KAYAKGEN_OPENFOAM_LOCAL_RUN=1).
   ```

   Use the actual job-dir variable (`paths.job_dir`) for
   `<job_dir>`. Do not modify the warning / status / wrote echoes.

## Verify

```bash
.venv/bin/pytest tests/test_runs_cli.py tests/test_cfd_jobs.py tests/test_cfd_jobs_openfoam.py -q 2>&1 | tail -20
```

If `tests/test_runs_cli.py` does not exist, skip it. All other tests
must stay green. Your additions are additive; if any test pins
exact stdout / stderr prose, update the assertion to match (the test
was pinning prose, not contract).

## Write scope (hard boundaries)

Touch only:

- `kayakgen/cli/runs_cli.py`
- `kayakgen/cli/main.py`
- `docs/USER_GUIDE.md`
- `tests/test_runs_cli.py` (if you add or update one)
- `tests/test_cfd_jobs.py`, `tests/test_cfd_jobs_openfoam.py` (only
  if a pinned-prose assertion needs to match an appended line)
- `docs/audits/2026-05-22-code-doc-audit/follow-ups/0032/`

Do NOT touch:

- `CHANGELOG.md` (parent agent).
- Any `FINDINGS.md` (parent agent flips statuses).
- `kayakgen/eval/contract.py`, `kayakgen/eval/stability/`,
  `kayakgen/ui/web/`, `tests/test_vocabulary_coverage.py` (owned
  by parallel follow-up workflows).

## Publish

Publish `docs/audits/2026-05-22-code-doc-audit/follow-ups/0032/PATCH_SUMMARY.md`
with:

- The exact filter-key list you documented.
- The exact text of the two appended messages (mesh-evidence + cfd
  prepare).
- Files touched (paths only).
- pytest pass/fail counts from the verify command.
