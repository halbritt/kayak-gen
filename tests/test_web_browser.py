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
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest

from kayakgen.model.hull import Hull
from kayakgen.ui import theme
from kayakgen.ui.web.state import hull_from_query_string, state_dict_from_hull

PLAYWRIGHT_SETUP = (
    "Install browser tooling with `pip install -e '.[web,browser]'` and "
    "`python -m playwright install chromium`."
)
RENDER_SELECTOR = "canvas, img, [class*='vtk'], [class*='Vtk']"
VISUAL_BASELINE_DIR = Path(__file__).parent / "visual_baselines"
VISUAL_MASK_FILL = "#f3f4f6"
VISUAL_PIXEL_CHANNEL_TOLERANCE = 8
VISUAL_MISMATCH_PIXEL_RATIO = 0.02
A11Y_MIN_HIT_TARGET_PX = 24


@dataclass(frozen=True)
class VisualViewport:
    name: str
    width: int
    height: int


VISUAL_VIEWPORTS: tuple[VisualViewport, ...] = (
    VisualViewport("1440x900", 1440, 900),
    VisualViewport("1024x768", 1024, 768),
    VisualViewport("960x720", 960, 720),
)


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


def _load_playwright_optional(request: pytest.FixtureRequest):
    try:
        import playwright.sync_api as playwright_api
    except ImportError:
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


def _launch_chromium_optional(playwright_api, pw):
    try:
        return pw.chromium.launch(headless=True)
    except playwright_api.Error as exc:
        pytest.skip(f"Chromium is not installed. {PLAYWRIGHT_SETUP} {exc}")


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


def _wait_for_workspace_shell(page) -> None:
    page.get_by_text("kayakgen").first.wait_for(timeout=10_000)
    page.get_by_text("Length (m)").first.wait_for(timeout=10_000)
    page.get_by_text("Metrics").first.wait_for(timeout=10_000)
    page.get_by_text("Hydrostatics").first.wait_for(timeout=10_000)


def _mask_vtk_viewport(page) -> None:
    page.evaluate(
        """
        ({selector, fill}) => {
          document.querySelectorAll(".kg-visual-mask").forEach((el) => el.remove());
          const targets = Array.from(document.querySelectorAll(selector))
            .filter((el) => {
              const rect = el.getBoundingClientRect();
              return rect.width > 0 && rect.height > 0;
            });
          if (targets.length === 0) {
            throw new Error(`no VTK viewport found for visual mask: ${selector}`);
          }
          for (const target of targets) {
            const rect = target.getBoundingClientRect();
            const mask = document.createElement("div");
            mask.className = "kg-visual-mask";
            mask.setAttribute("data-testid", "visual-vtk-mask");
            Object.assign(mask.style, {
              position: "fixed",
              left: `${rect.left}px`,
              top: `${rect.top}px`,
              width: `${rect.width}px`,
              height: `${rect.height}px`,
              background: fill,
              zIndex: "2147483647",
              pointerEvents: "none",
            });
            document.body.appendChild(mask);
          }
        }
        """,
        arg={
            "selector": "[data-testid='geometry-vtk-view'], .kg-vtk-viewport",
            "fill": VISUAL_MASK_FILL,
        },
    )


def _capture_masked_workspace_png(page, viewport: VisualViewport) -> bytes:
    _wait_for_workspace_shell(page)
    _assert_nonblank_3d(page)
    _mask_vtk_viewport(page)
    page.wait_for_timeout(250)
    png = page.screenshot(full_page=False, timeout=10_000)
    assert _png_size(png) == (viewport.width, viewport.height)
    return png


@dataclass(frozen=True)
class VisualCompareResult:
    passed: bool
    mismatch_ratio: float
    max_channel_delta: int
    actual_path: Path
    diff_path: Path


def _compare_visual_png(
    *,
    actual_png: bytes,
    baseline_path: Path,
    output_dir: Path,
    viewport_name: str,
) -> VisualCompareResult:
    try:
        from PIL import Image, ImageChops
    except ImportError:
        pytest.skip("Pillow is required for visual-baseline comparison.")

    output_dir.mkdir(parents=True, exist_ok=True)
    actual_path = output_dir / f"{viewport_name}.actual.png"
    diff_path = output_dir / f"{viewport_name}.diff.png"
    actual_path.write_bytes(actual_png)

    actual = Image.open(actual_path).convert("RGBA")
    expected = Image.open(baseline_path).convert("RGBA")
    if actual.size != expected.size:
        diff = Image.new("RGBA", actual.size, (255, 0, 255, 255))
        diff.save(diff_path)
        return VisualCompareResult(
            passed=False,
            mismatch_ratio=1.0,
            max_channel_delta=255,
            actual_path=actual_path,
            diff_path=diff_path,
        )

    diff = ImageChops.difference(actual, expected)
    mismatched = 0
    max_delta = 0
    pixel_count = actual.size[0] * actual.size[1]
    diff_bytes = diff.tobytes()
    for idx in range(0, len(diff_bytes), 4):
        delta = max(diff_bytes[idx], diff_bytes[idx + 1], diff_bytes[idx + 2])
        max_delta = max(max_delta, delta)
        if delta > VISUAL_PIXEL_CHANNEL_TOLERANCE:
            mismatched += 1
    ratio = mismatched / max(1, pixel_count)
    if ratio > VISUAL_MISMATCH_PIXEL_RATIO:
        amplified = diff.point(lambda value: min(255, value * 8))
        amplified.save(diff_path)
        return VisualCompareResult(
            passed=False,
            mismatch_ratio=ratio,
            max_channel_delta=max_delta,
            actual_path=actual_path,
            diff_path=diff_path,
        )
    if diff_path.exists():
        diff_path.unlink()
    return VisualCompareResult(
        passed=True,
        mismatch_ratio=ratio,
        max_channel_delta=max_delta,
        actual_path=actual_path,
        diff_path=diff_path,
    )


def _synthetic_rgba_png(
    size: tuple[int, int],
    fill: tuple[int, int, int, int],
    pixels: dict[tuple[int, int], tuple[int, int, int, int]] | None = None,
) -> bytes:
    Image = pytest.importorskip("PIL.Image", reason="Pillow is required for PNG tests.")
    image = Image.new("RGBA", size, fill)
    for xy, rgba in (pixels or {}).items():
        image.putpixel(xy, rgba)
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def test_compare_visual_png_fails_over_tolerance_and_writes_diff(tmp_path: Path) -> None:
    baseline_path = tmp_path / "baseline.png"
    baseline_path.write_bytes(_synthetic_rgba_png((10, 10), (255, 255, 255, 255)))
    actual_png = _synthetic_rgba_png(
        (10, 10),
        (255, 255, 255, 255),
        {
            (0, 0): (0, 0, 0, 255),
            (1, 0): (0, 0, 0, 255),
            (2, 0): (0, 0, 0, 255),
        },
    )

    result = _compare_visual_png(
        actual_png=actual_png,
        baseline_path=baseline_path,
        output_dir=tmp_path / "diffs",
        viewport_name="synthetic",
    )

    assert result.passed is False
    assert result.mismatch_ratio == pytest.approx(0.03)
    assert result.max_channel_delta == 255
    assert result.actual_path.exists()
    assert result.diff_path.exists()


def test_compare_visual_png_passes_under_mismatch_ratio_without_diff(
    tmp_path: Path,
) -> None:
    baseline_path = tmp_path / "baseline.png"
    baseline_path.write_bytes(_synthetic_rgba_png((10, 10), (255, 255, 255, 255)))
    actual_png = _synthetic_rgba_png(
        (10, 10),
        (255, 255, 255, 255),
        {(0, 0): (0, 0, 0, 255)},
    )

    result = _compare_visual_png(
        actual_png=actual_png,
        baseline_path=baseline_path,
        output_dir=tmp_path / "diffs",
        viewport_name="synthetic",
    )

    assert result.passed is True
    assert result.mismatch_ratio == pytest.approx(0.01)
    assert result.max_channel_delta == 255
    assert result.actual_path.exists()
    assert not result.diff_path.exists()


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


def _png_size(png: bytes) -> tuple[int, int]:
    assert png.startswith(b"\x89PNG\r\n\x1a\n")
    length = struct.unpack(">I", png[8:12])[0]
    chunk_type = png[12:16]
    assert length == 13
    assert chunk_type == b"IHDR"
    width, height = struct.unpack(">II", png[16:24])
    return int(width), int(height)


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


def _assert_stl_response(
    stl: dict[str, object],
    *,
    expected_filename: str | None = None,
) -> None:
    assert stl["status"] == 200
    assert "application/sla" in str(stl["content_type"])
    if expected_filename is not None:
        assert str(stl["content_disposition"]) == (
            f'attachment; filename="{expected_filename}"'
        )
    length = int(stl["length"])
    tri_count = int(stl["triangle_count"])
    assert length == 84 + tri_count * 50
    assert tri_count > 0


def _slider_number(page, key: str, attr: str) -> float:
    value = page.locator(f".kg-param-{key} [role='slider']").first.get_attribute(attr)
    assert value is not None
    return float(value)


def _select_class_preset(page, label: str) -> None:
    page.locator(".kg-class-preset-select").click()
    page.get_by_role("option", name=label, exact=True).click()


def _class_preset_value(page) -> str:
    value = page.evaluate("() => window.trame?.state?.get?.('class_preset')")
    assert isinstance(value, str)
    return value


def _assert_parameter_slider_label_geometry(page) -> None:
    expected = {
        "length_m": "Length (m)",
        "beam_oa_m": "Beam OA (m)",
        "beam_wl_m": "Beam WL (m)",
        "draft_m": "Draft (m)",
        "deck_height_m": "Deck Height (m)",
        "Cp": "Prismatic Cp",
        "Cm": "Midship Cm",
        "deck_flatness": "Deck Flatness",
        "center_box_ratio": "Parallel Mid-Body",
        "bow_rake": "Bow Rake (1=raked)",
        "stern_rake": "Stern Rake (1=raked)",
        "target_speed_kt": "Target Speed (kt)",
    }
    failures = page.evaluate(
        """
        async (expected) => {
          const intersects = (a, b) => (
            a.left < b.right && a.right > b.left && a.top < b.bottom && a.bottom > b.top
          );
          const rectObject = (rect) => ({
            left: rect.left, right: rect.right, top: rect.top, bottom: rect.bottom,
            width: rect.width, height: rect.height,
          });
          const visibleRect = (el) => {
            if (!el) return null;
            const style = window.getComputedStyle(el);
            if (
              style.display === "none"
              || style.visibility === "hidden"
              || Number(style.opacity) === 0
            ) {
              return null;
            }
            const rect = el.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) return null;
            return rectObject(rect);
          };
          const rail = document.querySelector(".kg-parameter-rail");
          const railBoundary = rail?.closest(".v-navigation-drawer") || rail;
          const failures = [];
          if (!visibleRect(railBoundary)) {
            return ["parameter rail has no positive rendered box"];
          }
          for (const [key, expectedLabel] of Object.entries(expected)) {
            const row = document.querySelector(`.kg-param-${key}`);
            if (!row) {
              failures.push(`${key}: missing slider row`);
              continue;
            }
            row.scrollIntoView({ block: "center", inline: "nearest" });
            await new Promise((resolve) => requestAnimationFrame(resolve));
            const railRect = visibleRect(railBoundary);
            if (!railRect) {
              failures.push(`${key}: parameter rail lost its rendered box after scroll`);
              continue;
            }
            const label = row.querySelector(".v-slider__label");
            const labelRect = visibleRect(label);
            const actualLabel = (label?.textContent || "").trim();
            if (actualLabel !== expectedLabel) {
              failures.push(`${key}: label text ${actualLabel} != ${expectedLabel}`);
            }
            const ariaValues = [
              row.getAttribute("aria-label"),
              ...Array.from(row.querySelectorAll("[aria-label]"))
                .map((el) => el.getAttribute("aria-label")),
            ].filter(Boolean);
            if (!ariaValues.includes(expectedLabel)) {
              failures.push(
                `${key}: aria-label values ${ariaValues.join("|")} omit ${expectedLabel}`
              );
            }
            if (!labelRect) {
              failures.push(`${key}: label has no positive rendered box`);
              continue;
            }
            const track = row.querySelector(".v-slider-track");
            const trackRect = visibleRect(track);
            if (
              labelRect.left < railRect.left
              || labelRect.right > railRect.right
              || labelRect.top < railRect.top
              || labelRect.bottom > railRect.bottom
            ) {
              failures.push(`${key}: label is clipped outside parameter rail`);
            }
            if (trackRect && intersects(labelRect, trackRect)) {
              failures.push(`${key}: label intersects slider track`);
            }
            for (const thumbLabel of Array.from(row.querySelectorAll(".v-slider-thumb__label"))) {
              const thumbRect = visibleRect(thumbLabel);
              if (thumbRect && intersects(labelRect, thumbRect)) {
                failures.push(`${key}: label intersects visible thumb label`);
              }
            }
          }
          return failures;
        }
        """,
        arg=expected,
    )
    assert failures == [], "parameter slider label geometry failures:\n" + "\n".join(failures)


def _assert_parameter_slider_accessibility(page) -> None:
    expected = {
        "length_m": "Length (m)",
        "beam_oa_m": "Beam OA (m)",
        "beam_wl_m": "Beam WL (m)",
        "draft_m": "Draft (m)",
        "deck_height_m": "Deck Height (m)",
        "Cp": "Prismatic Cp",
        "Cm": "Midship Cm",
        "deck_flatness": "Deck Flatness",
        "center_box_ratio": "Parallel Mid-Body",
        "bow_rake": "Bow Rake (1=raked)",
        "stern_rake": "Stern Rake (1=raked)",
        "target_speed_kt": "Target Speed (kt)",
    }

    assert page.locator(".kg-param-slider[role='group'][aria-label]").count() == len(expected)
    for key, expected_label in expected.items():
        row = page.locator(f".kg-param-{key}")
        assert row.count() == 1
        assert row.get_attribute("role") == "group"
        assert row.get_attribute("aria-label") == expected_label
        assert row.locator("[role='group']").count() == 0
        assert row.locator("[role='slider']").count() == 1

        visible_label = row.locator(".v-slider__label").first.text_content()
        assert visible_label == expected_label
        assert page.get_by_role("group", name=visible_label, exact=True).count() == 1


def _hex_to_rgb_ints(value: str) -> tuple[int, int, int]:
    hex_value = value.removeprefix("#")
    return tuple(int(hex_value[index : index + 2], 16) for index in (0, 2, 4))


def _linear_channel(channel: float) -> float:
    if channel <= 0.04045:
        return channel / 12.92
    return ((channel + 0.055) / 1.055) ** 2.4


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    red, green, blue = (_linear_channel(channel / 255.0) for channel in rgb)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _contrast_ratio(foreground: tuple[int, int, int], background: tuple[int, int, int]) -> float:
    lighter = max(_relative_luminance(foreground), _relative_luminance(background))
    darker = min(_relative_luminance(foreground), _relative_luminance(background))
    return (lighter + 0.05) / (darker + 0.05)


def _assert_contrast_manifest() -> None:
    failures = []
    for palette_name, tokens in (("light", theme.COLORS_LIGHT), ("dark", theme.COLORS_DARK)):
        for pair in theme.CONTRAST_MANIFEST:
            foreground = _hex_to_rgb_ints(tokens[pair.foreground_token])
            background = _hex_to_rgb_ints(tokens[pair.background_token])
            ratio = _contrast_ratio(foreground, background)
            if ratio < pair.min_ratio:
                failures.append(
                    f"{palette_name}.{pair.name}: {ratio:.2f} < {pair.min_ratio:.2f}"
                )
    assert failures == [], "contrast manifest failures:\n" + "\n".join(failures)


def _assert_workspace_focus_order_and_ring(page) -> None:
    expected_prefix = [
        "combobox:custom",
        "button:reset",
        "button:share",
        "button:export",
    ]
    page.locator(".kg-class-preset-select input").focus()

    observed: list[str] = []
    ring_failures: list[str] = []
    for index in range(len(expected_prefix)):
        result = page.evaluate(
            """
            (focusRingToken) => {
              const el = document.activeElement;
              const descriptor = (node) => {
                if (!node) return "";
                const role = node.getAttribute("role") || node.tagName.toLowerCase();
                const text = (
                  node.innerText
                  || node.value
                  || node.getAttribute("aria-label")
                  || node.textContent
                  || ""
                ).trim().replace(/\\s+/g, " ").toLowerCase();
                return `${role}:${text}`;
              };
              const expected = getComputedStyle(document.documentElement)
                .getPropertyValue(focusRingToken).trim();
              const probe = document.createElement("span");
              probe.style.color = expected;
              document.body.appendChild(probe);
              const expectedColor = getComputedStyle(probe).color;
              probe.remove();
              let hasRing = false;
              for (
                let cursor = el;
                cursor && cursor !== document.body;
                cursor = cursor.parentElement
              ) {
                const style = getComputedStyle(cursor);
                if (
                  style.outlineStyle !== "none"
                  && parseFloat(style.outlineWidth) >= 1
                  && style.outlineColor === expectedColor
                ) {
                  hasRing = true;
                  break;
                }
              }
              return {descriptor: descriptor(el), hasRing};
            }
            """,
            arg="--state-focus-ring",
        )
        observed.append(result["descriptor"])
        if not result["hasRing"]:
            ring_failures.append(result["descriptor"])
        if index < len(expected_prefix) - 1:
            page.keyboard.press("Tab")

    failures = []
    for index, expected in enumerate(expected_prefix):
        if not observed[index].startswith(expected):
            failures.append(f"focus {index}: {observed[index] or '<none>'} != {expected}")
    for failure in ring_failures:
        failures.append(f"missing token focus ring: {failure}")

    assert failures == [], (
        "workspace focus-order/focus-ring failures:\n"
        + "\n".join(failures)
        + "\nobserved order:\n"
        + "\n".join(observed)
    )


def _assert_workspace_hit_targets(page) -> None:
    failures = page.evaluate(
        """
        (minimum) => {
          const visibleRect = (el) => {
            const style = getComputedStyle(el);
            if (
              style.display === "none"
              || style.visibility === "hidden"
              || Number(style.opacity) === 0
            ) {
              return null;
            }
            const rect = el.getBoundingClientRect();
            if (rect.width <= 0 || rect.height <= 0) return null;
            return rect;
          };
          const label = (el) => (
            el.innerText
            || el.value
            || el.getAttribute("aria-label")
            || el.getAttribute("role")
            || el.tagName
          ).trim().replace(/\\s+/g, " ");
          const selectors = [
            ".kg-workspace-shell button:not(:disabled)",
            ".kg-workspace-shell [role='button']:not([aria-disabled='true'])",
            ".kg-workspace-shell [role='tab']",
            ".kg-workspace-shell [role='slider']",
            ".kg-workspace-shell input:not([type='hidden']):not([tabindex='-1'])",
            ".kg-workspace-shell select",
            ".kg-workspace-shell textarea",
          ].join(",");
          const controls = Array.from(document.querySelectorAll(selectors));
          const failures = [];
          for (const control of controls) {
            const target = control.closest(".v-slider")
              || control.closest(".v-field")
              || control.closest(".v-btn")
              || control.closest("button")
              || control;
            const rect = visibleRect(target);
            if (!rect) continue;
            if (rect.width < minimum || rect.height < minimum) {
              failures.push(
                `${label(control)}: ${rect.width.toFixed(1)}x${rect.height.toFixed(1)}`
              );
            }
          }
          return failures;
        }
        """,
        arg=A11Y_MIN_HIT_TARGET_PX,
    )
    assert failures == [], (
        f"interactive controls below {A11Y_MIN_HIT_TARGET_PX}px hit target:\n"
        + "\n".join(failures)
    )


@pytest.mark.browser_acceptance
@pytest.mark.parametrize("viewport", VISUAL_VIEWPORTS, ids=lambda viewport: viewport.name)
def test_web_workspace_visual_baseline(
    request: pytest.FixtureRequest,
    tmp_path: Path,
    viewport: VisualViewport,
) -> None:
    acceptance_required = _browser_acceptance_required(request)
    playwright_api = _load_playwright(request)
    update_baselines = bool(request.config.getoption("--update-visual-baselines"))
    baseline_path = VISUAL_BASELINE_DIR / f"{viewport.name}.png"
    url, proc = _start_server()
    try:
        with playwright_api.sync_playwright() as pw:
            browser = None
            try:
                browser = _launch_chromium(playwright_api, pw, request)
                page = browser.new_page(
                    viewport={"width": viewport.width, "height": viewport.height}
                )
                failures = _collect_browser_failures(page)
                page.goto(url, wait_until="networkidle", timeout=30_000)
                actual_png = _capture_masked_workspace_png(page, viewport)
                _assert_no_browser_failures(failures)
            finally:
                if browser is not None:
                    browser.close()
    finally:
        _stop_server(proc)

    if update_baselines:
        VISUAL_BASELINE_DIR.mkdir(parents=True, exist_ok=True)
        baseline_path.write_bytes(actual_png)
        return

    if not baseline_path.exists():
        message = (
            f"visual baseline is missing for {viewport.name}; regenerate with "
            "--update-visual-baselines"
        )
        if acceptance_required:
            pytest.fail(message)
        pytest.skip(message)

    result = _compare_visual_png(
        actual_png=actual_png,
        baseline_path=baseline_path,
        output_dir=tmp_path / "visual_baseline_diffs",
        viewport_name=viewport.name,
    )
    if not result.passed:
        message = (
            "visual baseline mismatch for "
            f"{viewport.name}: mismatch_ratio={result.mismatch_ratio:.4f}, "
            f"max_channel_delta={result.max_channel_delta}; "
            f"actual={result.actual_path}; diff={result.diff_path}"
        )
        if acceptance_required:
            pytest.fail(message)
        pytest.skip("advisory " + message)


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
                page.get_by_text("Resistance - raw comparative filter").first.wait_for(
                    timeout=10_000
                )
                page.get_by_text("Rv N").first.wait_for(timeout=10_000)
                page.get_by_text("uncalibrated_comparative").first.wait_for(timeout=10_000)
                page.get_by_text("Comparison").first.wait_for(timeout=10_000)
                _assert_parameter_slider_label_geometry(page)
                _assert_parameter_slider_accessibility(page)
                _assert_contrast_manifest()
                _assert_workspace_focus_order_and_ring(page)
                _assert_workspace_hit_targets(page)
                _assert_nonblank_3d(page)

                _select_class_preset(page, "Elite surfski")
                page.wait_for_function(
                    """
                    () => Math.abs(parseFloat(
                      document.querySelector(".kg-param-length_m [role='slider']")
                        ?.getAttribute("aria-valuenow") || "0"
                    ) - 6.1) < 0.001
                    """,
                    timeout=10_000,
                )
                assert abs(_slider_number(page, "length_m", "aria-valuemin") - 5.8) < 1e-6
                assert abs(_slider_number(page, "length_m", "aria-valuemax") - 6.4) < 1e-6
                assert abs(_slider_number(page, "beam_wl_m", "aria-valuemin") - 0.38) < 1e-6
                assert abs(_slider_number(page, "beam_wl_m", "aria-valuemax") - 0.43) < 1e-6
                page.get_by_text("In Elite surfski envelope").first.wait_for(timeout=10_000)
                # Selecting the preset fires same-seed hull updates through Trame; this
                # assertion pins the retained listener guard without private-helper calls.
                assert _class_preset_value(page) == "surfski_elite"

                # Reselecting the same preset must also keep preset bounds until an
                # actual hull edit flips the selector to custom.
                _select_class_preset(page, "Elite surfski")
                page.wait_for_function(
                    """
                    () => window.trame?.state?.get?.("class_preset") === "surfski_elite"
                    """,
                    timeout=10_000,
                )
                assert abs(_slider_number(page, "length_m", "aria-valuemin") - 5.8) < 1e-6
                assert abs(_slider_number(page, "length_m", "aria-valuemax") - 6.4) < 1e-6
                assert _class_preset_value(page) == "surfski_elite"

                page.locator(".kg-param-length_m [role='slider']").first.focus()
                page.keyboard.press("ArrowRight")
                page.wait_for_function(
                    """
                    () => window.trame?.state?.get?.("class_preset") === "custom"
                    """,
                    timeout=10_000,
                )
                page.get_by_text("In Elite surfski envelope").first.wait_for(timeout=10_000)

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

                page.get_by_role("tab", name="Mesh").click()
                page.get_by_text("Hull diagnostics").first.wait_for(timeout=10_000)
                page.get_by_text("Deck diagnostics").first.wait_for(timeout=10_000)
                page.get_by_text("Boundary edges (perimeter; acceptable)").first.wait_for(
                    timeout=10_000
                )
                page.get_by_text("(welded),").first.wait_for(timeout=10_000)
                page.get_by_text("Non-manifold edges (must be 0)").first.wait_for(
                    timeout=10_000
                )
                page.get_by_text("Degenerate faces (must be 0)").first.wait_for(
                    timeout=10_000
                )
                page.get_by_text("watertight-solid").first.wait_for(timeout=10_000)
                page.get_by_text("not watertight cfd_ready").first.wait_for(timeout=10_000)

                page.locator(".kg-export-menu-under-1200").click()
                page.get_by_text("Hull STL").first.wait_for(timeout=10_000)
                page.get_by_text("Deck STL").first.wait_for(timeout=10_000)
                page.get_by_text("Hydro JSON").first.wait_for(timeout=10_000)
                page.get_by_text("Stability JSON").first.wait_for(timeout=10_000)
                page.get_by_text("Mesh package (CLI only)").first.wait_for(timeout=10_000)
                page.get_by_text("use kayakgen mesh-package").first.wait_for(timeout=10_000)

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
                    async ({state, part}) => {
                      const response = await fetch(`/api/stl?part=${part}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(state),
                      });
                      const buffer = await response.arrayBuffer();
                      const view = new DataView(buffer);
                      return {
                        status: response.status,
                        content_type: response.headers.get('content-type'),
                        content_disposition: response.headers.get('content-disposition'),
                        length: buffer.byteLength,
                        triangle_count: buffer.byteLength >= 84 ? view.getUint32(80, true) : 0,
                      };
                    }
                    """,
                    arg={"state": default_state, "part": "hull"},
                )
                _assert_stl_response(stl, expected_filename="kayak_hull.stl")
                deck_stl = reload_page.evaluate(
                    """
                    async ({state, part}) => {
                      const response = await fetch(`/api/stl?part=${part}`, {
                        method: 'POST',
                        headers: {'Content-Type': 'application/json'},
                        body: JSON.stringify(state),
                      });
                      const buffer = await response.arrayBuffer();
                      const view = new DataView(buffer);
                      return {
                        status: response.status,
                        content_type: response.headers.get('content-type'),
                        content_disposition: response.headers.get('content-disposition'),
                        length: buffer.byteLength,
                        triangle_count: buffer.byteLength >= 84 ? view.getUint32(80, true) : 0,
                      };
                    }
                    """,
                    arg={"state": default_state, "part": "deck"},
                )
                _assert_stl_response(deck_stl, expected_filename="kayak_deck.stl")
                _assert_no_browser_failures(failures)
                reload_page.close()
            finally:
                browser.close()
    finally:
        _stop_server(proc)
