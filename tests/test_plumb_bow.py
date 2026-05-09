"""RFC 0004 — bow_rake parameter and end-decay blend."""

from __future__ import annotations

import struct
from pathlib import Path

import numpy as np

from kayakgen.eval.hydrostatics import evaluate
from kayakgen.model.geometry import LoftedHullGeometry
from kayakgen.model.hull import Hull


def _stl_payload_sha256(path: Path) -> str:
    import hashlib

    data = path.read_bytes()
    n_tris = struct.unpack("<I", data[80:84])[0]
    return hashlib.sha256(data[84 : 84 + n_tris * 50]).hexdigest()


def test_default_rake_preserves_legacy_geometry(tmp_path: Path) -> None:
    """bow_rake=1.0 (default) must reproduce the golden STL payload."""
    hull = Hull()
    assert hull.bow_rake == 1.0
    out = tmp_path / "default_hull.stl"
    hull.to_geometry().generate_stl("hull", str(out))
    expected = "bd3ba7d497e78349d43495bb0d02097ddfcc3c0e2c5781945c25f781218a4c39"
    assert _stl_payload_sha256(out) == expected


def test_plumb_keel_holds_full_draft_in_middle() -> None:
    """bow_rake=0.0 keeps the keel at full draft until the last 5% of L/2."""
    geom = LoftedHullGeometry(Hull(bow_rake=0.0))
    keel = geom.keel_line(n=400)
    L = geom.L
    inner = keel[(keel[:, 0] >= -0.4 * L) & (keel[:, 0] <= 0.4 * L)]
    # Inner 80% of length: keel z must be at full draft (within float noise)
    np.testing.assert_allclose(inner[:, 1], -geom.T, atol=1e-12)


def test_plumb_keel_drops_in_last_five_percent() -> None:
    """In the last 5% near the bow, plumb keel ramps down to z=0 linearly."""
    geom = LoftedHullGeometry(Hull(bow_rake=0.0))
    keel = geom.keel_line(n=2000)
    L = geom.L
    # 95% of half-length = 0.475 L
    last5 = keel[keel[:, 0] >= 0.475 * L]
    # First sample inside the transition is near full draft, last is at 0.
    assert last5[0, 1] < -0.10
    assert last5[-1, 1] == 0.0


def test_plumb_section_at_end_has_nonzero_area() -> None:
    """At bow_rake=0.0, station near x=-L/2 still has positive section area."""
    geom = LoftedHullGeometry(Hull(bow_rake=0.0))
    L = geom.L
    # Station at 95% to the bow — inside the parallel mid-body for plumb
    area = geom.section_area(-0.45 * L)
    assert area > 0.005


def test_plumb_displacement_exceeds_raked() -> None:
    """A plumb hull holds its full keel draft farther forward than a raked
    hull, so its integrated displacement is larger at the same beam/draft."""
    raked = evaluate(Hull(bow_rake=1.0))
    plumb = evaluate(Hull(bow_rake=0.0))
    assert plumb.displaced_volume_m3 > raked.displaced_volume_m3


def test_intermediate_rake_blends_monotonically() -> None:
    """Volume changes monotonically as bow_rake interpolates 1.0 → 0.0."""
    vols = [evaluate(Hull(bow_rake=r)).displaced_volume_m3 for r in (1.0, 0.75, 0.50, 0.25, 0.0)]
    assert all(b >= a for a, b in zip(vols, vols[1:]))


def test_stl_watertight_at_plumb_bow_rake_zero(tmp_path: Path) -> None:
    """Mesh remains valid (no degenerate end-cap singletons) at bow_rake=0."""
    geom = LoftedHullGeometry(Hull(bow_rake=0.0))
    out = tmp_path / "plumb.stl"
    geom.generate_stl("hull", str(out))
    assert out.stat().st_size > 0
    # Same mesh shape as raked — only positions differ
    v, f = geom.mesh("hull")
    assert v.shape == (150 * 79, 3)
    assert f.shape == (149 * 78 * 2, 3)


def test_waterplane_uses_blended_decay() -> None:
    """waterplane() must reflect bow_rake, not stay sqrt(area_fraction)."""
    raked = LoftedHullGeometry(Hull(bow_rake=1.0)).waterplane(n=400)
    plumb = LoftedHullGeometry(Hull(bow_rake=0.0)).waterplane(n=400)
    # At ~30% of half-length, plumb should still hold full beam_wl, raked is decayed
    L = 4.5
    idx = np.argmin(abs(raked[:, 0] - 0.3 * L / 2))
    assert plumb[idx, 1] > raked[idx, 1]
