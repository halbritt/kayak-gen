"""OpenFOAM-side evidence contracts.

This module re-exports the load-bearing ``OpenFoamProvenanceProbe``
contract from its original home in ``kayakgen.eval.cfd.jobs`` so that new
code can import it from a neutral location without taking a dependency on
the full ``jobs`` module (which carries the adapter machinery as well).
"""

from __future__ import annotations

from kayakgen.eval.cfd.jobs import OpenFoamProvenanceProbe

__all__ = ["OpenFoamProvenanceProbe"]
