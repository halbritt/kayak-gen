# Task — review math/physics correctness

Read the items listed in `docs/workflows/0009-multi-lane-review/SOURCES.md`,
plus the diffs landed by the seven feature branches and their RFCs.

Write your review at the path the runner gives you under
`striatum/0009-multi-lane-review/codex/REVIEW_MATH.md`. Use the
template below.

```markdown
# Math / physics review — RFCs 0004, 0005, 0006, 0007

## Summary

One paragraph. What did you check, what's solid, what's the most
concerning math finding.

## Findings

### F-MATH-001 — <short title>
- Severity: blocker | major | minor | nit
- RFC: NNNN, section
- File: kayakgen/eval/<file>.py:<line>
- What you found: <2-4 sentences>
- Suggested remediation: <1-3 sentences>
- Reproduction or evidence: <commands run, numerical comparison, citation>

### F-MATH-002 — ...
```

## Specific things to verify

1. **Hydrostatics** (`kayakgen/eval/hydrostatics.py`):
   - Divergence-theorem `_signed_volume` with the open hull bounded
     above by z=0 — does the cap really contribute zero?
   - `_waterplane_area` extracts the topmost ring and projects to z=0;
     correct for the lofted hull?
   - `LCB_frac` formula. Re-derive.
   - `Cp_actual = volume / (midship_area × L)` and `Cm_actual = midship_area / (B × T)`.
2. **Resistance** (`kayakgen/eval/resistance.py`):
   - Check the prefactor. The implementer claims `16ρg²/(πV²)` with a
     port/starboard × fore/aft symmetry argument; verify against a
     published derivation.
   - Wigley calibration in `tests/test_resistance.py`. Does Cw at
     Fn 0.30 actually agree with literature within 5%?
   - The known limitation about `ε^(-1/2)` end gradients — is the
     mitigation (qualitative tests + Wigley benchmark) sufficient for
     RFC 0005's "fast filter tier" framing?
3. **Geometry** (`kayakgen/model/geometry.py`):
   - `_get_area_fraction`, `_end_decay` blend, `_half_beam_for_part`.
     Does the blend preserve volume continuously across `bow_rake ∈ [0, 1]`?
   - `beam_wl_m` semantics: hull uses `B_wl`, deck uses `B_oa`.
     Acceptable? What happens at z=0 between them — is the gap intentional?
4. **Constraints document** (`docs/design/kayak_hull_design_constraints.md`):
   - The four class presets (`kayakgen/model/classes.py`) — do their
     ranges match §4 / §9?

Cite specific lines and equations. Be willing to flag "I cannot tell
from the code; needs a unit test" as a finding.
