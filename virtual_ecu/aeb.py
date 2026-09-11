"""
Virtual ECU - Automatic Emergency Braking (AEB) logika.

Ovo je "sistem pod testom" (system under test): jednostavan softverski
model ECU-a koji donosi odluku o kocenju na osnovu ulaznih parametara.
Cilj MVP-a nije realan fizicki model automobila, vec kontrolisan sistem
sa ulazima, logikom i izlazima koji mozemo automatski i masovno testirati.

Kasnije (V2/V3) ovaj modul se moze zameniti ili dopuniti pravim STM32
uredjajem povezanim preko CAN-a, dok Test Engine i Scenario Engine
ostaju isti.
"""

from dataclasses import dataclass

from config import GRAVITY_M_S2


@dataclass(frozen=True)
class ECUOutput:
    brake: bool
    stopping_distance_m: float
    reaction_distance_m: float
    braking_distance_m: float


class AEBVirtualECU:
    """Simulira ECU logiku za Automatic Emergency Braking."""

    def process(
        self,
        vehicle_speed_kmh: float,
        obstacle_distance_m: float,
        road_friction: float,
        sensor_delay_ms: float,
    ) -> ECUOutput:
        if vehicle_speed_kmh < 0:
            raise ValueError("vehicle_speed_kmh ne moze biti negativna")
        if obstacle_distance_m < 0:
            raise ValueError("obstacle_distance_m ne moze biti negativna")
        if not (0 < road_friction <= 1.5):
            raise ValueError("road_friction mora biti u opsegu (0, 1.5]")
        if sensor_delay_ms < 0:
            raise ValueError("sensor_delay_ms ne moze biti negativan")

        speed_m_s = vehicle_speed_kmh / 3.6

        # Reakciona udaljenost - koliko vozilo predje dok senzor/ECU "primeti" prepreku
        reaction_distance_m = speed_m_s * (sensor_delay_ms / 1000.0)

        # Kociona udaljenost iz fizike kretanja: v^2 / (2 * mu * g)
        braking_distance_m = (speed_m_s ** 2) / (2 * road_friction * GRAVITY_M_S2)

        stopping_distance_m = reaction_distance_m + braking_distance_m

        # Ako je potrebna udaljenost za zaustavljanje >= stvarne udaljenosti
        # do prepreke, sistem mora da koci.
        brake = obstacle_distance_m <= stopping_distance_m

        return ECUOutput(
            brake=brake,
            stopping_distance_m=round(stopping_distance_m, 2),
            reaction_distance_m=round(reaction_distance_m, 2),
            braking_distance_m=round(braking_distance_m, 2),
        )
