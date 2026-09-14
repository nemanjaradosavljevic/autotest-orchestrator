"""
LKA Assertions - reference ("oracle") calculation of expected behavior for
Lane Keep Assist, following the same principle as test_engine/assertions.py
for AEB: "expected" is deliberately a stricter (more conservative) version
of the system, with a safety margin, while "actual" (virtual_ecu/lka.py)
intervenes exactly at the boundary.

SAFETY_MARGIN here means: the system should intervene with MORE time to
spare (a larger threshold for time-to-lane-crossing), not less - the same
"threshold shifted to the more conservative side" principle as with AEB,
just applied to a time threshold instead of a spatial one.
"""

from dataclasses import dataclass
from typing import Optional

from config import LKA_SAFETY_MARGIN as SAFETY_MARGIN
from virtual_ecu.lka import TTLC_THRESHOLD_S

MARGIN_THRESHOLD_S = TTLC_THRESHOLD_S * SAFETY_MARGIN


@dataclass(frozen=True)
class LKAExpectedResult:
    intervene: bool
    time_to_crossing_s: Optional[float]


def compute_lka_expected(
    vehicle_speed_kmh: float,
    lateral_offset_m: float,
    lane_half_width_m: float,
    lateral_velocity_m_s: float,
    driver_steering_active: bool,
) -> LKAExpectedResult:
    distance_to_edge_m = lane_half_width_m - abs(lateral_offset_m)

    if distance_to_edge_m <= 0:
        time_to_crossing_s: Optional[float] = 0.0
    elif lateral_velocity_m_s <= 0:
        time_to_crossing_s = None
    else:
        time_to_crossing_s = distance_to_edge_m / lateral_velocity_m_s

    if driver_steering_active or time_to_crossing_s is None:
        intervene = False
    else:
        intervene = time_to_crossing_s <= MARGIN_THRESHOLD_S

    return LKAExpectedResult(
        intervene=intervene,
        time_to_crossing_s=round(time_to_crossing_s, 3) if time_to_crossing_s is not None else None,
    )
