"""
Scenario Engine - generise veliki broj test scenarija iz opsega parametara
(poglavlje "Scenario Engine" u projektnom planu). Sadrzi generatore za sva
tri use case-a: AEB (kocenje), LKA (drzanje trake) i ACC (odrzavanje
razmaka).
"""

import random
from typing import List, Optional

from config import ACC_SCENARIO_RANGES as ACC_RANGES
from config import AEB_SCENARIO_RANGES as DEFAULT_RANGES
from config import AEB_WEATHER_FRICTION_ADJUSTMENT as WEATHER_FRICTION_ADJUSTMENT
from config import LKA_SCENARIO_RANGES as LKA_RANGES
from scenarios.schemas import ACCScenario, LKAScenario, Scenario

# Napomena: opsezi (DEFAULT_RANGES/LKA_RANGES/ACC_RANGES) i podesavanje
# trenja za kisu (WEATHER_FRICTION_ADJUSTMENT) sada zive u config.py; ovde
# su samo aliasi da postojeci kod/testovi ne moraju da se menjaju.


def generate_random_scenarios(count: int, seed: Optional[int] = None) -> List[Scenario]:
    """Generise `count` slucajnih scenarija unutar definisanih opsega."""
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
    Rucno definisani granicni scenariji, sa unapred izracunatim ocekivanim
    ponasanjem (videti tests/test_aeb.py). Korisni kao regresioni testovi
    koji ne zavise od nasumicnog generatora.
    """
    # (speed_kmh, obstacle_distance_m, weather, road_friction, sensor_delay_ms)
    presets = [
        (80, 20, "rain", 0.6, 100),    # primer iz projektnog dokumenta -> BRAKE ON
        (130, 100, "dry", 1.0, 0),     # velika brzina, dovoljno prostora -> BRAKE OFF
        (30, 2, "dry", 1.0, 0),        # mala brzina, ali vrlo blizu prepreke -> BRAKE ON
        (130, 30, "rain", 0.4, 500),   # worst-case: brzo, kisa, spor senzor -> BRAKE ON
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
    """Generise `count` slucajnih LKA scenarija."""
    rng = random.Random(seed)
    scenarios = []
    for i in range(count):
        lane_half_width = round(rng.uniform(*LKA_RANGES["lane_half_width_m"]), 2)
        # Ofset drzimo uglavnom unutar trake, ponekad malo preko ivice -
        # realno ponasanje: vozilo retko naglo "teleportuje" van trake.
        lateral_offset = round(rng.uniform(0, lane_half_width * 1.05), 3)
        # 15% scenarija ima vozaca koji aktivno upravlja (sistem se ne mesa).
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
    Rucno definisani granicni LKA scenariji, sa unapred izracunatim
    ocekivanim ponasanjem (videti tests/test_lka.py).
    """
    # (speed_kmh, lateral_offset_m, lane_half_width_m, lateral_velocity_m_s, driver_steering_active)
    presets = [
        (100, 1.0, 1.75, 1.0, False),   # blizu ivice i priblizava se -> INTERVENE ON
        (100, 0.0, 1.75, 0.0, False),   # centrirano, ne pomera se -> INTERVENE OFF
        (100, 1.0, 1.75, 2.0, True),    # brzo se priblizava, ALI vozac aktivno upravlja -> OFF
        (100, 1.8, 1.75, 1.0, False),   # vec preko ivice -> INTERVENE ON (odmah)
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
    """Generise `count` slucajnih ACC scenarija."""
    rng = random.Random(seed)
    scenarios = []
    for i in range(count):
        ego_speed = round(rng.uniform(*ACC_RANGES["ego_speed_kmh"]), 1)
        lead_speed = round(rng.uniform(*ACC_RANGES["lead_speed_kmh"]), 1)
        gap_distance = round(rng.uniform(*ACC_RANGES["gap_distance_m"]), 1)
        # 10% scenarija ima vozaca koji pritiska gas (override ACC usporavanja).
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
    Rucno definisani granicni ACC scenariji, sa unapred izracunatim
    ocekivanim ponasanjem (videti tests/test_acc.py).
    """
    # (ego_speed_kmh, lead_speed_kmh, gap_distance_m, driver_override_active)
    presets = [
        (100, 80, 30, False),   # razmak manji od zeljenog -> DECELERATE ON
        (100, 80, 60, False),   # razmak veci od zeljenog -> DECELERATE OFF
        (100, 80, 15, True),    # trebalo bi da uspori, ali vozac na gasu -> OFF
        (0, 0, 3, False),       # stajanje, razmak manji od minimuma -> DECELERATE ON
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
