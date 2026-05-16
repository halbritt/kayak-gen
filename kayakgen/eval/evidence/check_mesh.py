"""``checkMesh`` evidence contracts.

Re-exports ``CheckMeshSummary`` from ``kayakgen.eval.snappy_hex_mesh`` so
new evidence-binding code can import it without pulling in the full
snappyHexMesh harness.

Per Phase 2 step 5 of
``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``.
"""

from __future__ import annotations

from kayakgen.eval.snappy_hex_mesh import CheckMeshSummary

__all__ = ["CheckMeshSummary"]
