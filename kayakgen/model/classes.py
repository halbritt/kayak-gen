"""Named regions of the kayak design space — RFC 0006.

Each :class:`KayakClass` is a value object describing a named slice of
the parameter envelope from
``docs/design/kayak_hull_design_constraints.md`` §3, §4, §8, §9. Selecting
a class seeds default values; ranges advise the GUI but do not hard-block.
"""

from __future__ import annotations

from dataclasses import dataclass

from kayakgen.model.hull import Hull


@dataclass(frozen=True)
class Range:
    min: float
    max: float
    default: float


@dataclass(frozen=True)
class KayakClass:
    name: str
    label: str
    length_m: Range
    beam_oa_m: Range
    beam_wl_m: Range
    draft_m: Range
    Cp: Range
    notes: str

    def default_hull(self) -> Hull:
        """Return a :class:`Hull` seeded from this class's default values."""
        return Hull(
            name=self.name,
            length_m=self.length_m.default,
            beam_oa_m=self.beam_oa_m.default,
            beam_wl_m=self.beam_wl_m.default,
            draft_m=self.draft_m.default,
            Cp=self.Cp.default,
        )


# Numbers come from docs/design/kayak_hull_design_constraints.md §3, §4, §8, §9.
# RFC 0006 acceptance criteria pin the touring and elite surfski defaults
# explicitly; performance and intermediate surfski are placed mid-range inside
# their classes. Ranges intentionally prefer the named class rows in §4 where
# they are more specific than the broad generator envelope in §9. Stable
# surfskis are not merged into the intermediate-surfski preset; that wider edge
# remains a future class/preset decision.
CLASSES: dict[str, KayakClass] = {
    "touring": KayakClass(
        name="touring",
        label="Touring sea kayak",
        length_m=Range(4.3, 5.5, 5.0),
        beam_oa_m=Range(0.56, 0.61, 0.58),
        beam_wl_m=Range(0.50, 0.58, 0.53),
        draft_m=Range(0.10, 0.14, 0.12),
        Cp=Range(0.52, 0.56, 0.54),
        notes="General-purpose ocean touring. Stable, forgiving, decent glide.",
    ),
    "performance": KayakClass(
        name="performance",
        label="Performance sea kayak",
        length_m=Range(4.9, 5.5, 5.2),
        beam_oa_m=Range(0.51, 0.56, 0.53),
        beam_wl_m=Range(0.46, 0.52, 0.49),
        draft_m=Range(0.10, 0.14, 0.12),
        Cp=Range(0.54, 0.58, 0.56),
        notes="Faster than touring; secondary-stable but tippier on flat water.",
    ),
    "surfski_int": KayakClass(
        name="surfski_int",
        label="Intermediate surfski",
        length_m=Range(5.5, 5.8, 5.65),
        beam_oa_m=Range(0.48, 0.51, 0.50),
        beam_wl_m=Range(0.46, 0.49, 0.47),
        draft_m=Range(0.10, 0.13, 0.115),
        Cp=Range(0.55, 0.59, 0.57),
        notes="Surfski for downwind running and flat-water training; manageable stability.",
    ),
    "surfski_elite": KayakClass(
        name="surfski_elite",
        label="Elite surfski",
        length_m=Range(5.8, 6.4, 6.1),
        beam_oa_m=Range(0.42, 0.46, 0.43),
        beam_wl_m=Range(0.38, 0.43, 0.40),
        draft_m=Range(0.09, 0.12, 0.11),
        Cp=Range(0.56, 0.60, 0.58),
        notes="Elite-class surfski; narrow waterline, fine ends, demanding stability.",
    ),
}


def list_classes() -> list[KayakClass]:
    """Return the canonical class list in display order."""
    return list(CLASSES.values())


def get_class(name: str) -> KayakClass:
    if name not in CLASSES:
        raise KeyError(f"unknown KayakClass {name!r}; have {list(CLASSES)}")
    return CLASSES[name]
