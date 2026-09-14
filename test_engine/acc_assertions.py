"""
ACC Assertions - reference ("oracle") calculation of expected behavior for
Adaptive Cruise Control, following the same principle as
test_engine/assertions.py (AEB) and test_engine/lka_assertions.py (LKA):
"expected" is deliberately a stricter (more conservative) version of the
system, with a safety margin, while "actual" (virtual_ecu/acc.py) decelerates
exactly at the boundary of the desired gap.

ACC_SAFETY_MARGIN here means: the system should decelerate when the gap is
smaller than the desired gap INCREASED by the margin - the same "threshold
shifted to the more conservative side" principle as with AEB/LKA, just
applied to the gap to the lead vehicle.
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
