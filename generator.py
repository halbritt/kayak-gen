"""Legacy entry point — re-exports the lofted geometry under its old name.

Use :class:`kayakgen.model.geometry.LoftedHullGeometry` directly in new
code. ``KayakGenerator`` here keeps the original positional/keyword
constructor working so existing scripts, tests, and the desktop GUI
shim continue to import ``from generator import KayakGenerator``.
"""

from __future__ import annotations

from kayakgen.model.geometry import LoftedHullGeometry
from kayakgen.model.hull import Hull


class KayakGenerator(LoftedHullGeometry):
    def __init__(
        self,
        length: float = 4.5,
        beam: float = 0.55,
        draft: float = 0.12,
        deck_height: float = 0.23,
        Cp: float = 0.54,
        deck_flatness: float = 8.0,
        center_box_ratio: float = 0.33,
        beam_wl: float | None = None,
        bow_rake: float = 1.0,
    ) -> None:
        hull = Hull(
            length_m=length,
            beam_oa_m=beam,
            beam_wl_m=beam_wl,
            draft_m=draft,
            deck_height_m=deck_height,
            Cp=Cp,
            deck_flatness=deck_flatness,
            center_box_ratio=center_box_ratio,
            bow_rake=bow_rake,
        )
        super().__init__(hull)


if __name__ == "__main__":
    kayak = KayakGenerator(
        length=4.5,
        beam=0.55,
        draft=0.12,
        deck_height=0.23,
        Cp=0.55,
        deck_flatness=8.0,
        center_box_ratio=0.33,
    )

    print("Generating Hull...")
    kayak.generate_stl("hull", "kayak_hull.stl")

    print("Generating Deck...")
    kayak.generate_stl("deck", "kayak_deck.stl")
