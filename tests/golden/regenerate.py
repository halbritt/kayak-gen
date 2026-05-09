"""
Regenerate tests/golden/default_*.stl from the current generator.

Run this only when an intentional change to KayakGenerator's geometry has
landed and the byte hashes in tests/test_golden.py need to track. After
running, copy the printed SHA256 values into HULL_STL_SHA256 and
DECK_STL_SHA256 and commit both the goldens and the constant updates in the
same commit.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from generator import KayakGenerator  # noqa: E402

GOLDEN_DIR = Path(__file__).parent

DEFAULT_PARAMS = dict(
    length=4.5,
    beam=0.55,
    draft=0.12,
    deck_height=0.23,
    Cp=0.55,
    deck_flatness=8.0,
    center_box_ratio=0.33,
)


def main() -> None:
    kg = KayakGenerator(**DEFAULT_PARAMS)
    for part in ("hull", "deck"):
        out = GOLDEN_DIR / f"default_{part}.stl"
        kg.generate_stl(part, str(out))
        sha = hashlib.sha256(out.read_bytes()).hexdigest()
        print(f"{out.name}: sha256 {sha}  size {out.stat().st_size}")


if __name__ == "__main__":
    main()
