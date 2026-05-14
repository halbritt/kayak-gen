Read `docs/workflows/0048-successor-rfc-backlog/SOURCES.md` first.

Draft two proposed successor RFCs, and only those RFC files:

- `docs/rfcs/0042-resistance-calibration-fixture-successor.md`
- `docs/rfcs/0043-high-angle-gz-successor.md`

Use the maximal number of useful sub-agents with disjoint write scopes. Prefer
parallel agents for independent source analysis, domain checks, RFC drafting,
and artifact drafting, but keep one agent responsible for final integration of
this job's files.

Source scope:

- Existing RFCs 0019, 0020, 0024, and 0027.
- `docs/workflows/0018-deferred-backlog/QUEUE.md` entries for resistance
  calibration fixture and high-angle `GZ` / secondary stability.
- The current user-facing limitations in `docs/USER_GUIDE.md`.

Constraints:

- Do not implement runtime behavior.
- Do not edit `kayakgen/` or `tests/`.
- Do not update `docs/rfcs/README.md`; the integration job owns the index.
- Do not fabricate calibration fixtures, licenses, measured datasets, heeled
  volume integration, accepted secondary stability values, final prediction, or
  capsize claims.
- Do not add bylines or co-author trailers unless Striatum supplies an exact
  expected author line in the packet.

Publish a synthesis artifact at
`striatum/0048-successor-rfc-backlog/rfc_calibration_stability/RFC_SCOPE_CALIBRATION_STABILITY.md`
with Striatum `synthesis` front matter and a concise summary of files changed
and open questions.
