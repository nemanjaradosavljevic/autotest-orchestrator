"""
Virtual ECU - Adaptive Cruise Control (ACC) logic.

A third use case alongside AEB (virtual_ecu/aeb.py) and LKA
(virtual_ecu/lka.py), deliberately written following the same pattern:
clean input -> logic -> output, with no dependency on the rest of the
system.

A simplified "constant time headway" model, also used in real ACC systems:
the desired (safe) distance to the lead vehicle grows linearly with speed
(the faster you drive, the more space/time you need to react), plus a
fixed minimum gap that applies even at a standstill. If the actual gap is
smaller than the desired one, the system decelerates (unless the driver is
actively pressing the accelerator, which overrides the ACC).
"""

from dataclasses import dataclass

from config import ACC_MIN_GAP_M, ACC_TIME_HEADWAY_S


@dataclass(frozen=True)
class ACCOutput:
    decelerate: bool
    desired_gap_m: float
    relative_speed_m_s: float  # positive = closing in on the lead vehicle


class ACCVirtualECU:
    """Simulates the ECU logic for Adaptive Cruise Control."""

    def process(
        self,
        ego_speed_kmh: float,
        lead_speed_kmh: float,
        gap_distance_m: float,
        driver_override_active: bool,
    ) -> ACCOutput:
        if ego_speed_kmh < 0:
            raise ValueError("ego_speed_kmh cannot be negative")
        if lead_speed_kmh < 0:
            raise ValueError("lead_speed_kmh cannot be negative")
        if gap_distance_m < 0:
            raise ValueError("gap_distance_m cannot be negative")

        ego_speed_m_s = ego_speed_kmh / 3.6
        lead_speed_m_s = lead_speed_kmh / 3.6
        relative_speed_m_s = ego_speed_m_s - lead_speed_m_s

        # Desired gap: fixed minimum + time headway that grows with speed.
        desired_gap_m = ACC_MIN_GAP_M + ego_speed_m_s * ACC_TIME_HEADWAY_S

        decelerate = gap_distance_m < desired_gap_m

        if driver_override_active:
            decelerate = False

        return ACCOutput(
            decelerate=decelerate,
            desired_gap_m=round(desired_gap_m, 2),
            relative_speed_m_s=round(relative_speed_m_s, 2),
        )
