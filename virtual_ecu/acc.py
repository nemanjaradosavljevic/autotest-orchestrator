"""
Virtual ECU - Adaptive Cruise Control (ACC) logika.

Treci use case pored AEB-a (virtual_ecu/aeb.py) i LKA-e (virtual_ecu/lka.py),
namerno napisan po istom obrascu: cist ulaz -> logika -> izlaz, bez
zavisnosti od ostatka sistema.

Pojednostavljen "constant time headway" model, koji se koristi i u pravim
ACC sistemima: zeljeno (bezbedno) rastojanje od vozila ispred raste
linearno sa brzinom (sto brze vozis, treba ti vise prostora/vremena da
reagujes), plus fiksni minimum razmak koji vazi i pri stajanju. Ako je
stvarni razmak manji od zeljenog, sistem usporava (osim ako vozac aktivno
pritiska gas, sto override-uje ACC).
"""

from dataclasses import dataclass

from config import ACC_MIN_GAP_M, ACC_TIME_HEADWAY_S


@dataclass(frozen=True)
class ACCOutput:
    decelerate: bool
    desired_gap_m: float
    relative_speed_m_s: float  # pozitivno = priblizavamo se vozilu ispred


class ACCVirtualECU:
    """Simulira ECU logiku za Adaptive Cruise Control."""

    def process(
        self,
        ego_speed_kmh: float,
        lead_speed_kmh: float,
        gap_distance_m: float,
        driver_override_active: bool,
    ) -> ACCOutput:
        if ego_speed_kmh < 0:
            raise ValueError("ego_speed_kmh ne moze biti negativna")
        if lead_speed_kmh < 0:
            raise ValueError("lead_speed_kmh ne moze biti negativna")
        if gap_distance_m < 0:
            raise ValueError("gap_distance_m ne moze biti negativan")

        ego_speed_m_s = ego_speed_kmh / 3.6
        lead_speed_m_s = lead_speed_kmh / 3.6
        relative_speed_m_s = ego_speed_m_s - lead_speed_m_s

        # Zeljeni razmak: fiksni minimum + vremenski razmak koji raste sa brzinom.
        desired_gap_m = ACC_MIN_GAP_M + ego_speed_m_s * ACC_TIME_HEADWAY_S

        decelerate = gap_distance_m < desired_gap_m

        if driver_override_active:
            decelerate = False

        return ACCOutput(
            decelerate=decelerate,
            desired_gap_m=round(desired_gap_m, 2),
            relative_speed_m_s=round(relative_speed_m_s, 2),
        )
