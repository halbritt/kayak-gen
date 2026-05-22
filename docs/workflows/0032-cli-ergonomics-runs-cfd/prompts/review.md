# Review — workflow 0032 (R4 + R5)

Read `SOURCES.md`, `REMEDIATION_PLAN.md` R4 and R5 rows, the
implement job's `PATCH_SUMMARY.md`, and every changed file.

## What to verify

1. **Write-scope boundary.** The patch touches only the files
   listed in the implement prompt's "Write scope" section. Flag any
   file outside that list (especially `CHANGELOG.md`, any
   `FINDINGS.md`, `kayakgen/eval/contract.py`,
   `kayakgen/eval/stability/`, `kayakgen/ui/web/`,
   `tests/test_vocabulary_coverage.py`).

2. **Back-compat — runs CLI rows unchanged.** Without `--header`,
   the stdout of `kayakgen runs list` and `kayakgen runs jobs`
   must be byte-identical to before. The flag default must be
   `--no-header`.

3. **Header columns match row format.** When `--header` is set,
   the printed header line names exactly the columns the row loop
   emits, in order, prefixed with `# ` (a single `#` and a single
   space).

4. **Filter-key vocabulary is honest.** The `--filter` help text
   on `runs_query_command` (and `runs_jobs_command` if applicable)
   names only keys the implementation actually honors. Cross-check
   against the `candidates` SQLite table schema and the filter
   loop in `runs_query_command`. If unknown keys are silently
   dropped, the help text must say so — no invented restrictions.

5. **Appended lines verbatim.** The mesh-evidence env-var refusal
   ends with exactly:

   ```
   Alternatively, the RFC 0046 profile flag (kayakgen cfd prepare --allow-real-solver-execution) or a persistent setting in ~/.config/kayakgen/cfd.json can opt in; mesh-evidence currently honors only the env-knob mechanism. See docs/USER_GUIDE.md '### cfd run' for precedence.
   ```

   The `cfd prepare` success echo ends with exactly:

   ```
   Next: kayakgen cfd run <job_dir>. The real-solver path requires an RFC 0046 opt-in (--allow-real-solver-execution, ~/.config/kayakgen/cfd.json, or KAYAKGEN_OPENFOAM_LOCAL_RUN=1).
   ```

   with `<job_dir>` interpolated from the actual `paths.job_dir`.

6. **USER_GUIDE addition is tight.** `### runs` gains one short
   paragraph plus one short code example; no other section is
   rewritten.

7. **Test suite stays green.** Run:

   ```bash
   .venv/bin/pytest tests/test_runs_cli.py tests/test_cfd_jobs.py tests/test_cfd_jobs_openfoam.py -q
   ```

   All tests must pass. If a pinned-prose assertion was updated,
   the diff is acceptable; flag any deleted test.

## Verdict vocabulary

`accept` | `accept_with_findings` | `needs_revision` | `reject`.

Use `accept_with_findings` for non-blocking polish notes;
`needs_revision` for any of: scope creep, broken back-compat,
verbatim copy drift, invented filter-key vocabulary, broken test.

Publish the finding artifact at
`docs/audits/2026-05-22-code-doc-audit/follow-ups/0032/reviews/REVIEW.md`
with `striatum.finding.v1` front matter and one of the four
verdicts.
