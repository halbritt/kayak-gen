"""Tests for the persistent ``~/.config/kayakgen/cfd.json`` loader (RFC 0046)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from kayakgen.eval.cfd.config import (
    KayakgenCfdConfig,
    KayakgenCfdConfigError,
    load_kayakgen_cfd_config,
)


def test_kayakgen_cfd_config_loads_empty_when_file_absent(tmp_path: Path) -> None:
    """A missing config file yields an empty default config, not an error."""
    missing = tmp_path / "does-not-exist.json"

    config = load_kayakgen_cfd_config(missing)

    assert isinstance(config, KayakgenCfdConfig)
    assert config.allow_real_solver_execution_profiles == []


def test_kayakgen_cfd_config_loads_profile_list(tmp_path: Path) -> None:
    """A well-formed config exposes the parsed profile allowlist."""
    config_path = tmp_path / "cfd.json"
    config_path.write_text(
        json.dumps(
            {
                "allow_real_solver_execution_profiles": [
                    "openfoam-v2512-interfoam-local",
                    "another-solver-profile",
                ],
            }
        )
    )

    config = load_kayakgen_cfd_config(config_path)

    assert config.allow_real_solver_execution_profiles == [
        "openfoam-v2512-interfoam-local",
        "another-solver-profile",
    ]


def test_kayakgen_cfd_config_rejects_malformed_json(tmp_path: Path) -> None:
    """Malformed JSON raises a structured error rather than crashing the loader."""
    config_path = tmp_path / "cfd.json"
    config_path.write_text("{this is not valid json")

    with pytest.raises(KayakgenCfdConfigError) as excinfo:
        load_kayakgen_cfd_config(config_path)

    assert excinfo.value.code == "cfd_config_malformed_json"


def test_kayakgen_cfd_config_rejects_unknown_keys(tmp_path: Path) -> None:
    """Strict schema validation rejects typos so opt-ins do not silently disable."""
    config_path = tmp_path / "cfd.json"
    config_path.write_text(
        json.dumps(
            {
                "allow_real_solver_execution_profiles": [
                    "openfoam-v2512-interfoam-local"
                ],
                "totally_unknown_key": True,
            }
        )
    )

    with pytest.raises(KayakgenCfdConfigError) as excinfo:
        load_kayakgen_cfd_config(config_path)

    assert excinfo.value.code == "cfd_config_schema_mismatch"
