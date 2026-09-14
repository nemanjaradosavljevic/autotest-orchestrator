"""
LKA Test Engine - loads an LKA scenario, runs the Virtual ECU, compares
expected vs actual, and returns PASS/FAIL. The structure is deliberately
identical to test_engine/runner.py (AEB) - proof that the pattern repeats
for a new use case without needing to reinvent the same logic.
"""

from dataclasses import asdict, dataclass
from typing import List

from scenarios.schemas import LKAScenario
from test_engine.lka_assertions import LKAExpectedResult, compute_lka_expected
from virtual_ecu.lka import LKAOutput, LKAVirtualECU


@dataclass(frozen=True)
class LKATestResult:
    scenario: LKAScenario
    actual: LKAOutput
    expected: LKAExpectedResult
    passed: bool

    def to_dict(self) -> dict:
        d = asdict(self.scenario)
        d["actual_intervene"] = self.actual.intervene
        d["expected_intervene"] = self.expected.intervene
        d["actual_ttlc_s"] = self.actual.time_to_crossing_s
        d["expected_ttlc_s"] = self.expected.time_to_crossing_s
        d["distance_to_edge_m"] = self.actual.distance_to_edge_m
        d["passed"] = self.passed
        return d


class LKATestEngine:
    def __init__(self) -> None:
        self.ecu = LKAVirtualECU()

    def run_scenario(self, scenario: LKAScenario) -> LKATestResult:
        actual = self.ecu.process(
            vehicle_speed_kmh=scenario.vehicle_speed_kmh,
            lateral_offset_m=scenario.lateral_offset_m,
            lane_half_width_m=scenario.lane_half_width_m,
            lateral_velocity_m_s=scenario.lateral_velocity_m_s,
            driver_steering_active=scenario.driver_steering_active,
        )
        expected = compute_lka_expected(
            vehicle_speed_kmh=scenario.vehicle_speed_kmh,
            lateral_offset_m=scenario.lateral_offset_m,
            lane_half_width_m=scenario.lane_half_width_m,
            lateral_velocity_m_s=scenario.lateral_velocity_m_s,
            driver_steering_active=scenario.driver_steering_active,
        )
        passed = actual.intervene == expected.intervene
        return LKATestResult(scenario=scenario, actual=actual, expected=expected, passed=passed)

    def run_batch(self, scenarios: List[LKAScenario]) -> List[LKATestResult]:
        return [self.run_scenario(s) for s in scenarios]
