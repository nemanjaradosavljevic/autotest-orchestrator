"""
Virtual ECU - Lane Keep Assist (LKA) logika.

Drugi use case pored AEB-a (virtual_ecu/aeb.py), namerno napisan po istom
obrascu: cist ulaz -> logika -> izlaz, bez zavisnosti od ostatka sistema.
Cilj je da pokaze da arhitektura (Scenario Engine -> Virtual ECU -> Test
Engine -> Analytics -> Dashboard) generalizuje na vise od jedne automotive
funkcije, ne samo na kocenje.

Pojednostavljen model: sistem prati koliko je vozilo daleko od ivice trake
i koliko brzo se ka njoj priblizava (lateralna brzina), pa racuna "time to
line crossing" (TTLC) - za koliko sekundi bi vozilo preslo ivicu trake ako
se nista ne promeni. Ako je TTLC ispod praga (i vozac ne upravlja aktivno),
sistem intervenise (koriguje upravljanje).
"""

from dataclasses import dataclass
from typing import Optional

from config import LKA_TTLC_THRESHOLD_S as TTLC_THRESHOLD_S


@dataclass(frozen=True)
class LKAOutput:
    intervene: bool
    time_to_crossing_s: Optional[float]  # None = vozilo se ne priblizava ivici
    distance_to_edge_m: float


class LKAVirtualECU:
    """Simulira ECU logiku za Lane Keep Assist."""

    def process(
        self,
        vehicle_speed_kmh: float,
        lateral_offset_m: float,
        lane_half_width_m: float,
        lateral_velocity_m_s: float,
        driver_steering_active: bool,
    ) -> LKAOutput:
        if vehicle_speed_kmh < 0:
            raise ValueError("vehicle_speed_kmh ne moze biti negativna")
        if lane_half_width_m <= 0:
            raise ValueError("lane_half_width_m mora biti pozitivna")

        distance_to_edge_m = lane_half_width_m - abs(lateral_offset_m)

        if distance_to_edge_m <= 0:
            # Vozilo je vec na ivici ili preko nje - nema vremena za gubljenje.
            time_to_crossing_s: Optional[float] = 0.0
        elif lateral_velocity_m_s <= 0:
            # Ne priblizava se ivici (miruje ili se vraca ka centru trake).
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
