"""Reserved heavy-CFD evaluator boundary.

RFC 0007 and RFC 0008 reserve this module for external solver integration.
The current package exposes the boundary explicitly so imports fail with a
clear message instead of looking like a missing module.
"""

from __future__ import annotations


class CfdNotImplementedError(NotImplementedError):
    """Raised when the reserved heavy-CFD evaluator is invoked."""


def evaluate_cfd(*_args: object, **_kwargs: object) -> None:
    raise CfdNotImplementedError("heavy CFD evaluation is reserved for a future RFC")
