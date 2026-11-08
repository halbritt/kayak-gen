"""Renderer evidence and resource admission for actual gate callers."""

from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys

import pytest


def test_software_profile_observes_real_mesa_without_nvidia_gl():
    from kayakgen.operations.renderer import rendering_profile

    evidence = {}
    with rendering_profile("software", evidence) as environment:
        assert environment["LIBGL_ALWAYS_SOFTWARE"] == "1"
        assert evidence["actual"]["status"] == "observed"
        assert evidence["actual"]["window_class"] == "vtkEGLRenderWindow"
        assert "Mesa" in evidence["actual"]["opengl_vendor"]
        assert "llvmpipe" in evidence["actual"]["opengl_renderer"].lower()
        assert evidence["actual"]["gl_libraries"]
        assert evidence["actual"]["nvidia_opengl_loaded"] is False
        assert evidence["coordination"]["policy"] == "independent_verified_software"
        assert evidence["probe"]["exit_code"] == 0
    assert os.environ.get("LIBGL_ALWAYS_SOFTWARE") == evidence["declared"]["LIBGL_ALWAYS_SOFTWARE"]


def test_software_profile_refuses_an_observed_nvidia_context_before_caller(monkeypatch):
    from kayakgen.operations import renderer

    actual = {"status": "observed", "opengl_vendor": "NVIDIA Corporation",
              "opengl_renderer": "NVIDIA RTX", "nvidia_opengl_loaded": True,
              "gl_libraries": ["/usr/lib/libEGL_nvidia.so.0"]}

    def observed_nvidia(environment, evidence):
        evidence["actual"] = actual
        return actual

    monkeypatch.setattr(renderer, "probe_renderer", observed_nvidia)
    called = False
    evidence = {}
    with pytest.raises(renderer.RendererRefused, match="software.*hardware"):
        with renderer.rendering_profile("software", evidence):
            called = True
    assert called is False
    assert evidence["actual"] == actual


def test_software_capabilities_do_not_override_loaded_nvidia_gl_evidence():
    from kayakgen.operations.renderer import RendererRefused, renderer_kind

    actual = {"opengl_vendor": "Mesa", "opengl_renderer": "llvmpipe",
              "nvidia_opengl_loaded": True, "gl_libraries": ["/usr/lib/libEGL_nvidia.so.0"]}
    with pytest.raises(RendererRefused, match="contradictory"):
        renderer_kind(actual)


def lock_attempt(path: Path) -> int:
    script = (
        "import fcntl,sys\n"
        "with open(sys.argv[1], 'a+') as lock:\n"
        "    try: fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)\n"
        "    except BlockingIOError: sys.exit(73)\n"
    )
    return subprocess.run([sys.executable, "-c", script, str(path)], timeout=5).returncode


def test_hardware_lease_excludes_another_process_and_releases_on_failure(tmp_path):
    from kayakgen.operations.renderer import hardware_lock

    lock = tmp_path / "renderer.lock"
    with pytest.raises(RuntimeError, match="controlled caller failure"):
        with hardware_lock(lock):
            assert lock_attempt(lock) == 73
            raise RuntimeError("controlled caller failure")
    assert lock_attempt(lock) == 0


def test_hardware_profile_refuses_actual_mesa_and_records_released_lease(tmp_path, monkeypatch):
    from kayakgen.operations import renderer

    lock = tmp_path / "hardware-control.lock"
    monkeypatch.setattr(renderer, "HARDWARE_LOCK", lock)
    monkeypatch.setenv("LIBGL_ALWAYS_SOFTWARE", "1")
    monkeypatch.setenv("__EGL_VENDOR_LIBRARY_FILENAMES", str(renderer.MESA_VENDOR))
    monkeypatch.setenv("VTK_DEFAULT_OPENGL_WINDOW", "vtkEGLRenderWindow")
    evidence = {}
    called = False
    with pytest.raises(renderer.RendererRefused, match="hardware.*software"):
        with renderer.rendering_profile("hardware", evidence):
            called = True
    assert called is False
    assert evidence["probe"]["exit_code"] == 0
    assert "llvmpipe" in evidence["actual"]["opengl_renderer"].lower()
    assert evidence["coordination"]["state"] == "released"
    assert lock_attempt(lock) == 0
