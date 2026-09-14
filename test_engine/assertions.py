"""
Assertions - reference ("oracle") calculation of expected behavior, used
to verify that the Virtual ECU (virtual_ecu/aeb.py) behaves correctly.

Deliberately kept in its own file (as in the project plan:
test_engine/{runner, assertions, results}.py), so the test infrastructure
stays separate from the implementation it tests.

SAFETY MARGIN: this module is deliberately NOT identical to
virtual_ecu/aeb.py. A real safety-critical requirement (as in the real
automotive world too) is that the system brakes BEFORE it physically
reaches the limit - with a reserve, because real-world conditions (road
surface irregularities, tires, sensor noise) are never perfectly known.
That's why "expected" here requires SAFETY_MARGIN (15%) more space than
the AEB implementation (aeb.py) currently uses. When the actual distance
to the obstacle falls between the "bare" physical limit and the limit
with margin, the ECU (actual) says OFF, while the specification
(expected) says it should have been ON -> FAIL. These are real, useful
failures for failure analysis (analytics/failures.py), not an
artificially injected bug.

When a real STM32/CAN ECU or a CANoe/dSPACE integration is added in
V2/V3, this same code remains the "expected" side of the comparison,
while "actual" comes from the real device - the separation then starts
catching real differences in firmware, rounding, and delays as well.

For a fully independent check that the pure physical formula (without
the margin) is implemented correctly, see the manually calculated edge
cases in tests/test_aeb.py - they test aeb.py directly and do not
depend on this file.
"""

from dataclasses import dataclass

from config import AEB_SAFETY_MARGIN as SAFETY_MARGIN
from config import GRAVITY_M_S2

# Note: SAFETY_MARGIN (the "reserve" for uncertainty in real-world
# conditions) and GRAVITY_M_S2 now live in config.py, so they're in the
# same place as all the other tunable thresholds in the system.


@dataclass(frozen=True)
class ExpectedResult:
    brake: bool
    stopping_distance_m: float
    required_distance_with_margin_m: float


def compute_expected(
    vehicle_speed_kmh: float,
    obstacle_distance_m: float,
    road_friction: float,
    sensor_delay_ms: float,
) -> ExpectedResult:
    speed_m_s = vehicle_speed_kmh / 3.6
    reaction_distance = speed_m_s * (sensor_delay_ms / 1000.0)
    braking_distance = (speed_m_s ** 2) / (2 * road_friction * GRAVITY_M_S2)
    stopping_distance = reaction_distance + braking_distance
    required_distance_with_margin = stopping_distance * SAFETY_MARGIN
    brake = obstacle_distance_m <= required_distance_with_margin
    return ExpectedResult(
        brake=brake,
        stopping_distance_m=round(stopping_distance, 2),
        required_distance_with_margin_m=round(required_distance_with_margin, 2),
    )
