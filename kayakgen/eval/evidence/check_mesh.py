"""``checkMesh`` evidence contracts.

Re-exports ``CheckMeshSummary`` from ``kayakgen.eval.snappy_hex_mesh`` so
new evidence-binding code can import it without pulling in the full
snappyHexMesh harness.
"""

from __future__ import annotations

from kayakgen.eval.snappy_hex_mesh import CheckMeshSummary

__all__ = ["CheckMeshSummary"]
