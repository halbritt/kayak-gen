"""OpenFOAM provenance probe contract and helpers.

Hosts the ``OpenFoamProvenanceProbe`` model and the
``probe_openfoam_provenance`` runner.

``kayakgen.eval.evidence.openfoam`` continues to re-export
``OpenFoamProvenanceProbe`` for neutral-import callers; this module is now
its canonical home inside the CFD subpackage.
"""

from __future__ import annotations

import os
import re
import subprocess
from collections.abc import Callable

from pydantic import BaseModel, ConfigDict, Field

OpenFoamProbeRunner = Callable[[list[str]], tuple[int, str, str]]
OPENFOAM_PROBE_COMMANDS: dict[str, list[str]] = {
    "application": ["interFoam", "-help"],
    "build": ["foamVersion", "-build"],
    "api": ["foamVersion", "-api"],
    "project_version": ["foamVersion"],
}


# OpenCFD release numbers are YYMM. The case and force parser were first
# qualified on v2512; older output layouts are outside this contract.
MIN_OPENFOAM_RELEASE = "v2512"
_RELEASE = r"([0-9]{2}(?:0[1-9]|1[0-2]))"
_NAMED_RELEASE = re.compile(r"\bOpenFOAM[- ]v?" + _RELEASE + r"(?![a-zA-Z0-9])", re.I)


def openfoam_release(text: str | None) -> str | None:
    """Read an OpenCFD release from solver output (never from a build date)."""
    if not text:
        return None
    releases = set(_NAMED_RELEASE.findall(text))
    api = re.search(r"OpenFOAM[- ]v?[0-9]+\s+\(" + _RELEASE + r"\)", text, re.I)
    if api:
        releases.add(api[1])
    bare = re.fullmatch("v?" + _RELEASE, text.strip())
    if bare:
        releases.add(bare[1])
    if len(releases) == 1:
        return "v" + releases.pop()
    return None


class OpenFoamProvenanceProbe(BaseModel):
    """Solver-reported OpenCFD provenance. The shell version is advisory."""

    model_config = ConfigDict(extra="forbid")

    application: str | None = None
    build: str | None = None
    api: str | None = None
    project_version: str | None = None
    env_project_version: str | None = None
    raw: dict[str, str] = Field(default_factory=dict)

    @property
    def release(self) -> str | None:
        """Require agreement among the version-bearing solver channels."""
        # Older runners prepended an environment-derived summary to the real
        # banner. Only the Using line in that archived transcript is evidence.
        channels = [self.application, self.build, self.api, self.project_version]
        if self.application and "application=interFoam" in self.application:
            channels = [next((line for line in self.raw.get("application", "").splitlines()
                              if line.startswith("Using:")), None)]
        releases = set()
        for value in filter(None, channels):
            release = openfoam_release(value)
            if release:
                releases.add(release)
            elif _NAMED_RELEASE.search(value):
                return None
        return releases.pop() if len(releases) == 1 else None

    def matches_required(self, required: str | None = None) -> tuple[bool, str | None]:
        release = self.release
        if release is None:
            return False, "Missing or conflicting solver release; $WM_PROJECT_VERSION is insufficient"
        if required is not None and openfoam_release(required) != release:
            return False, f"OpenFOAM release {release} differs from required {required!r}"
        if release < MIN_OPENFOAM_RELEASE:
            return False, f"OpenFOAM release {release} predates supported {MIN_OPENFOAM_RELEASE}"
        return True, None


def _first_nonempty_line(text: str) -> str | None:
    for line in text.splitlines():
        stripped = line.strip()
        if stripped:
            return stripped
    return None


def application_probe(text: str) -> OpenFoamProvenanceProbe:
    """Extract the application and build from one solver invocation."""
    lines = [line.strip() for line in text.splitlines()]
    banner = next((line for line in lines if line.startswith("Using:")), None)
    build = next((line.removeprefix("Build:").strip() for line in lines
                  if line.startswith("Build:")), None)
    return OpenFoamProvenanceProbe(application=banner or _first_nonempty_line(text),
                                   build=build, raw={"application": text.strip()})


def probe_openfoam_provenance(
    *,
    runner: OpenFoamProbeRunner,
    env: dict[str, str] | None = None,
    commands: dict[str, list[str]] | None = None,
) -> OpenFoamProvenanceProbe:
    """Probe OpenCFD provenance across application/build/API channels.

    The runner is injected so unit tests can supply deterministic probe output
    without invoking the real OpenFOAM binary. ``$WM_PROJECT_VERSION`` is read
    only as ``env_project_version`` and is intentionally NOT trusted as the
    sole evidence of a solver release.
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
        except (OSError, subprocess.TimeoutExpired) as exc:
            raw[f"{channel}_error"] = str(exc)
            continue
        if returncode != 0:
            raw[f"{channel}_returncode"] = str(returncode)
            continue
        text = (stdout or "") + ("\n" + stderr if stderr else "")
        raw[channel] = text.strip()
        channels[channel] = _first_nonempty_line(text)
        if channel == "application":
            probe = application_probe(text)
            channels[channel] = probe.application
            if probe.build:
                channels["build"] = probe.build
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
