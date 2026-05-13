Verdict intent: accept_with_findings

# Domain Review: Generated Closed-Body Construction Policy

## Sub-agent Delegation Statement
I used the `codebase_investigator` sub-agent to analyze the production code (`kayakgen/model/geometry.py`, `kayakgen/eval/closed_volume.py`, and `generator.py`) for the current state of geometry construction policies. I used the `generalist` sub-agent to analyze the test suite (`tests/test_closed_volume.py` and `tests/test_mesh_package.py`) to determine the current test coverage for the domain rules.

## Policy Evaluation
RFC 0022 successfully addresses the deferred domain policy gaps from RFC 0016. It explicitly defines the required geometric semantics to produce a valid `generated_hull_plus_deck_closed_body_v1` suitable for hydrostatic evaluation. 

The domain constraints are well-defined:
1. **Bow/Stern Caps and Plumb Endpoints:** Explicit endpoint surfaces are required. For plumb endpoints (`bow_rake = 0.0`), the non-zero section area must be preserved and capped rather than collapsing to a degenerate point.
2. **Sheerline and Deck Join:** The policy correctly requires the deck to join at the overall-beam sheer edge, closing the horizontal gap when `beam_wl_m != beam_oa_m`.
3. **Waterline Metadata:** Treating the waterline as metadata rather than a geometric cut boundary prevents premature truncation, which is correct for a hull-plus-deck solid.
4. **Normals and Signed Volume:** Enforcing outward-oriented normals and requiring positive signed volume above the serialized tolerance guarantees consistent orientation for evaluation.
5. **Closure Tolerances & Diagnostics:** Body-level manifold diagnostics are correctly established as the authority over part-level intent, with exact tolerances for welding and degeneracy serialized.

## Implementation Findings
Based on the independent sub-agent investigations, the current implementation has not yet fulfilled the RFC 0022 policy. The following findings must be addressed during implementation:

1. **Missing Caps:** The mesh generator currently lofts to stations at +/- L/2 where the area becomes zero, but no explicit cap faces are generated.
2. **Unresolved Plumb Endpoints:** Although the `plumb_transition_decay` holds draft/beam near the ends, it still results in an uncapped, zero-area closure point.
3. **Unjoined Sheerlines:** The hull and deck are separate surfaces meeting at z=0. If `beam_wl_m` differs from `beam_oa_m`, a gap occurs at the sheerline with no joining geometry.
4. **Test Coverage Gaps:** The test suite extensively verifies the closed-volume contract using `explicit_synthetic_triangle_mesh` fixtures (asserting normals, positive volume, and tolerances). However, there are no tests asserting the closure of generated plumb endpoints or specific sheerline joins.
5. **Display Separation:** Generated hulls currently fail `closed_volume` readiness due to boundary edges. The implementation must ensure the generated closed body is built separately from the existing open display STL surfaces.

## Conclusion
The proposed domain policy is sound and establishes a clear contract for the generated hull-plus-deck evaluation body. I accept the policy with the finding that the subsequent implementation phase must explicitly close the geometric and testing gaps identified above to realize a manifold, watertight volume.
