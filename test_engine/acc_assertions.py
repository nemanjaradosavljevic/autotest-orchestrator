"""
ACC Assertions - referentni ("oracle") proracun ocekivanog ponasanja za
Adaptive Cruise Control, po istom principu kao test_engine/assertions.py
(AEB) i test_engine/lka_assertions.py (LKA): "expected" je namerno strozija
(konzervativnija) verzija sistema, sa bezbednosnom marginom, dok "actual"
(virtual_ecu/acc.py) usporava tacno na granici zeljenog razmaka.

ACC_SAFETY_MARGIN ovde znaci: sistem treba da usporava kad je razmak manji
od zeljenog razmaka UVECANOG za marginu - isti "prag pomeren u
konzervativniju stranu" princip kao kod AEB-a/LKA-e, samo primenjen na
razmak od vozila ispred.
"""

from dataclasses import dataclass

from config import ACC_MIN_GAP_M, ACC_SAFETY_MARGIN, ACC_TIME_HEADWAY_S


@dataclass(frozen=True)
class ACCExpectedResult:
    decelerate: bool
    desired_gap_with_margin_m: float


def compute_acc_expected(
    ego_speed_kmh: float,
    lead_speed_kmh: float,
    gap_distance_m: float,
    driver_override_active: bool,
) -> ACCExpectedResult:
    ego_speed_m_s = ego_speed_kmh / 3.6
    desired_gap_m = ACC_MIN_GAP_M + ego_speed_m_s * ACC_TIME_HEADWAY_S
    desired_gap_with_margin_m = desired_gap_m * ACC_SAFETY_MARGIN

    decelerate = gap_distance_m < desired_gap_with_margin_m

    if driver_override_active:
        decelerate = False

    return ACCExpectedResult(
        decelerate=decelerate,
        desired_gap_with_margin_m=round(desired_gap_with_margin_m, 2),
    )
