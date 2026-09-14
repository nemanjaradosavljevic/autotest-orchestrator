"""
Schemas - defines the structure of test scenarios, one dataclass per use
case (AEB, LKA, ...). Each new use case just adds its own class here -
the rest of the system (Test Engine, Analytics, Dashboard) doesn't need to
know about the details of other use cases.
"""

from dataclasses import dataclass, asdict
from typing import Literal

Weather = Literal["dry", "rain"]


@dataclass(frozen=True)
class Scenario:
    """AEB scenario. The name is historical (the first use case in the
    project) - kept this way so we don't break existing, tested code."""

    id: int
    vehicle_speed_kmh: float
    obstacle_distance_m: float
    weather: Weather
    road_friction: float
    sensor_delay_ms: float

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class LKAScenario:
    """Lane Keep Assist scenario."""

    id: int
    vehicle_speed_kmh: float
    lateral_offset_m: float
    lane_half_width_m: float
    lateral_velocity_m_s: float
    driver_steering_active: bool

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass(frozen=True)
class ACCScenario:
    """Adaptive Cruise Control scenario."""

    id: int
    ego_speed_kmh: float
    lead_speed_kmh: float
    gap_distance_m: float
    driver_override_active: bool

    def to_dict(self) -> dict:
        return asdict(self)
