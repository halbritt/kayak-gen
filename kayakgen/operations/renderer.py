"""Observe gate rendering and coordinate the host's hardware renderer."""

from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time


RENDERER_ENV_KEYS = (
    "LIBGL_ALWAYS_SOFTWARE",
    "__EGL_VENDOR_LIBRARY_FILENAMES",
    "VTK_DEFAULT_OPENGL_WINDOW",
)
HARDWARE_LOCK = Path.home() / ".cache/kayakgen-release-gate.lock"
MESA_VENDOR = Path("/usr/share/glvnd/egl_vendor.d/50_mesa.json")
NVIDIA_GL = re.compile(r"lib(?:EGL_nvidia|GLX_nvidia|nvidia-(?:eglcore|glcore|glsi))", re.I)


class RendererRefused(ValueError):
    """The observed renderer does not satisfy the selected gate profile."""


def observe_renderer() -> dict:
    """Create a real offscreen context in this disposable probe process."""
    from vtkmodules.vtkCommonCore import vtkVersion
    from vtkmodules.vtkRenderingCore import vtkRenderer, vtkRenderWindow
    import vtkmodules.vtkRenderingOpenGL2  # noqa: F401 -- register OpenGL factories

    window = vtkRenderWindow()
    window.SetOffScreenRendering(1)
    window.SetSize(32, 32)
    window.AddRenderer(vtkRenderer())
    try:
        window.Render()
        capabilities = window.ReportCapabilities()
        observed = {}
        for key in ("vendor", "renderer", "version"):
            match = re.search(rf"^OpenGL {key} string:\s*(.+)$", capabilities, re.MULTILINE)
            if match is None:
                raise RendererRefused(f"actual context omitted OpenGL {key}")
            observed["opengl_" + key] = match.group(1).strip()
        libraries = sorted({
            line.split()[-1]
            for line in Path("/proc/self/maps").read_text().splitlines()
            if "/" in line and re.search(
                r"/(?:lib(?:EGL|GL|OpenGL|OSMesa|nvidia|LLVM|gallium)|[^/]+_dri\.so)", line
            )
        })
        return {
            "status": "observed", "vtk_version": vtkVersion.GetVTKVersion(),
            "window_class": window.GetClassName(), "capabilities": capabilities,
            "gl_libraries": libraries,
            "nvidia_opengl_loaded": any(NVIDIA_GL.search(path) for path in libraries),
            **observed,
        }
    finally:
        window.Finalize()


def renderer_kind(actual: dict) -> str:
    vendor = actual["opengl_vendor"].lower()
    renderer = actual["opengl_renderer"].lower()
    if ("mesa" in vendor and any(name in renderer for name in ("llvmpipe", "softpipe"))
            and not actual["nvidia_opengl_loaded"] and actual["gl_libraries"]):
        return "software"
    if "nvidia" in vendor and actual["nvidia_opengl_loaded"]:
        return "hardware"
    raise RendererRefused("unsupported or contradictory actual renderer evidence")


@contextmanager
def hardware_lock(path: Path = HARDWARE_LOCK):
    """Hold the existing advisory lock without replacing or deleting its inode."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def probe_renderer(environment: dict[str, str], evidence: dict) -> dict:
    argv = [sys.executable, "-B", "-m", "kayakgen.operations.renderer", "probe"]
    started = time.monotonic()
    evidence["probe"] = {"argv": argv, "status": "running", "exit_code": None}
    try:
        completed = subprocess.run(argv, env=environment, capture_output=True,
                                   text=True, timeout=30)
    except subprocess.TimeoutExpired as exc:
        evidence["probe"].update(status="timed_out", duration_seconds=time.monotonic() - started)
        raise RendererRefused("actual renderer probe exceeded 30 seconds") from exc
    except BaseException:
        # subprocess.run reaps its one probe child on exceptions, including the
        # gate's signal exception; preserve the incomplete probe outcome too.
        evidence["probe"].update(status="interrupted_or_failed",
                                 duration_seconds=time.monotonic() - started)
        raise
    evidence["probe"].update(
        status="passed" if completed.returncode == 0 else "failed",
        exit_code=completed.returncode, duration_seconds=time.monotonic() - started,
        stderr=completed.stderr,
    )
    if completed.returncode != 0:
        raise RendererRefused(f"actual renderer probe failed with exit {completed.returncode}")
    try:
        actual = json.loads(completed.stdout)
        if actual["status"] != "observed":
            raise ValueError("probe did not observe a context")
    except (ValueError, KeyError, TypeError) as exc:
        raise RendererRefused("actual renderer probe returned invalid evidence") from exc
    evidence["actual"] = actual
    return actual


@contextmanager
def rendering_profile(mode: str, evidence: dict):
    """Yield the exact environment checked by the probe, under its resource policy."""
    if mode not in {"software", "hardware"}:
        raise RendererRefused("renderer profile must be software or hardware")
    environment = os.environ.copy()
    evidence.update(requested_mode=mode,
        declared={key: environment.get(key) for key in RENDERER_ENV_KEYS},
        actual={"status": "unobserved", "reason": "renderer probe has not completed"})
    if mode == "software":
        if not MESA_VENDOR.is_file():
            raise RendererRefused(f"supported Mesa EGL vendor file is missing: {MESA_VENDOR}")
        vendor = json.loads(MESA_VENDOR.read_text())
        if vendor["ICD"]["library_path"] != "libEGL_mesa.so.0":
            raise RendererRefused("Mesa vendor file no longer names the supported library")
        environment.update(LIBGL_ALWAYS_SOFTWARE="1",
            __EGL_VENDOR_LIBRARY_FILENAMES=str(MESA_VENDOR),
            VTK_DEFAULT_OPENGL_WINDOW="vtkEGLRenderWindow")
    evidence["effective"] = {key: environment.get(key) for key in RENDERER_ENV_KEYS}
    evidence["coordination"] = {"policy": "independent_verified_software" if mode == "software"
        else "exclusive_hardware", "lock_path": str(HARDWARE_LOCK) if mode == "hardware" else None,
        "state": "waiting" if mode == "hardware" else "probing"}
    if mode == "hardware":
        with hardware_lock(HARDWARE_LOCK):
            evidence["coordination"]["state"] = "held"
            try:
                actual = probe_renderer(environment, evidence)
                if renderer_kind(actual) != mode:
                    raise RendererRefused("hardware profile selected a software renderer")
                yield environment
            finally:
                evidence["coordination"]["state"] = "released"
    else:
        actual = probe_renderer(environment, evidence)
        if renderer_kind(actual) != mode:
            raise RendererRefused("software profile selected a hardware renderer; gate refused")
        evidence["coordination"]["state"] = "verified"
        yield environment


def main() -> int:
    if sys.argv[1:] != ["probe"]:
        print("usage: python -m kayakgen.operations.renderer probe", file=sys.stderr)
        return 2
    print(json.dumps(observe_renderer()))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
