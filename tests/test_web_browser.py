"""Optional real-browser smoke checks for RFC 0008.

These tests are deliberately optional: the default test suite should remain
usable without a browser binary. To run them:

    pip install -e ".[web,browser]"
    python -m playwright install chromium
    python -m pytest tests/test_web_browser.py -q
"""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from contextlib import closing
from urllib.error import URLError
from urllib.request import urlopen

import pytest


def _free_port() -> int:
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _wait_for_http(url: str, proc: subprocess.Popen[str], timeout_s: float = 30.0) -> None:
    deadline = time.monotonic() + timeout_s
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if proc.poll() is not None:
            stdout, stderr = proc.communicate(timeout=1)
            raise AssertionError(
                "kayakgen serve exited before accepting HTTP connections\n"
                f"stdout:\n{stdout}\nstderr:\n{stderr}"
            )
        try:
            with urlopen(url, timeout=1.0) as response:
                if response.status < 500:
                    return
        except (OSError, URLError) as exc:
            last_error = exc
        time.sleep(0.25)
    raise AssertionError(f"timed out waiting for {url}: {last_error}")


def test_kayakgen_serve_loads_in_chromium_and_updates_metrics() -> None:
    playwright_api = pytest.importorskip(
        "playwright.sync_api",
        reason=(
            "Playwright is not installed; run `pip install -e '.[web,browser]'` "
            "and `python -m playwright install chromium` to enable browser smoke tests"
        ),
    )
    port = _free_port()
    url = f"http://127.0.0.1:{port}/"
    proc = subprocess.Popen(
        [
            sys.executable,
            "-m",
            "kayakgen.cli.main",
            "serve",
            "--host",
            "127.0.0.1",
            "--port",
            str(port),
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        _wait_for_http(url, proc)
        with playwright_api.sync_playwright() as pw:
            try:
                browser = pw.chromium.launch(headless=True)
            except playwright_api.Error as exc:
                pytest.skip(
                    "Chromium is not installed for Playwright; run "
                    "`python -m playwright install chromium` to enable this test. "
                    f"Original error: {exc}"
                )
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                page.goto(url, wait_until="networkidle", timeout=30_000)
                page.get_by_text("kayakgen").first.wait_for(timeout=10_000)
                page.get_by_text("Length (m)").first.wait_for(timeout=10_000)
                page.get_by_text("Metrics").first.wait_for(timeout=10_000)
                page.get_by_text("Displacement").first.wait_for(timeout=10_000)

                before = page.locator("pre").first.inner_text(timeout=10_000)
                sliders = page.get_by_role("slider")
                assert sliders.count() > 0
                sliders.first.focus()
                page.keyboard.press("ArrowRight")
                page.wait_for_function(
                    "before => document.querySelector('pre')?.innerText !== before",
                    arg=before,
                    timeout=10_000,
                )
            finally:
                browser.close()
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=5)
