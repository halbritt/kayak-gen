Verdict intent: accept_with_findings

### Independent Verification
- I verified the coordinate system and geometric assumptions by reviewing `kayakgen/model/geometry.py`. The proposed coordinate/sign conventions match the internal implementation exactly: X moves from `-L/2` at the bow to `+L/2` at the stern, Z is upward, and port/starboard symmetry relies on an implicit reflection over the XZ plane.
- I checked the cross-product orientation of the existing `LoftedHullGeometry` mesh builder to validate the "outward normals" requirement for the assembled closed body against the current surface generation logic.
- Sub-agents used: None (direct review via CLI).

### Findings
1. **Coordinate and Sign Conventions:** Defining rake as dimensionless fullness (0.0 plumb, 1.0 raked) is domain-appropriate, avoids tricky angle trigonometry near vertical, and perfectly respects the existing parameter constraints. The X-axis and Z-axis definitions formally align with the internal math of `LoftedHullGeometry`.
2. **Asymmetric Bow/Stern Rake:** Introducing `stern_rake` while treating the legacy `bow_rake` field as a symmetric fallback is an elegant backward-compatibility design. It enables asymmetric profiles (e.g., plumb bow, raked stern) without invalidating existing serialized `Hull` JSONs.
3. **Exact Endpoint Section Semantics:** Retaining a non-zero section area precisely at `x = \pm L/2` for `rake = 0.0` accurately mirrors the geometry of real-world plumb stems (such as surf skis), which do not taper to zero thickness.
4. **Cap Polygon Winding and Signed Volume:** The RFC correctly mandates positive signed volume and stable outward-facing normals for the closed bodies, adhering to the contract in `kayakgen/eval/closed_volume.py`.
  - *Implementation Caveat:* My analysis of `LoftedHullGeometry.mesh()` shows that the current open hull surface generates faces (`[c1, n1, c2]`) with an upward-pointing (`+Z`) normal component. Since this points *inward* from the hull bottom, the new closed-body builder will need to explicitly invert the hull's face winding during assembly to satisfy the "outward normals" requirement.
5. **Generated Closed-Body Ownership Boundaries:** Delegating the construction of the watertight body to a dedicated builder—while allowing `kayakgen.geometry` to continue generating the open inspection meshes—establishes a clean architectural boundary. This prevents open surfaces from being mistakenly promoted to `cfd_ready`.

### Required Actions
- **Implementation requirement:** The closed-body builder must actively manage face winding (specifically reversing the current open hull surface winding) so that the assembled volume possesses strictly outward normals.
- No changes to the RFC text are required. Proceed with the proposed implementation path.
