"""OpenFOAM provenance probe contract and helpers.

Hosts the ``OpenFoamProvenanceProbe`` model and the
``probe_openfoam_provenance`` runner. Split out from the historical
``kayakgen.eval.cfd.jobs`` per Phase 3A of
``ARCHITECTURE_RECOMMENDATION_PLAN_2026-05-16.md``.

``kayakgen.eval.evidence.openfoam`` continues to re-export
``OpenFoamProvenanceProbe`` for neutral-import callers; this module is now
its canonical home inside the CFD subpackage.
"""

from __future__ import annotations

import os
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field

OpenFoamProbeRunner = Callable[[list[str]], tuple[int, str, str]]
OPENFOAM_PROBE_COMMANDS: dict[str, list[str]] = {
    "application": ["interFoam", "-help"],
    "build": ["foamVersion", "-build"],
    "api": ["foamVersion", "-api"],
    "project_version": ["foamVersion"],
}


class OpenFoamProvenanceProbe(BaseModel):
    """Deterministic v2512 application/build/API provenance record.

    Per workflow 0052 D004 the OpenFOAM-v2512 dispatch decision must derive
    provenance from solver-reported probes (application name, build hash,
    API version) and never trust ``$WM_PROJECT_VERSION`` alone. Tests inject
    probe outputs through ``probe_openfoam_provenance`` to keep CI offline.
    """

    model_config = ConfigDict(extra="forbid")

    application: str | None = None
    build: str | None = None
    api: str | None = None
    project_version: str | None = None
    env_project_version: str | None = None
    raw: dict[str, str] = Field(default_factory=dict)

    def matches_required(self, required: str) -> tuple[bool, str | None]:
        """Return (accepted, reason_if_rejected) for a required version token."""
        if not required:
            return True, None
        # Require at least one solver-reported probe channel (not env) to mention
        # the required token. ``project_version`` is also acceptable when it came
        # from ``foamVersion`` rather than the bare environment variable.
        accepted_channels = {
            "application": self.application,
            "build": self.build,
            "api": self.api,
            "project_version": self.project_version,
        }
        matched = [name for name, value in accepted_channels.items() if value and required in value]
        if matched:
            return True, None
        if self.env_project_version and required in self.env_project_version:
            return (
                False,
                (
                    "OpenFOAM provenance rejected: required "
                    f"{required!r} only present in $WM_PROJECT_VERSION; "
                    "application/build/API probes did not confirm v2512"
                ),
            )
        return (
            False,
            f"OpenFOAM provenance rejected: no probe channel reported {required!r}",
        )


def _first_nonempty_line(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def probe_openfoam_provenance(
    *,
    runner: OpenFoamProbeRunner,
    env: dict[str, str] | None = None,
    commands: dict[str, list[str]] | None = None,
) -> OpenFoamProvenanceProbe:
    """Probe v2512 provenance across application/build/API channels.

    The runner is injected so unit tests can supply deterministic probe output
    without invoking the real OpenFOAM binary. ``$WM_PROJECT_VERSION`` is read
    only as ``env_project_version`` and is intentionally NOT trusted as the
    sole evidence of v2512 (per workflow 0052 D004).
    """
    probe_commands = commands or OPENFOAM_PROBE_COMMANDS
    raw: dict[str, str] = {}
    channels: dict[str, str | None] = {
        "application": None,
        "build": None,
        "api": None,
        "project_version": None,
    }
    for channel, command in probe_commands.items():
        try:
            returncode, stdout, stderr = runner(list(command))
        except (FileNotFoundError, PermissionError, OSError) as exc:
            raw[f"{channel}_error"] = str(exc)
            continue
        if returncode != 0:
            raw[f"{channel}_returncode"] = str(returncode)
            continue
        text = (stdout or "") + ("\n" + stderr if stderr else "")
        raw[channel] = text.strip()
        channels[channel] = _first_nonempty_line(text)
    env_value = None
    if env is not None:
        env_value = env.get("WM_PROJECT_VERSION")
    elif "WM_PROJECT_VERSION" in os.environ:
        env_value = os.environ["WM_PROJECT_VERSION"]
    return OpenFoamProvenanceProbe(
        application=channels["application"],
        build=channels["build"],
        api=channels["api"],
        project_version=channels["project_version"],
        env_project_version=env_value,
        raw=raw,
    )


__all__ = [
    "OPENFOAM_PROBE_COMMANDS",
    "OpenFoamProbeRunner",
    "OpenFoamProvenanceProbe",
    "probe_openfoam_provenance",
]
