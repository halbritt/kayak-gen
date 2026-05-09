"""Legacy entry point — desktop GUI now lives in ``kayakgen.ui.desktop``."""

from __future__ import annotations

from kayakgen.ui.desktop import KayakGUI

__all__ = ["KayakGUI"]


if __name__ == "__main__":
    KayakGUI()
