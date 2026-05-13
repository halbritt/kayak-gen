"""Real-browser checks for the RFC 0008/RFC 0032 web frontend.

The default invocation remains optional and self-skips when browser tooling is
not installed:

    python -m pytest tests/test_web_browser.py -q

The browser-acceptance profile is deliberate and must fail when Playwright or
Chromium is missing:

    python -m pytest tests/test_web_browser.py -m browser_acceptance \
      --browser-acceptance -q
"""

from __future__ import annotations

import os
import socket
import struct
import subprocess
import sys
import time
import zlib
from contextlib import closing
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from kayakgen.model.hull import Hull
from kayakgen.ui.web.state import hull_from_query_string, state_dict_from_hull

PLAYWRIGHT_SETUP = (
    "Install browser tooling with `pip install -e '.[web,browser]'` and "
    "`python -m playwright install chromium`."
)
RENDER_SELECTOR = "canvas, img, [class*='vtk'], [class*='Vtk']"


def _browser_acceptance_required(request: pytest.FixtureRequest) -> bool:
    env = os.environ.get("KAYAKGEN_BROWSER_ACCEPTANCE", "").lower()
    return bool(request.config.getoption("--browser-acceptance")) or env in {
        "1",
        "true",
        "yes",
    }


def _load_playwright(request: pytest.FixtureRequest):
    try:
        import playwright.sync_api as playwright_api
    except ImportError:
        if _browser_acceptance_required(request):
            pytest.fail(f"Playwright is required for browser acceptance. {PLAYWRIGHT_SETUP}")
        pytest.skip(f"Playwright is not installed. {PLAYWRIGHT_SETUP}")
    return playwright_api


def _launch_chromium(playwright_api, pw, request: pytest.FixtureRequest):
    try:
        return pw.chromium.launch(headless=True)
    except playwright_api.Error as exc:
        message = f"Chromium is required for browser acceptance. {PLAYWRIGHT_SETUP} {exc}"
        if _browser_acceptance_required(request):
            pytest.fail(message)
        pytest.skip(message)


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


def _start_server() -> tuple[str, subprocess.Popen[str]]:
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
    _wait_for_http(url, proc)
    return url, proc


def _stop_server(proc: subprocess.Popen[str]) -> None:
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=5)


def _collect_browser_failures(page, failures: list[str] | None = None) -> list[str]:
    if failures is None:
        failures = []

    def on_console(message) -> None:
        if message.type in {"error", "warning"}:
            text = message.text
            if message.type == "warning" and "mixed content" not in text.lower():
                return
            failures.append(f"console {message.type}: {text}")

    def on_page_error(exc: Exception) -> None:
        failures.append(f"pageerror: {exc}")

    def on_request_failed(request) -> None:
        failure = request.failure or {}
        failures.append(f"requestfailed: {request.method} {request.url} {failure}")

    def on_response(response) -> None:
        if response.status < 400:
            return
        if not response.url.startswith("http://127.0.0.1:"):
            return
        failures.append(f"http {response.status}: {response.request.method} {response.url}")

    page.on("console", on_console)
    page.on("pageerror", on_page_error)
    page.on("requestfailed", on_request_failed)
    page.on("response", on_response)
    return failures


def _assert_no_browser_failures(failures: list[str]) -> None:
    assert failures == [], "unexpected browser failures:\n" + "\n".join(failures)


def _metrics_text(page) -> str:
    return page.locator("pre").first.inner_text(timeout=10_000)


def _share_url_value(page) -> str:
    values = page.locator("input").evaluate_all("(els) => els.map((el) => el.value)")
    return next(value for value in values if value.startswith("?hull="))


def _wait_for_render_candidate(page) -> int:
    page.wait_for_function(
        """
        (selector) => Array.from(document.querySelectorAll(selector)).some((el) => {
          const rect = el.getBoundingClientRect();
          return rect.width >= 200 && rect.height >= 200;
        })
        """,
        arg=RENDER_SELECTOR,
        timeout=20_000,
    )
    return int(
        page.evaluate(
            """
            (selector) => {
              const entries = Array.from(document.querySelectorAll(selector))
                .map((el, index) => {
                  const rect = el.getBoundingClientRect();
                  return { index, area: rect.width * rect.height };
                })
                .filter((entry) => entry.area > 0)
                .sort((a, b) => b.area - a.area);
              return entries[0].index;
            }
            """,
            arg=RENDER_SELECTOR,
        )
    )


def _assert_nonblank_3d(page) -> None:
    index = _wait_for_render_candidate(page)
    candidate = page.locator(RENDER_SELECTOR).nth(index)
    box = candidate.bounding_box(timeout=10_000)
    assert box is not None
    assert box["width"] >= 200
    assert box["height"] >= 200
    png = candidate.screenshot(timeout=10_000)
    min_rgb, max_rgb = _png_rgb_range(png)
    assert max_rgb - min_rgb > 8


def _png_rgb_range(png: bytes) -> tuple[int, int]:
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    pos = 8
    width = height = color_type = None
    compressed = bytearray()
    while pos < len(png):
        length = struct.unpack(">I", png[pos : pos + 4])[0]
        chunk_type = png[pos + 4 : pos + 8]
        data = png[pos + 8 : pos + 8 + length]
        pos += 12 + length
        if chunk_type == b"IHDR":
            width, height, bit_depth, color_type, _comp, _filter, _interlace = struct.unpack(
                ">IIBBBBB", data
            )
            assert bit_depth == 8
        elif chunk_type == b"IDAT":
            compressed.extend(data)
        elif chunk_type == b"IEND":
            break
    assert width is not None and height is not None and color_type is not None
    channels_by_type = {0: 1, 2: 3, 4: 2, 6: 4}
    channels = channels_by_type[color_type]
    raw = zlib.decompress(bytes(compressed))
    stride = width * channels
    prev = bytearray(stride)
    offset = 0
    min_rgb = 255
    max_rgb = 0
    for _row in range(height):
        filter_type = raw[offset]
        offset += 1
        scan = bytearray(raw[offset : offset + stride])
        offset += stride
        _unfilter_png_scanline(scan, prev, filter_type, channels)
        for idx in range(0, stride, channels):
            if color_type == 0:
                rgb = (scan[idx], scan[idx], scan[idx])
            elif color_type == 4:
                rgb = (scan[idx], scan[idx], scan[idx])
            else:
                rgb = (scan[idx], scan[idx + 1], scan[idx + 2])
            min_rgb = min(min_rgb, *rgb)
            max_rgb = max(max_rgb, *rgb)
        prev = scan
    return min_rgb, max_rgb


def _unfilter_png_scanline(
    scan: bytearray,
    prev: bytearray,
    filter_type: int,
    channels: int,
) -> None:
    for idx, value in enumerate(scan):
        left = scan[idx - channels] if idx >= channels else 0
        up = prev[idx]
        up_left = prev[idx - channels] if idx >= channels else 0
        if filter_type == 0:
            predictor = 0
        elif filter_type == 1:
            predictor = left
        elif filter_type == 2:
            predictor = up
        elif filter_type == 3:
            predictor = (left + up) // 2
        elif filter_type == 4:
            predictor = _paeth(left, up, up_left)
        else:
            raise AssertionError(f"unsupported PNG filter: {filter_type}")
        scan[idx] = (value + predictor) & 0xFF


def _paeth(a: int, b: int, c: int) -> int:
    p = a + b - c
    pa = abs(p - a)
    pb = abs(p - b)
    pc = abs(p - c)
    if pa <= pb and pa <= pc:
        return a
    if pb <= pc:
        return b
    return c


def _assert_stl_response(stl: dict[str, object]) -> None:
    assert stl["status"] == 200
    assert "application/sla" in str(stl["content_type"])
    length = int(stl["length"])
    tri_count = int(stl["triangle_count"])
    assert length == 84 + tri_count * 50
    assert tri_count > 0


@pytest.mark.browser_acceptance
def test_kayakgen_serve_browser_acceptance(request: pytest.FixtureRequest) -> None:
    playwright_api = _load_playwright(request)
    url, proc = _start_server()
    try:
        with playwright_api.sync_playwright() as pw:
            browser = _launch_chromium(playwright_api, pw, request)
            try:
                page = browser.new_page(viewport={"width": 1280, "height": 900})
                failures = _collect_browser_failures(page)

                page.goto(url, wait_until="networkidle", timeout=30_000)
                page.get_by_text("kayakgen").first.wait_for(timeout=10_000)
                page.get_by_text("Length (m)").first.wait_for(timeout=10_000)
                page.get_by_text("Metrics").first.wait_for(timeout=10_000)
                page.get_by_text("Hydrostatics").first.wait_for(timeout=10_000)
                page.get_by_text("Displacement").first.wait_for(timeout=10_000)
                page.get_by_text("GM0").first.wait_for(timeout=10_000)
                page.get_by_text("Resistance curve (raw comparative filter)").first.wait_for(
                    timeout=10_000
                )
                page.get_by_text("comparative_filter_only").first.wait_for(timeout=10_000)
                page.get_by_text("Comparison").first.wait_for(timeout=10_000)
                _assert_nonblank_3d(page)

                before = _metrics_text(page)
                sliders = page.get_by_role("slider")
                assert sliders.count() > 0
                sliders.first.focus()
                page.keyboard.press("ArrowRight")
                page.wait_for_function(
                    "before => document.querySelector('pre')?.innerText !== before",
                    arg=before,
                    timeout=10_000,
                )
                mutated_metrics = _metrics_text(page)
                assert mutated_metrics != before
                _assert_nonblank_3d(page)

                page.get_by_role("button", name="Share").click()
                page.wait_for_function(
                    """
                    () => Array.from(document.querySelectorAll('input'))
                      .some((input) => input.value.startsWith('?hull='))
                    """,
                    timeout=10_000,
                )
                page.get_by_text("Shareable URL copied").first.wait_for(timeout=10_000)
                share_path = _share_url_value(page)
                assert share_path.startswith("?hull=")
                shared_hull = hull_from_query_string(share_path)
                assert shared_hull is not None
                assert shared_hull.length_m != Hull().length_m

                reload_page = browser.new_page(viewport={"width": 1280, "height": 900})
                _collect_browser_failures(reload_page, failures)
                reload_page.goto(url + share_path, wait_until="networkidle", timeout=30_000)
                reload_page.wait_for_function(
                    "mutated => document.querySelector('pre')?.innerText === mutated",
                    arg=mutated_metrics,
                    timeout=10_000,
                )
                _assert_nonblank_3d(reload_page)

                default_state = state_dict_from_hull(Hull()) | {"target_speed_kt": 3.5}
                stl = reload_page.evaluate(
                    """
                    async (state) => {
                      const response = await fetch('/api/stl?part=hull', {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(state),
                      });
                      const buffer = await response.arrayBuffer();
                      const view = new DataView(buffer);
                      return {
                        status: response.status,
                        content_type: response.headers.get('content-type'),
                        length: buffer.byteLength,
                        triangle_count: buffer.byteLength >= 84 ? view.getUint32(80, true) : 0,
                      };
                    }
                    """,
                    arg=default_state,
                )
                _assert_stl_response(stl)
                _assert_no_browser_failures(failures)
                reload_page.close()
            finally:
                browser.close()
    finally:
        _stop_server(proc)
