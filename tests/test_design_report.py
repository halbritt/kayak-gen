"""Tests for the RFC 0055 design-report renderer."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

pytest.importorskip("jinja2", reason="design-report renderer requires jinja2")

from typer.testing import CliRunner  # noqa: E402

from kayakgen.cli.main import app  # noqa: E402
from kayakgen.io.json import save_hull  # noqa: E402
from kayakgen.model.hull import Hull  # noqa: E402
from kayakgen.services.design_report import (  # noqa: E402
    FORBIDDEN_COPY_PATTERN,
    FORBIDDEN_COPY_SCRUB_TOKENS,
    FORBIDDEN_COPY_TOKENS,
    DesignReportResult,
    ReportForbiddenCopyError,
    render_design_report,
)


def _scrub(text: str) -> str:
    scrubbed = text
    for token in FORBIDDEN_COPY_SCRUB_TOKENS:
        scrubbed = re.sub(re.escape(token), "", scrubbed, flags=re.IGNORECASE)
    return scrubbed


def test_renderer_round_trip_produces_self_contained_html_under_5_mb(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    result = render_design_report(Hull(), html_out=out)
    assert isinstance(result, DesignReportResult)
    assert result.forbidden_copy_clean is True
    assert out.is_file()
    payload = out.read_text()
    # Self-contained: inline CSS in a single ``<style>`` block and the 3D
    # preview embedded as a ``data:image/png;base64`` URL.
    assert "<style>" in payload
    assert "data:image/png;base64," in payload
    # No external network or filesystem-link references for the preview.
    assert "<link rel=\"stylesheet\"" not in payload
    assert "<script src=" not in payload
    size = out.stat().st_size
    assert size < 5 * 1024 * 1024, f"report HTML grew to {size} bytes, over 5 MB budget"
    # Every RFC 0055 section is named in the result.
    expected_sections = {
        "header",
        "parameters",
        "rendered_views",
        "hydrostatics",
        "stability",
        "resistance",
        "mesh",
        "comparison",
        "artifacts",
        "claim_explanations",
    }
    assert expected_sections.issubset(set(result.sections))


def test_renderer_forbidden_copy_scan_clean_after_scrubbing(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    render_design_report(Hull(), html_out=out)
    payload = out.read_text().lower()
    scrubbed = _scrub(payload)
    for token in FORBIDDEN_COPY_TOKENS:
        assert token not in scrubbed, (
            f"design report leaked forbidden token {token!r} after scrubbing"
        )


def test_forbidden_copy_pattern_refuses_synthetic_counter_example() -> None:
    """A renderer output containing any forbidden token must trip the refusal.

    This pins the regex itself with a synthetic counter-example so a future
    edit cannot silently relax the refusal.
    """

    for token in FORBIDDEN_COPY_TOKENS:
        sample = f"<p>Status: this hull is {token} for the open ocean.</p>"
        # The scrubber removes only the explicit negations, never these
        # bare tokens.
        assert FORBIDDEN_COPY_PATTERN.search(_scrub(sample)) is not None, (
            f"forbidden-copy regex failed to catch bare token {token!r}"
        )


def test_from_run_adds_comparison_section_when_hull_in_run(tmp_path: Path) -> None:
    hull = Hull(name="default")
    run_dir = _write_minimal_run(tmp_path / "run", hull=hull)
    out = tmp_path / "report.html"
    result = render_design_report(hull, from_run=run_dir, html_out=out)
    payload = out.read_text()
    assert result.forbidden_copy_clean is True
    assert "Comparison position" in payload
    # Hull-in-run path: candidate key from the matching run record renders.
    record = json.loads((run_dir / "run.json").read_text())
    matched_key = record["candidates"][0]["candidate_key"]
    assert matched_key in payload
    assert "this hull was not in the referenced run" not in payload.lower()


def test_from_run_honestly_notes_when_hull_not_in_run(tmp_path: Path) -> None:
    in_run_hull = Hull(name="in-run")
    run_dir = _write_minimal_run(tmp_path / "run", hull=in_run_hull)
    # Different hull (different displacement) — must NOT match.
    other_hull = Hull(name="other", length_m=4.8, beam_oa_m=0.60, draft_m=0.13)
    out = tmp_path / "report.html"
    render_design_report(other_hull, from_run=run_dir, html_out=out)
    payload = out.read_text().lower()
    assert "this hull was not in the referenced run" in payload


def test_pdf_export_succeeds_or_reports_extras(tmp_path: Path) -> None:
    out = tmp_path / "report.html"
    pdf_out = tmp_path / "report.pdf"
    try:
        import weasyprint  # noqa: F401
    except ImportError:
        with pytest.raises(RuntimeError) as excinfo:
            render_design_report(Hull(), html_out=out, pdf_out=pdf_out)
        message = str(excinfo.value)
        assert "weasyprint" in message
        assert "kayakgen[report]" in message
        # The HTML still landed before the PDF step failed.
        assert out.is_file()
        return
    result = render_design_report(Hull(), html_out=out, pdf_out=pdf_out)
    assert result.pdf_path == pdf_out
    assert pdf_out.is_file()
    assert pdf_out.stat().st_size > 0


def test_design_report_cli_writes_html(tmp_path: Path) -> None:
    hull_path = tmp_path / "default.json"
    save_hull(Hull(), hull_path)
    out = tmp_path / "report.html"
    runner = CliRunner()
    result = runner.invoke(app, ["design-report", str(hull_path), "--out", str(out)])
    assert result.exit_code == 0, result.output
    assert out.is_file()
    payload = out.read_text().lower()
    for token in FORBIDDEN_COPY_TOKENS:
        assert token not in _scrub(payload)


def test_design_report_refusal_raises_forbidden_copy_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """If a section assembler leaks a forbidden token, render must refuse."""

    from kayakgen.services import design_report as svc

    original = svc._section_header

    def leaky_header(hull, hull_source_path, timestamp):
        block = original(hull, hull_source_path, timestamp)
        block["hull_name"] = "this hull is safe and seaworthy"
        return block

    monkeypatch.setattr(svc, "_section_header", leaky_header)
    out = tmp_path / "report.html"
    with pytest.raises(ReportForbiddenCopyError):
        svc.render_design_report(Hull(), html_out=out)
    assert not out.exists(), "renderer must not write on forbidden-copy refusal"


# ---------------------------------------------------------------------------
# Helpers


def _write_minimal_run(run_dir: Path, *, hull: Hull) -> Path:
    """Write a sweep-run directory with one candidate matching ``hull``.

    The shape mirrors the RFC 0009 sweep output enough for
    ``build_comparison_report`` to load it without running a real sweep.
    """

    run_dir.mkdir(parents=True, exist_ok=True)
    candidates_dir = run_dir / "candidates"
    candidates_dir.mkdir(exist_ok=True)
    candidate_key = hull.hash()[:32]
    record = {
        "schema_version": "1",
        "candidate_index": 0,
        "candidate_key": candidate_key,
        "parameters": {"length_m": hull.length_m},
        "attempted_hull": hull.model_dump(mode="json"),
        "status": "complete",
        "hull_hash": hull.hash(),
        "artifacts": {},
        "summary": {},
        "warnings": [],
    }
    run = {
        "schema_version": "1",
        "name": "test-run",
        "spec_hash": "0" * 64,
        "candidate_count": 1,
        "pending_count": 0,
        "completed_count": 1,
        "failed_count": 0,
        "skipped_count": 0,
        "candidates": [record],
    }
    (run_dir / "run.json").write_text(json.dumps(run))
    return run_dir
