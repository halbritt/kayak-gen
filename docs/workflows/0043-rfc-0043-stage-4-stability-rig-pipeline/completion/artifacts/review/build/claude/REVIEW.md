author: operator

workflow: 0043-rfc-0043-stage-4-stability-rig-pipeline
role: reviewer
lane: claude
posture: ergonomics_dx

# Build review — RFC 0043 stage 4 CLI completion (claude / ergonomics_dx)

I reviewed the CLI-completion build against
`artifacts/build/CLI_COMPLETION_HANDOFF.md` (the §1-§8 spec),
`artifacts/synthesis/DESIGN_SYNTHESIS.md` §A-§E, and
`artifacts/build/CLI_COMPLETION_RESULT.md`. I exercised the live CLI
(`.venv/bin/kayakgen stability …`) and ran the §7 gate locally; both are
allowed read-only operations per the prompt.

## Decision

`accept_with_findings`

The operator-facing surface lands cleanly: every §A subcommand exists,
the §A.4 JSON shape is correct in-vivo, refusals emit the §E.3 envelope
with `next_action` from `REASON_NEXT_ACTION`, the stage-4 USER_GUIDE
subsection is self-contained and runnable, and the §7 verification gate
is green (89/89). Two ergonomics gaps are remediable in follow-up and
do not block landing.

## Required checks

| # | Surface | Verdict | Evidence |
|---|---|---|---|
| 1 | `promote-fixture` writes `promotion.json`; manifest immutable | pass | `kayakgen/cli/stability_cli.py:167-251` (assert manifest bytes byte-equal at `:250`). |
| 2 | `accept-fit` uses `--fit-record / --fixture-id / --out`, `--packet` removed, refuses §B gates, byte-stable | pass (with F1) | `stability_cli.py:254-431` (signature `:256-283`, removed-`--packet` refusal `:295-302`, gate refusals `:308-424`, byte-stable `_write_json_refusing_overwrite` `:92-96` / `:426-427`). |
| 3 | `claim-status` emits §A.4 JSON shape; `--debug` lists `REASON_*` diagnostics | pass | `stability_cli.py:434-508`; live: `{"claim_label","covering_fit_id","design_hash","dropped_fit_count","fits_loaded","fits_root","hull_class"}` on an in-test hull, `--debug` adds `"diagnostics": []`. |
| 4 | `--help` lists `claim-status`; refusals are one structured JSON line with `next_action` | pass (with F1) | `kayakgen stability --help` renders the §E.1 commands block exactly; `_refuse` at `stability_cli.py:103-124` emits `{ok, code, fixture_id, details, next_action}` with `next_action = REASON_NEXT_ACTION[code]`; live `fixture_manifest_missing` returned `"next_action": "run \`kayakgen stability ingest-rig-run\` first."`. |
| 5 | Both web call sites use a lazy mtime-memoized loaded registry; no `EMPTY_STABILITY_FIT_REGISTRY` import | pass | `kayakgen/ui/web/generate_frontier_view.py:38-50` accessor + `:582` use site; `kayakgen/ui/web/generate_spec_form.py:881-893` accessor + `:909` use site; `grep -n EMPTY_STABILITY_FIT_REGISTRY kayakgen/ui/web/*.py kayakgen/eval/stability/evaluator.py` → no matches. |
| 6 | Tests + conftest triple factory; §7 gate passes; `test_cli_stability.py` swept to new signature | pass | `.venv/bin/pytest tests/test_stability_fit_registry.py tests/test_measured_stability_acceptance.py tests/test_measured_stability_ingest.py tests/test_claim_state_measured_promotion.py tests/test_cli_stability.py tests/test_resolve_analytical_claim_label.py -q` → **89 passed in 0.70s**. |
| 7 | `Hull` carries `hull_class`; unset keeps unvalidated label; real-`Hull` production-flip test exists | pass | `kayakgen/model/hull.py:67-79` (optional, default `None`); `kayakgen/eval/stability/high_angle_contracts.py:66-69` keeps `None` at `unvalidated_hydrostatic_comparison`; production-flip tests at `tests/test_resolve_analytical_claim_label.py:201` and `:227` (Revision-1 fix per CLI_COMPLETION_RESULT.md, all green in the §7 run). Live: a synthesized `Hull(hull_class="sea_kayak")` against an empty fits root resolved to `unvalidated_hydrostatic_comparison` with `dropped_fit_count: 0`. |
| 8 | Docs — USER_GUIDE / SOURCES updates in the right sections | pass (with F2) | Stage-4 subsection `docs/USER_GUIDE.md:252-330` is correct and self-contained; SOURCES.md was rewritten to the canonical `kayakgen stability` surface (`docs/workflows/.../SOURCES.md:30-101`). |

## Posture-scoped findings (ergonomics_dx)

### F1 — `accept-fit --packet` removal is not discoverable from `--help`

**Surface:** check 2 / check 4.
**Issue.** `--packet` is declared `hidden=True`
(`kayakgen/cli/stability_cli.py:277-282`), so `kayakgen stability
accept-fit --help` lists only `--fit-record`, `--fixture-id`, `--out`.
The "REMOVED in RFC 0043 stage 4" copy lives in the command docstring
prose (`stability_cli.py:286-294`), not in any flag listing. The
explicit refusal at `stability_cli.py:295-302` only fires when every
new required flag is also passed; the natural migration command
`kayakgen stability accept-fit --packet path/to/packet.json` hits
Typer's required-option check first and surfaces:

```
Error: Missing option '--fit-record'.
```

The operator gets no breadcrumb that `--packet` was removed. The old
positional form `accept-fit fit.json --packet pkt.json` produces the
same Typer-stock error.

**Evidence (verified live).** `.venv/bin/kayakgen stability accept-fit
--packet /tmp/x.json` → `Missing option '--fit-record'.`; with all
required args plus `--packet`, the message becomes the expected
"accept-fit failed: --packet was REMOVED in RFC 0043 stage 4. Pass
--fixture-id <id> instead…" (exit 2).

**Impact.** Medium. The prompt's check "the `accept-fit` Typer error
path names `--packet` as removed and points at `--fixture-id`" is met
only when the caller has already supplied the new flags. An operator
adapting from the prior signature is more likely to hit the bare
missing-option error.

**Remediation.** Drop `hidden=True` from the `--packet` Option so
`--help` shows it with the existing `help=` text
("REMOVED in RFC 0043 stage 4 — pass --fixture-id instead.") visible.
Optionally add a Typer `epilog=` summarizing the migration.

### F2 — USER_GUIDE stage-3 examples are stale relative to the landed stage-4 CLI

**Surface:** check 8.
**Issue.** The stage-3 "Stability fixtures (RFC 0058)" block at
`docs/USER_GUIDE.md:203-250` was not updated when stage 4 landed.
Three of its four worked examples no longer match the live CLI:

- `:213-217` shows `kayakgen stability ingest-rig-run --fixture-id …
  --rig-run … --out …`; the landed signature
  (`stability_cli.py:140-153`) is positional `<manifest_path>` plus
  `--out <dir>`. Neither `--fixture-id` nor `--rig-run` exists.
- `:223-226` shows `promote-fixture --fixture-id … --packet … --out
  …`; the landed signature (`stability_cli.py:167-179`) is positional
  `<fixture_id>` plus `--packet`. There is no `--out`; the path is
  derived.
- `:233-235` shows `accept-fit --fit-record … --out …`; the landed
  signature (`stability_cli.py:254-283`) additionally requires
  `--fixture-id`. Copy-pasting the stale example fails with
  `Missing option '--fixture-id'.`

The narrative line `:209-210` ("Stage 4 first promotion remains gated
on D007 / D014 physical rig data") is technically still true for the
*first measured fixture* but reads, in context, as if the pipeline
itself were still gated — which it no longer is. An operator who
reads the guide top-to-bottom hits all three broken examples before
reaching the correct stage-4 subsection at `:252-330`.

**Evidence.** All examples reproduced from
`docs/USER_GUIDE.md:213-235` against the live CLI shown above; the
SOURCES.md update for stage 4 explicitly removed those obsolete
invocation names (`docs/workflows/.../SOURCES.md:30-101`) but the
USER_GUIDE did not follow.

**Impact.** Medium. The stage-4 subsection itself is correct and
self-contained (an operator who reads only `:252-330` can run the
pipeline). The risk is that operators reading top-to-bottom hit
broken examples first.

**Remediation.** Inside the stage-3 block, replace each example with
the landed signature (or delete the worked examples and link to the
stage-4 subsection). Tighten the `:209-210` narrative to
"stage-4 pipeline landed; first promotion of a real measured fixture
remains gated on D007 / D014 rig data."

### F3 — `promote-fixture` overwrite-with-different-bytes path does not emit the structured JSON envelope

**Surface:** check 4.
**Issue.** When `promote-fixture` succeeds it prints
`wrote <path>` (`stability_cli.py:251`); when it sees identical bytes
already on disk it prints `no-op <path>` (`stability_cli.py:238`); the
overwrite-with-different-bytes path emits a plaintext error to stderr
and exits 1 (`stability_cli.py:240-245`) rather than the §E.3 JSON
line. Every other refusal in the package routes through `_refuse(…)`
and emits the envelope; this CLI-only "refuse to clobber" surface is
the lone exception.

**Evidence.** `stability_cli.py:240-245`:
`typer.echo("promote-fixture failed: refusing to overwrite existing
artifact: …", err=True); raise typer.Exit(code=1)` — no `_refuse(…)`,
no JSON envelope, no `next_action`.

**Impact.** Low. Operators driving the CLI from a wrapper that
greps structured-JSON lines for `code`/`next_action` would have to
special-case this path. Not blocking — there is no `REASON_*`
constant for "refusing to overwrite", so this would require a new
reason token.

**Remediation.** Either add
`REASON_PROMOTION_PACKET_OVERWRITE_REFUSED` (+ a
`REASON_NEXT_ACTION` entry pointing at delete-the-old-promotion or
re-sign-against-current-bytes) and route through `_refuse`, or
explicitly document the plaintext shape in §E.3 as a stable
exception.

## Out-of-posture observations

- out-of-posture: `kayakgen/cli/stability_cli.py:127-128`'s
  `_heel_ranges_overlap` duplicates
  `kayakgen/eval/stability/registry.py:154-155`; the registry version
  could be reused. Pure refactor; no behavior impact.
- out-of-posture: `_refuse` (`stability_cli.py:103-124`) accepts
  `fixture_id=None` and emits `"fixture_id": null` — fine today since
  every caller passes a real id, but a future `claim-status`-side
  refusal envelope would need to think about this default.
- out-of-posture: the `LegacyStabilityGroup`
  (`stability_cli.py:61-75`) routes unrecognized positionals to a
  `legacy` command not in the §A surface; falls through to Typer's
  default group help. No behavior issue, just non-obvious.

## Operating discipline

- I did not modify implementation files; my write_scope is this
  REVIEW.md only.
- I did not coordinate with the codex reviewer (separate posture).
- I exercised `kayakgen stability --help`, `accept-fit --help`,
  `promote-fixture --help`, `claim-status --help`, two refusal paths
  (`accept-fit` removed-`--packet` and `fixture_manifest_missing`),
  the `claim-status` happy path against an in-test hull, and the §7
  `pytest` gate — all read-only.

## Verification gate run by this review

```
.venv/bin/pytest \
  tests/test_stability_fit_registry.py \
  tests/test_measured_stability_acceptance.py \
  tests/test_measured_stability_ingest.py \
  tests/test_claim_state_measured_promotion.py \
  tests/test_cli_stability.py \
  tests/test_resolve_analytical_claim_label.py \
  -q
```

Result: **89 passed in 0.70 s**.
