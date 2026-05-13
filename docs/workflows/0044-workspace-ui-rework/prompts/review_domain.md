Operator parallelism instruction: use the maximal number of useful sub-agents
or parallel workers available for independent investigation and cross-checking.
Keep scopes disjoint, preserve this assigned Striatum role, and state what
sub-agent help was used in the artifact.

Read `docs/workflows/0044-workspace-ui-rework/SOURCES.md`, especially
`kayakgen/eval/claims.py`, `kayakgen/eval/mesh_diagnostics.py`,
`kayakgen/eval/cfd/jobs.py`, and the chip/banner text tables in RFC 0033 §4–§6
and the original Claude Design handoff §6.

Produce
`striatum/0044-workspace-ui-rework/domain/REVIEW_DOMAIN.md`.

Use this structure: verdict intent, findings, required actions, and residual
risk.

Focus on whether every chip text, persistent banner, and status-bar segment
in the rework mirrors the existing literals exactly (`ClaimState`,
`ReadinessLevel`, `CfdRunStatus`), whether the forbidden-claim list from RFC
0033 §8 is comprehensive (`cfd_ready` for current generated packages,
`calibrated`, `validated`, `final prediction`, `design fitness`, `hosted`,
`cloud`, `worker queue`, `OpenFOAM`, `SU2`, numeric `GZ_max`/`heel_angle_max_deg`),
whether class-preset wording stays in the "preset" / "in-class envelope"
register, and whether unsupported reserved fields (`LCB_frac`,
`rocker_bow_m`, `rocker_stern_m`) are surfaced only through RFC 0031's
unsupported channel.

Do not include any byline or any line beginning with `author:`.
