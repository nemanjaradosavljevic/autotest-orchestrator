"""
Scenario Engine - generates a large number of test scenarios from parameter
ranges (the "Scenario Engine" chapter in the project plan). Contains
generators for all three use cases: AEB (braking), LKA (lane keeping) and
ACC (gap maintenance).
"""

import random
from typing import List, Optional

from config import ACC_SCENARIO_RANGES as ACC_RANGES
from config import AEB_SCENARIO_RANGES as DEFAULT_RANGES
from config import AEB_WEATHER_FRICTION_ADJUSTMENT as WEATHER_FRICTION_ADJUSTMENT
from config import LKA_SCENARIO_RANGES as LKA_RANGES
from scenarios.schemas import ACCScenario, LKAScenario, Scenario

# Note: the ranges (DEFAULT_RANGES/LKA_RANGES/ACC_RANGES) and the friction
# adjustment for rain (WEATHER_FRICTION_ADJUSTMENT) now live in config.py;
# these are just aliases so existing code/tests don't have to change.


def generate_random_scenarios(count: int, seed: Optional[int] = None) -> List[Scenario]:
    """Generates `count` random scenarios within the defined ranges."""
    rng = random.Random(seed)
    scenarios = []
    for i in range(count):
        weather = rng.choice(["dry", "rain"])
        base_friction = rng.uniform(*DEFAULT_RANGES["road_friction"])
        friction = round(base_friction * WEATHER_FRICTION_ADJUSTMENT[weather], 3)
        friction = max(friction, 0.1)

        scenarios.append(
            Scenario(
                id=i,
                vehicle_speed_kmh=round(rng.uniform(*DEFAULT_RANGES["speed_kmh"]), 1),
                obstacle_distance_m=round(rng.uniform(*DEFAULT_RANGES["obstacle_distance_m"]), 1),
                weather=weather,
                road_friction=friction,
                sensor_delay_ms=round(rng.uniform(*DEFAULT_RANGES["sensor_delay_ms"]), 0),
            )
        )
    return scenarios


def generate_edge_case_scenarios() -> List[Scenario]:
    """
    Manually defined edge-case scenarios, with precomputed expected
    behavior (see tests/test_aeb.py). Useful as regression tests that
    don't depend on the random generator.
    """
    # (speed_kmh, obstacle_distance_m, weather, road_friction, sensor_delay_ms)
    presets = [
        (80, 20, "rain", 0.6, 100),    # example from the project document -> BRAKE ON
        (130, 100, "dry", 1.0, 0),     # high speed, enough room -> BRAKE OFF
        (30, 2, "dry", 1.0, 0),        # low speed, but very close to obstacle -> BRAKE ON
        (130, 30, "rain", 0.4, 500),   # worst-case: fast, rain, slow sensor -> BRAKE ON
    ]
    return [
        Scenario(
            id=1000 + idx,
            vehicle_speed_kmh=p[0],
            obstacle_distance_m=p[1],
            weather=p[2],
            road_friction=p[3],
            sensor_delay_ms=p[4],
        )
        for idx, p in enumerate(presets)
    ]


def generate_random_lka_scenarios(count: int, seed: Optional[int] = None) -> List[LKAScenario]:
    """Generates `count` random LKA scenarios."""
    rng = random.Random(seed)
    scenarios = []
    for i in range(count):
        lane_half_width = round(rng.uniform(*LKA_RANGES["lane_half_width_m"]), 2)
        # We keep the offset mostly within the lane, occasionally slightly past the
        # edge - realistic behavior: a vehicle rarely "teleports" abruptly out of the lane.
        lateral_offset = round(rng.uniform(0, lane_half_width * 1.05), 3)
        # 15% of scenarios have a driver who is actively steering (the system doesn't intervene).
        driver_active = rng.random() < 0.15

        scenarios.append(
            LKAScenario(
                id=i,
                vehicle_speed_kmh=round(rng.uniform(*LKA_RANGES["speed_kmh"]), 1),
                lateral_offset_m=lateral_offset,
                lane_half_width_m=lane_half_width,
                lateral_velocity_m_s=round(rng.uniform(*LKA_RANGES["lateral_velocity_m_s"]), 3),
                driver_steering_active=driver_active,
            )
        )
    return scenarios


def generate_edge_case_lka_scenarios() -> List[LKAScenario]:
    """
    Manually defined edge-case LKA scenarios, with precomputed expected
    behavior (see tests/test_lka.py).
    """
    # (speed_kmh, lateral_offset_m, lane_half_width_m, lateral_velocity_m_s, driver_steering_active)
    presets = [
        (100, 1.0, 1.75, 1.0, False),   # close to the edge and approaching it -> INTERVENE ON
        (100, 0.0, 1.75, 0.0, False),   # centered, not moving -> INTERVENE OFF
        (100, 1.0, 1.75, 2.0, True),    # approaching fast, BUT the driver is actively steering -> OFF
        (100, 1.8, 1.75, 1.0, False),   # already past the edge -> INTERVENE ON (immediately)
    ]
    return [
        LKAScenario(
            id=2000 + idx,
            vehicle_speed_kmh=p[0],
            lateral_offset_m=p[1],
            lane_half_width_m=p[2],
            lateral_velocity_m_s=p[3],
            driver_steering_active=p[4],
        )
        for idx, p in enumerate(presets)
    ]


def generate_random_acc_scenarios(count: int, seed: Optional[int] = None) -> List[ACCScenario]:
    """Generates `count` random ACC scenarios."""
    rng = random.Random(seed)
    scenarios = []
    for i in range(count):
        ego_speed = round(rng.uniform(*ACC_RANGES["ego_speed_kmh"]), 1)
        lead_speed = round(rng.uniform(*ACC_RANGES["lead_speed_kmh"]), 1)
        gap_distance = round(rng.uniform(*ACC_RANGES["gap_distance_m"]), 1)
        # 10% of scenarios have a driver pressing the accelerator (overriding ACC deceleration).
        driver_override = rng.random() < 0.10

        scenarios.append(
            ACCScenario(
                id=i,
                ego_speed_kmh=ego_speed,
                lead_speed_kmh=lead_speed,
                gap_distance_m=gap_distance,
                driver_override_active=driver_override,
            )
        )
    return scenarios


def generate_edge_case_acc_scenarios() -> List[ACCScenario]:
    """
    Manually defined edge-case ACC scenarios, with precomputed expected
    behavior (see tests/test_acc.py).
    """
    # (ego_speed_kmh, lead_speed_kmh, gap_distance_m, driver_override_active)
    presets = [
        (100, 80, 30, False),   # gap smaller than desired -> DECELERATE ON
        (100, 80, 60, False),   # gap larger than desired -> DECELERATE OFF
        (100, 80, 15, True),    # should decelerate, but driver is on the accelerator -> OFF
        (0, 0, 3, False),       # standing still, gap smaller than the minimum -> DECELERATE ON
    ]
    return [
        ACCScenario(
            id=3000 + idx,
            ego_speed_kmh=p[0],
            lead_speed_kmh=p[1],
            gap_distance_m=p[2],
            driver_override_active=p[3],
        )
        for idx, p in enumerate(presets)
    ]
