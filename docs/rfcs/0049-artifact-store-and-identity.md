# RFC 0049: Artifact Store and Identity Normalization

Status: landed Hull.{record,design}_hash + FilesystemArtifactStore + SqliteIndex + kayakgen runs CLI
Date: 2026-05-16
Context: Phase 4 of `ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md`.
Today's sweep/search/CFD/comparison artifacts live as files in
operator-chosen directories with a single content-hash field
(`Hull.hash()`) and no cross-run index. This scales to single-digit
hundreds of candidates per run; it does not scale to active-search
campaigns over thousands of candidates or to surfacing the
provenance ledger the architecture review asks for.

## Problem

Three concrete pain points:

1. **Identity collapses everything into one hash.** `Hull.hash()`
   conflates physical design inputs with serialization shape. Two hulls
   that differ only in `name` or `class_preset` hash differently even
   though they should hit the same cache. Two hulls that differ in a
   *reserved* shape control (`LCB_frac`) hash identically even though
   they may evaluate differently when the control becomes implemented.
2. **Run lookup is "find the directory."** There's no index. Operators
   point at a path; `kayakgen compare` reads `summary.csv` line by
   line. Sweep/search runs are append-only by convention, not by
   construction.
3. **Artifacts have no content-addressed identity.** A STL file in a
   sweep candidate directory is named by deterministic candidate-key,
   but its on-disk bytes have no published checksum. The mesh evidence
   chain (D026) records SHA-256 for polyMesh artifacts; sweep STLs,
   high_angle_gz JSON, comparison reports, and run records do not.

This RFC normalizes identity and introduces an `ArtifactStore`
abstraction. The store starts filesystem-backed (same layout as today,
with a manifest at the run root). A SQLite or DuckDB index over runs +
candidates + metrics + artifacts + events lands second. Migration is
opt-in: existing run directories still load.

## Goals

- Define four explicit identity concepts and the rules that govern them.
- Add an `ArtifactStore` interface that abstracts content-addressed
  artifact persistence and metadata queries.
- Preserve `Hull.hash()` byte-stably; introduce `Hull.design_hash()`
  alongside.
- Filesystem-backed store first; SQLite index second; both opt-in;
  the existing run directory layout remains a compatibility export.
- Make sweep / search / compare / CFD job records the system of record
  for their respective domains while routing artifact writes through
  the store.
- Make query patterns ("show me all candidates in run X with
  GM0_m > 0.05 and displacement_error_kg < 5", "show me the latest
  succeeded OpenFOAM run that targets profile P") cheap.

## Non-Goals

- No remote storage backend. ArtifactStore v1 is filesystem-local. A
  cloud backend (S3, GCS) is a successor decision, not part of this
  RFC.
- No durable event stream across runs in v1. The store records
  per-run events; cross-run correlation lives in the index but is not
  a Kafka.
- No automatic re-hashing of existing artifacts. The store records
  hashes for new writes; legacy artifacts get hashes lazily on first
  read.
- No new claim state, no new readiness level.
- No removal of the existing run-directory layout. The store sits
  atop that layout; the layout is the compatibility export.
- No web UI in v1; the store surfaces via the CLI (`kayakgen runs
  list`, `kayakgen runs query`).
- No CFD adapter change.

## Identity vocabulary

Four explicit hash concepts. All SHA-256, lowercase hex, 64 chars.

| Hash | Domain | Stability rule |
|---|---|---|
| **design_hash** | physical inputs that affect geometry/evaluation: `length_m`, `beam_oa_m`, `beam_wl_m`, `draft_m`, `deck_height_m`, `Cp`, `Cm`, `deck_flatness`, `center_box_ratio`, `bow_rake`, `stern_rake`, `rocker_bow_m`, `rocker_stern_m`, `LCB_frac` (when implemented), `geometry_kind`, `distribution_v2` block when present | invariant under: renaming the hull, changing `class_preset`, adding annotation fields, changing JSON key order |
| **record_hash** | the full serialized Pydantic record bytes after canonical-order JSON encoding | invariant under nothing but byte-equal serialization; differs whenever any field differs |
| **artifact_hash** | the on-disk bytes of any persisted artifact (STL, force.dat, JSON file, polyMesh file) | invariant under nothing but byte-equal bytes |
| **run_hash** | the spec + evaluator versions + the relevant kayakgen package version pin (`kayakgen.__version__`) | invariant under: timing, operator host, randomization seeds *unless* the spec includes seeds; differs whenever any input that affects the run output differs |

`Hull.hash()` becomes a synonym for `Hull.record_hash()` (byte-stable
with today's behavior). `Hull.design_hash()` is added.

Internal cache and run callers that today use `Hull.hash()` are
migrated to `Hull.design_hash()` where caching is correct
(geometry/evaluation cache) and stay on `Hull.record_hash()` where
record identity matters (run-record echo, JSON file naming).

## ArtifactStore interface

Pure Python; framework-agnostic; no external dependency in v1.

```python
class ArtifactStore(Protocol):
    def put_json(self, kind: ArtifactKind, payload: BaseModel) -> ArtifactRef: ...
    def put_file(self, kind: ArtifactKind, path: Path) -> ArtifactRef: ...
    def get_json(self, ref: ArtifactRef) -> dict: ...
    def get_file(self, ref: ArtifactRef) -> Path: ...
    def record_event(self, run_id: str, event: RunEvent) -> None: ...
    def query_candidates(
        self, run_id: str, *, filters: dict[str, Any] | None = None,
        metrics: Sequence[str] = (),
    ) -> list[CandidateSummary]: ...
```

`ArtifactRef` carries `kind`, `artifact_hash`, optional `run_id`,
optional `candidate_key`, and an optional `relative_path` for the
filesystem-backed store.

`ArtifactKind` is a literal enum: `hull_json`, `eval_result_json`,
`stability_result_json`, `mesh_package_manifest`, `mesh_quality_json`,
`hull_stl`, `deck_stl`, `cfd_run_record`, `cfd_raw_result`,
`openfoam_force_dat`, `openfoam_polymesh_file`,
`snappy_hex_mesh_evidence`, `sweep_run_record`,
`sweep_summary_csv`, `sweep_failures_jsonl`, `candidate_record`,
`high_angle_gz_artifact`, `search_run_record`, `comparison_report`.

## Filesystem store v1

Layout matches today's run directories with one addition: each run
gains a `_store/` subdirectory containing a SHA-256-indexed mirror of
the artifact bytes (content-addressed). The "human" filenames at the
canonical paths (e.g. `candidates/<key>/record.json`) become
hard-links into `_store/` so byte-equality is enforced for free.

```
runs/<name>/
├── _store/
│   ├── <hash>.json
│   ├── <hash>.stl
│   ├── manifest.json   # index of (kind, artifact_hash, canonical_path)
│   └── events.jsonl    # append-only event log
├── run.json            # hard-link into _store/
├── summary.csv         # legacy view; reconstructed from the index
├── failures.jsonl      # legacy view
├── spec.json           # hard-link into _store/
└── candidates/<key>/   # legacy canonical paths; hard-links into _store/
```

The legacy paths stay. Existing test fixtures and tools work
unchanged. The `_store/` is additive.

## SQLite index v1

A single SQLite database at `~/.local/share/kayakgen/index.sqlite`
(overridable via `KAYAKGEN_INDEX_DB`) indexes:

```sql
CREATE TABLE runs (
  run_id TEXT PRIMARY KEY,
  kind TEXT,        -- 'sweep' | 'search' | 'cfd' | 'comparison'
  spec_hash TEXT,
  run_hash TEXT,
  created_at INTEGER,
  out_dir TEXT
);

CREATE TABLE candidates (
  candidate_key TEXT,
  run_id TEXT,
  status TEXT,
  hull_design_hash TEXT,
  hull_record_hash TEXT,
  created_at INTEGER,
  PRIMARY KEY (run_id, candidate_key),
  FOREIGN KEY (run_id) REFERENCES runs (run_id)
);

CREATE TABLE metrics (
  run_id TEXT,
  candidate_key TEXT,
  metric_name TEXT,
  metric_value REAL,
  PRIMARY KEY (run_id, candidate_key, metric_name),
  FOREIGN KEY (run_id, candidate_key) REFERENCES candidates (run_id, candidate_key)
);

CREATE TABLE artifacts (
  artifact_hash TEXT PRIMARY KEY,
  kind TEXT,
  run_id TEXT,
  candidate_key TEXT,
  byte_count INTEGER,
  created_at INTEGER,
  relative_path TEXT
);

CREATE TABLE events (
  event_id INTEGER PRIMARY KEY AUTOINCREMENT,
  run_id TEXT,
  ts INTEGER,
  kind TEXT,
  payload TEXT  -- JSON
);
```

Indexes on `runs.kind`, `runs.created_at`, `candidates.hull_design_hash`,
`metrics.metric_name`, `artifacts.kind`.

## CLI

Two new opt-in subcommands; default kayakgen behaviour unchanged.

- `kayakgen runs list [--kind sweep|search|cfd|comparison] [--limit N]`
- `kayakgen runs query <run> [--filter metric:op:value] [--metric NAME]`
- `kayakgen runs reindex [--all | --since TIMESTAMP]`

`kayakgen sweep`, `kayakgen search`, `kayakgen compare`, and
`kayakgen cfd run` all gain an internal call into the store on write
that records the run + candidates + metrics + artifacts.

The store is created lazily on first write. Operators with no store
get today's behavior.

## What lands and what does not

Lands:
- `kayakgen/services/artifact_store.py` (Phase 3D adjacent; this RFC
  expects Phase 3D's services package to exist).
- `kayakgen/services/identity.py` for `design_hash()` / `record_hash()`
  / `run_hash()`.
- `kayakgen.model.hull.Hull.design_hash()` accessor.
- Internal cache callers migrated.
- Filesystem-backed store + SQLite index.
- The three new `kayakgen runs` subcommands.
- Tests:
  - identity invariance (rename hull → same design_hash; change Cp →
    different design_hash);
  - filesystem store round-trip;
  - SQLite index reads after each kayakgen subcommand;
  - legacy run-directory loading still works without an index.

Does not land:
- Remote storage.
- Hosted query API.
- Cross-run correlation engines.
- Migration of every existing fixture.
- Auto-promotion of any claim state.

## Acceptance Criteria

- `Hull.hash()` produces byte-identical output for every existing
  hull in tests/golden/ and tests/fixtures/.
- `Hull.design_hash()` is invariant under renaming, class_preset
  change, and JSON-key-order change. Pinned by parametrized tests.
- The filesystem store writes `_store/<hash>.<ext>` files and hard-
  links them to canonical paths. Existing test fixtures (sweep runs,
  CFD jobs, comparison reports) load through the store identically.
- The SQLite index records one row per run/candidate/metric/artifact.
  `kayakgen runs list` produces deterministic ordering.
- All 685 existing tests pass byte-stably (no schema changes to
  existing records).
- New parametrized tests for identity (~12), store round-trip (~10),
  index queries (~8), and CLI smoke (~6).

## Open Questions

- Should the index live in the run directory (`runs/<name>/_index.sqlite`)
  or one machine-wide DB? Per-run is simpler and works offline; one DB
  is the natural cross-run home.
- Hard-links break on Windows network shares; do we fall back to copy
  there, or refuse?
- How should the store handle `_store/` getting corrupted (manual file
  removal)? Re-derive from canonical paths on next read, with a
  warning.
- Do we expose the store interface in `kayakgen.services` or
  `kayakgen.eval`? `services` matches the Phase 3D layer.
- Should `Hull.design_hash()` include `geometry_kind` once
  RFC 0048 lands? Yes — the kind is a physical input.

## Implementation Path

1. Land `Hull.record_hash()` as the explicit name for today's
   `Hull.hash()`. Make `Hull.hash()` a thin alias.
2. Land `Hull.design_hash()` with the documented invariance rules
   and a parametrized test matrix.
3. Land `kayakgen/services/identity.py` with `run_hash()` over a
   sweep/search spec and the kayakgen version pin.
4. Land `kayakgen/services/artifact_store.py` with the filesystem
   backend and the manifest writer.
5. Migrate `kayakgen.search.sweep` and `kayakgen.search.active.runner`
   write paths to route through the store.
6. Migrate `kayakgen.eval.cfd.job_store` write paths (Phase 3A
   sibling) to route through the store.
7. Land the SQLite index and the `kayakgen runs` subcommands.
8. Update `docs/USER_GUIDE.md` with the new subcommands.

## Domain Modeling

Boundary clarification. The `ArtifactStore` is a domain service that
sits beside (not above) the existing aggregates. It does not own them;
it persists them. The four identity hashes are value objects: pure
functions over canonical-form bytes.

The SQLite index is a *read model* — a materialised view of the
authoritative file-system artifacts. The store keeps it eventually
consistent (each write updates both the canonical path and the index;
`kayakgen runs reindex` re-derives the index from disk).

Cite `DDD.md § "Adding to the model"`: this is a *persistence layer*
addition over existing aggregates, plus four new value objects and
two new write surfaces (`kayakgen runs list/query/reindex`).
