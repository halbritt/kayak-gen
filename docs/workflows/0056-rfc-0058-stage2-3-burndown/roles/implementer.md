# Role: Implementer

Implement your assigned RFC 0058 stage 2 / stage 3 / NB-1 track per
`STAGE_2_3_DECISIONS.md`. Stay inside the packet's write scope. The
other implementer tracks and the docs-sync track run in parallel
on disjoint files; do not touch their scope.

Use the maximal useful number of sub-agents for parallel code
reading and focused verification, keeping the final patch inside
the assigned ownership boundary. Preserve every no-claims
boundary; no fixture is promoted; no new claim-state literal beyond
the two already named in RFC 0058 is introduced.

Publish the required patch summary with the exact packet byline.
