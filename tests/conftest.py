"""Shared pytest options for local and acceptance test profiles."""

from __future__ import annotations

import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def pytest_addoption(parser):
    parser.addoption(
        "--browser-acceptance",
        action="store_true",
        default=False,
        help="Fail instead of skipping when required Playwright/Chromium tooling is missing.",
    )
