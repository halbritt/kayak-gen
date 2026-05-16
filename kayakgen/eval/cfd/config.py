"""Persistent CFD operator settings.

This module loads the optional ``~/.config/kayakgen/cfd.json`` file that
expresses workstation-wide opt-ins for the local CFD adapters. The
schema is strict: unknown keys are rejected so that typos do not
silently disable opt-ins.

The persistent setting is one of three opt-in mechanisms for the
``openfoam-v2512-interfoam-local`` succeeded path; see RFC 0046 for the
precedence rules.
"""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, ValidationError

DEFAULT_KAYAKGEN_CFD_CONFIG_PATH = Path.home() / ".config" / "kayakgen" / "cfd.json"


class KayakgenCfdConfigError(ValueError):
    """Raised when ``cfd.json`` cannot be parsed or fails schema validation."""

    def __init__(self, message: str, *, code: str = "cfd_config_error") -> None:
        super().__init__(message)
        self.code = code


class KayakgenCfdConfig(BaseModel):
    """Strict-schema persistent CFD operator settings.

    Today the only honored key is
    ``allow_real_solver_execution_profiles``: a list of solver-profile
    names whose freshly prepared jobs may run the real (non-fixture)
    solver path. Default-empty preserves the conservative posture.
    """

    model_config = ConfigDict(extra="forbid")

    allow_real_solver_execution_profiles: list[str] = Field(default_factory=list)


def load_kayakgen_cfd_config(path: Path | None = None) -> KayakgenCfdConfig:
    """Load the persistent CFD settings file.

    ``path`` defaults to ``~/.config/kayakgen/cfd.json``. If the file is
    absent, an empty :class:`KayakgenCfdConfig` is returned. If the file
    is present but malformed (invalid JSON or schema mismatch), a
    :class:`KayakgenCfdConfigError` is raised with a clear message.
    """
    resolved = path if path is not None else DEFAULT_KAYAKGEN_CFD_CONFIG_PATH
    if not resolved.is_file():
        return KayakgenCfdConfig()
    try:
        text = resolved.read_text()
    except OSError as exc:
        raise KayakgenCfdConfigError(
            f"failed to read kayakgen cfd config at {resolved}: {exc}",
            code="cfd_config_read_error",
        ) from exc
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise KayakgenCfdConfigError(
            f"kayakgen cfd config at {resolved} is not valid JSON: {exc}",
            code="cfd_config_malformed_json",
        ) from exc
    if not isinstance(payload, dict):
        raise KayakgenCfdConfigError(
            f"kayakgen cfd config at {resolved} must be a JSON object",
            code="cfd_config_invalid_root",
        )
    try:
        return KayakgenCfdConfig.model_validate(payload)
    except ValidationError as exc:
        raise KayakgenCfdConfigError(
            f"kayakgen cfd config at {resolved} failed schema validation: {exc}",
            code="cfd_config_schema_mismatch",
        ) from exc


__all__ = [
    "DEFAULT_KAYAKGEN_CFD_CONFIG_PATH",
    "KayakgenCfdConfig",
    "KayakgenCfdConfigError",
    "load_kayakgen_cfd_config",
]
