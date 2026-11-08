# RFC 0084 — Source-bound full-gate receipts

Status: landed full pytest then Ruff + persistent receipts.
Date: 2026-11-08.

## Context and problem

Release discipline requires complete pytest followed by Ruff, but the full
shell gate ran Ruff first. Campaign-specific wrappers recorded results against
HEAD, which does not identify a staged or dirty candidate. A green pytest exit
alone also omits the mandatory lint check, skip pin and source-freeze evidence.

## Goals and non-goals

Make the existing full gate authoritative for its fixed check sequence and
optional durable outcome. Preserve the supported external interpreter, complete
test collection and four-default/zero-full-OpenFOAM skip policy. Keep fast-gate
manifest protections. Renderer probing/scheduling, installed-release acceptance,
task completion decisions and scientific claims have separate owners.

## Proposal and decision D070

`scripts/full-gate.sh` selects `KAYAKGEN_PY` (default `.venv/bin/python`) and
executes `python -m kayakgen.operations.gate`. The runner executes only:

1. `python -m pytest -q`, with the existing explicit in-suite skip pin.
2. `python -m ruff check kayakgen tests`, after successful pytest and skip check.

The runner clears inherited `PYTEST_ADDOPTS` for its children and records that
policy. Tracked pytest configuration remains effective. There is no arbitrary
command or subset option. An optional early lint check outside this runner
cannot replace its post-suite check. Fast mode remains a convenience subset.

Pass `--receipt PATH` or set `KAYAKGEN_GATE_RECEIPT`. The path must be new and
outside source or inside a Git-ignored directory. Per-command UTF-8 diagnostic
logs live in `<receipt-stem>.<run_id>.logs/` beside the receipt. Invalid paths,
launch failures before the runner starts, unwritable storage and uncatchable
termination cannot promise a terminal receipt; they never produce acceptance.

The runner publishes an initial `running` receipt, command checkpoints and an
atomic terminal replacement. SIGINT/SIGTERM stop and reap the owned command
process group and produce `interrupted` with exit `128 + signal`. Pytest or
Ruff failure, a missing/wrong summary, snapshot failure or changed source yields
`failed`; pending commands stay `not_run`. A stale `running` receipt is incomplete.

### Receipt contract

The schema identifier is `kayakgen-gate-receipt/1`. Fields are:

| Field | Meaning |
| --- | --- |
| `gate`, `run_id`, `repository` | `full` for this entry point; RFC 0082's dedicated pre-push caller uses `fast`; invocation UUID and resolved Git worktree |
| `status`, `exit_code` | `running`, `passed`, `failed` or `interrupted`; null exit while running |
| `started_at`, `finished_at`, `duration_seconds` | UTC wall-clock timestamps and monotonic elapsed duration |
| `source_before`, `source_after` | Candidate Git `tree_sha`, raw `fingerprint_sha256`, observed `head_commit`, original `index_tree_sha`, `dirty` |
| `source_unchanged` | Both candidate tree and raw content fingerprints agree |
| `expected_skips`, `observed_skips` | Four by default, zero when both supported OpenFOAM knobs equal `1`; null observation before a parsed summary |
| `interpreter` | Actual executable, resolved executable, requested override, version, prefix and base prefix |
| `renderer.declared` | The three software/EGL/VTK environment declarations, including absent values |
| `renderer.actual` | Explicit `unobserved` plus reason in historical receipts; RFC 0082 adds actual context/library evidence and resource admission |
| `commands` | Ordered `pytest`, `ruff` objects: actual argv, status, raw child exit, timestamps, duration, log path and pytest summary when observed |
| `environment_policy` | Cleared `PYTEST_ADDOPTS` policy and whether an inherited value existed; never retains supplied option text |
| `failure_reasons`, `diagnostics` | Stable failure categories and descriptive execution errors |

`passed` requires both mandatory commands to exit zero, a parsed matching skip
count and unchanged source. A consumer must check the terminal result, both
commands and its own required source/renderer predicates; a report is evidence,
not an authorization to close an issue or deploy. `renderer.actual.unobserved`
does not establish a renderer profile.

### Candidate identity and limitations

Copy the real Git index to a temporary index, retain its tree identity, stage
all tracked/nonignored candidate content into that copy, then write the candidate
tree. The real index is unchanged. Separately hash sorted raw Git path bytes,
file contents, executable modes, deletions and symlink target bytes. Check the
raw fingerprint around each snapshot and compare before and after the gate.
Refuse unsupported entry types or an unmerged index. HEAD is diagnostic only:
committing the same frozen content afterward retains the candidate tree.

Keep source frozen throughout the gate. Endpoint checks cannot detect a
transient edit restored between snapshots. Ignored files, external dependencies,
external symlink targets and machine state are outside this source identity.
The raw hash complements Git's tree when clean filters normalize bytes. This
local receipt is neither an authenticated attestation nor power-loss storage.

## Acceptance criteria and implementation path

Real-process temporary Git repositories exercise full pytest then real Ruff,
four and zero skips, failed pytest, failed post-suite Ruff, source mutation,
SIGTERM cleanup, output ownership, environment-only subset refusal and unchanged
staged/untracked candidates committed later. The repository's full suite then
runs on frozen source, followed by Ruff. Existing fast ignore/deselect and
in-suite skip-pin checks remain. No fixture-only acceptance switch ships.

## Open questions and domain modeling

Actual renderer evidence and scheduling are implemented by KAYGEN-19 / RFC 0082.
A **gate receipt**
records one verification invocation. A **candidate source snapshot** identifies
the tested content independently of the commit that may later contain it.
Neither creates a scientific accepted-use or task-completion state.
