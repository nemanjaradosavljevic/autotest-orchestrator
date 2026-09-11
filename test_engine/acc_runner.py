"""
ACC Test Engine - ucitava ACC scenario, pokrece Virtual ECU, poredi
expected vs actual i vraca PASS/FAIL. Struktura je namerno identicna
test_engine/runner.py (AEB) i test_engine/lka_runner.py (LKA).
"""

from dataclasses import asdict, dataclass
from typing import List

from scenarios.schemas import ACCScenario
from test_engine.acc_assertions import ACCExpectedResult, compute_acc_expected
from virtual_ecu.acc import ACCOutput, ACCVirtualECU


@dataclass(frozen=True)
class ACCTestResult:
    scenario: ACCScenario
    actual: ACCOutput
    expected: ACCExpectedResult
    passed: bool

    def to_dict(self) -> dict:
        d = asdict(self.scenario)
        d["actual_decelerate"] = self.actual.decelerate
        d["expected_decelerate"] = self.expected.decelerate
        d["actual_desired_gap_m"] = self.actual.desired_gap_m
        d["expected_desired_gap_with_margin_m"] = self.expected.desired_gap_with_margin_m
        d["relative_speed_m_s"] = self.actual.relative_speed_m_s
        d["passed"] = self.passed
        return d


class ACCTestEngine:
    def __init__(self) -> None:
        self.ecu = ACCVirtualECU()

    def run_scenario(self, scenario: ACCScenario) -> ACCTestResult:
        actual = self.ecu.process(
            ego_speed_kmh=scenario.ego_speed_kmh,
            lead_speed_kmh=scenario.lead_speed_kmh,
            gap_distance_m=scenario.gap_distance_m,
            driver_override_active=scenario.driver_override_active,
        )
        expected = compute_acc_expected(
            ego_speed_kmh=scenario.ego_speed_kmh,
            lead_speed_kmh=scenario.lead_speed_kmh,
            gap_distance_m=scenario.gap_distance_m,
            driver_override_active=scenario.driver_override_active,
        )
        passed = actual.decelerate == expected.decelerate
        return ACCTestResult(scenario=scenario, actual=actual, expected=expected, passed=passed)

    def run_batch(self, scenarios: List[ACCScenario]) -> List[ACCTestResult]:
        return [self.run_scenario(s) for s in scenarios]
