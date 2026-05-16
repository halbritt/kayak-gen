"""Application services for kayakgen.

This package owns orchestration helpers that bridge the evaluation /
model / search layers and the web/CLI surfaces. Modules here must not
import from :mod:`kayakgen.ui` or :mod:`kayakgen.cli` — see
``tests/test_services_boundaries.py``.
"""
