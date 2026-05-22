# Sources for workflow 0032

> The implementer and reviewer both read this file. Keep entries short
> and link to the canonical source rather than duplicating it.

## Audit batches addressed

- **R4** — `kayakgen runs list / jobs` headers + `--filter` key
  documentation. Finding **AUD-O-004**.
- **R5** — `mesh-evidence` env-var refusal message + `cfd prepare`
  success-path next-step hint. Findings **AUD-O-005** and **AUD-O-006**.

## Source-of-truth references

| Topic | Path | Notes |
|---|---|---|
| Remediation plan | `docs/audits/2026-05-22-code-doc-audit/REMEDIATION_PLAN.md` | R4 + R5 rows are the contract this workflow lands. |
| Operator-adoption findings | `docs/audits/2026-05-22-code-doc-audit/operator-adoption/FINDINGS.md` | AUD-O-004, AUD-O-005, AUD-O-006 entries. |
| Runs CLI source | `kayakgen/cli/runs_cli.py` | `runs_list_command`, `runs_query_command`, `runs_jobs_command`. |
| CFD CLI source | `kayakgen/cli/main.py` | `mesh-evidence` env refusal (~lines 273-291), `cfd prepare` success echo (~lines 438-441). |
| SQLite index schema | `kayakgen/services/artifact_store.py` | `runs`, `candidates`, `metrics`, `generative_jobs` tables; `list_runs`, `list_generative_jobs`, `candidates_for_run` methods. |
| User guide | `docs/USER_GUIDE.md` `### runs` (around line 525) | Where the `--header` and filter-key documentation lands. |
| RFC 0046 | `docs/rfcs/0046-*.md` | The three opt-in mechanisms (profile flag, persistent setting, env knob) and their precedence. |

## Filter-key vocabulary

The implementer should enumerate the keys honored by:

- `runs_query_command --filter` — read the `candidates` SQLite table
  schema (`status`, `hull_design_hash`, `hull_record_hash`,
  `candidate_key`, `run_id`) and the actual filter loop in
  `runs_query_command`. If the loop only honors a subset (the current
  implementation honors `status` and `hull_design_hash` via an `or`
  chain), document the actual honored set.
- `runs_jobs_command --filter` — the command currently exposes
  `--state` and `--kind` as dedicated flags, not via `--filter`. If
  `--filter` is wired to `--filter`, document accordingly; otherwise
  scope the docs change to `runs query`.

If the implementation accepts any key and quietly returns empty for
invalid ones, the help text should say so (don't invent restrictions).

## Where the workflow artifacts land

`docs/audits/2026-05-22-code-doc-audit/follow-ups/0032/`:

```
PATCH_SUMMARY.md
reviews/REVIEW.md
```

## Out of scope

- `CHANGELOG.md` (parent agent updates).
- `FINDINGS.md` status flips (parent agent / operator).
- `kayakgen/eval/contract.py`, `kayakgen/eval/stability/`,
  `kayakgen/ui/web/`, `tests/test_vocabulary_coverage.py` — owned by
  parallel follow-up workflows.
