"""
Schemas - definicija strukture test scenarija, po jedan dataclass po use
case-u (AEB, LKA, ...). Svaki novi use case samo dodaje svoju klasu ovde -
ostatak sistema (Test Engine, Analytics, Dashboard) ne mora da zna za
detalje drugih use case-ova.
"""

from dataclasses import dataclass, asdict
from typing import Literal

Weather = Literal["dry", "rain"]


@dataclass(frozen=True)
class Scenario:
    """AEB scenario. Ime je istorijsko (prvi use case u projektu) - zadrzano
    ovakvo da ne bismo lomili vec postojeci, testirani kod."""

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
