"""
Test Engine - the heart of the V1 prototype. Loads a scenario, runs the
Virtual ECU, compares expected vs actual, and returns a PASS/FAIL result
per scenario.
"""

from dataclasses import dataclass, asdict
from typing import List

from scenarios.schemas import Scenario
from virtual_ecu.aeb import AEBVirtualECU, ECUOutput
from test_engine.assertions import compute_expected, ExpectedResult


@dataclass(frozen=True)
class TestResult:
    scenario: Scenario
    actual: ECUOutput
    expected: ExpectedResult
    passed: bool

    def to_dict(self) -> dict:
        d = asdict(self.scenario)
        d["actual_brake"] = self.actual.brake
        d["expected_brake"] = self.expected.brake
        d["actual_stopping_distance_m"] = self.actual.stopping_distance_m
        d["expected_stopping_distance_m"] = self.expected.stopping_distance_m
        d["required_distance_with_margin_m"] = self.expected.required_distance_with_margin_m
        d["passed"] = self.passed
        return d


class TestEngine:
    def __init__(self) -> None:
        self.ecu = AEBVirtualECU()

    def run_scenario(self, scenario: Scenario) -> TestResult:
        actual = self.ecu.process(
            vehicle_speed_kmh=scenario.vehicle_speed_kmh,
            obstacle_distance_m=scenario.obstacle_distance_m,
            road_friction=scenario.road_friction,
            sensor_delay_ms=scenario.sensor_delay_ms,
        )
        expected = compute_expected(
            vehicle_speed_kmh=scenario.vehicle_speed_kmh,
            obstacle_distance_m=scenario.obstacle_distance_m,
            road_friction=scenario.road_friction,
            sensor_delay_ms=scenario.sensor_delay_ms,
        )
        passed = actual.brake == expected.brake
        return TestResult(scenario=scenario, actual=actual, expected=expected, passed=passed)

    def run_batch(self, scenarios: List[Scenario]) -> List[TestResult]:
        return [self.run_scenario(s) for s in scenarios]
