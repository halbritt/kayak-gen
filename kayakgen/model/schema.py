"""JSON schema helpers for the Hull aggregate."""

from __future__ import annotations

from typing import Any

from kayakgen.model.hull import Hull


def hull_json_schema() -> dict[str, Any]:
    """Return the Pydantic JSON schema for :class:`Hull`."""
    return Hull.model_json_schema()
