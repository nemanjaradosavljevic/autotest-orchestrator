"""
LKA Assertions - referentni ("oracle") proracun ocekivanog ponasanja za
Lane Keep Assist, po istom principu kao test_engine/assertions.py za AEB:
"expected" je namerno strozija (konzervativnija) verzija sistema, sa
bezbednosnom marginom, dok "actual" (virtual_ecu/lka.py) intervenise tacno
na granici.

SAFETY_MARGIN ovde znaci: sistem treba da intervenise sa VISE vremena na
raspolaganju (veci prag za vreme-do-prelaska-linije), ne manje - isti
"prag pomeren u konzervativniju stranu" princip kao kod AEB-a, samo
primenjen na vremenski umesto na prostorni prag.
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
