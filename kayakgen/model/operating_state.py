"""Rigid operating pose of a fixed physical hull in calm water."""

from __future__ import annotations

from dataclasses import dataclass
import math


@dataclass(frozen=True)
class OperatingPose:
    """Positive sinkage lowers the hull; positive trim is stern-down."""

    sinkage_m: float = 0.0
    trim_angle_deg: float = 0.0

    def __post_init__(self) -> None:
        if not math.isfinite(self.sinkage_m) or not math.isfinite(self.trim_angle_deg):
            raise ValueError("operating pose values must be finite")
        if abs(self.trim_angle_deg) >= 90.0:
            raise ValueError("operating trim must lie strictly between -90 and 90 degrees")
