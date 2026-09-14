"""
Virtual ECU - Lane Keep Assist (LKA) logic.

A second use case alongside AEB (virtual_ecu/aeb.py), deliberately written
following the same pattern: clean input -> logic -> output, with no
dependency on the rest of the system. The goal is to show that the
architecture (Scenario Engine -> Virtual ECU -> Test Engine -> Analytics ->
Dashboard) generalizes to more than one automotive function, not just
braking.

Simplified model: the system tracks how far the vehicle is from the lane
edge and how fast it is approaching it (lateral velocity), then computes
the "time to line crossing" (TTLC) - how many seconds until the vehicle
would cross the lane edge if nothing changes. If TTLC is below the
threshold (and the driver is not actively steering), the system intervenes
(corrects the steering).
"""

from dataclasses import dataclass
from typing import Optional

from config import LKA_TTLC_THRESHOLD_S as TTLC_THRESHOLD_S


@dataclass(frozen=True)
class LKAOutput:
    intervene: bool
    time_to_crossing_s: Optional[float]  # None = the vehicle is not approaching the edge
    distance_to_edge_m: float


class LKAVirtualECU:
    """Simulates the ECU logic for Lane Keep Assist."""

    def process(
        self,
        vehicle_speed_kmh: float,
        lateral_offset_m: float,
        lane_half_width_m: float,
        lateral_velocity_m_s: float,
        driver_steering_active: bool,
    ) -> LKAOutput:
        if vehicle_speed_kmh < 0:
            raise ValueError("vehicle_speed_kmh cannot be negative")
        if lane_half_width_m <= 0:
            raise ValueError("lane_half_width_m must be positive")

        distance_to_edge_m = lane_half_width_m - abs(lateral_offset_m)

        if distance_to_edge_m <= 0:
            # The vehicle is already at or past the edge - no time to lose.
            time_to_crossing_s: Optional[float] = 0.0
        elif lateral_velocity_m_s <= 0:
            # Not approaching the edge (stationary or moving back toward the lane center).
            time_to_crossing_s = None
        else:
            time_to_crossing_s = distance_to_edge_m / lateral_velocity_m_s

        if driver_steering_active or time_to_crossing_s is None:
            intervene = False
        else:
            intervene = time_to_crossing_s <= TTLC_THRESHOLD_S

        return LKAOutput(
            intervene=intervene,
            time_to_crossing_s=round(time_to_crossing_s, 3) if time_to_crossing_s is not None else None,
            distance_to_edge_m=round(distance_to_edge_m, 3),
        )
