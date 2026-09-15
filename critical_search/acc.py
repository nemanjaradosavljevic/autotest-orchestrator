"""
Critical scenario search - ACC.

Same idea as critical_search/aeb.py - see that module's docstring for the
full rationale. The "gray zone" here is on the actual gap: a FAIL happens
when gap_distance_m lands strictly between the actual desired gap
(virtual_ecu/acc.py) and that same gap increased by ACC_SAFETY_MARGIN (the
oracle's more cautious version, test_engine/acc_assertions.py).

driver_override_active is left OFF for every scenario this search
generates - both virtual_ecu/acc.py and test_engine/acc_assertions.py
force decelerate=False whenever it's True, on both sides, so it can never
produce a FAIL. lead_speed_kmh doesn't affect the decelerate decision at
all either (only the informational relative_speed_m_s output field does),
so it isn't searched - it's sampled once per result purely for a
realistic-looking scenario.
"""

import random
from dataclasses import dataclass
from typing import Dict, List

from config import ACC_SCENARIO_RANGES
from scenarios.schemas import ACCScenario
from test_engine.acc_assertions import ACCExpectedResult, compute_acc_expected
from test_engine.acc_runner import ACCTestResult
from virtual_ecu.acc import ACCOutput, ACCVirtualECU

EGO_SPEED_RANGE = ACC_SCENARIO_RANGES["ego_speed_kmh"]
LEAD_SPEED_RANGE = ACC_SCENARIO_RANGES["lead_speed_kmh"]
GAP_RANGE = ACC_SCENARIO_RANGES["gap_distance_m"]

STEP_FRACTION = 0.12
ACCEPT_WORSE_PROB = 0.03


@dataclass(frozen=True)
class CriticalResult:
    result: ACCTestResult
    risk_score: float


def _risk(actual: ACCOutput, expected: ACCExpectedResult, gap_distance_m: float) -> float:
    d_actual = gap_distance_m - actual.desired_gap_m
    d_expected = gap_distance_m - expected.desired_gap_with_margin_m
    return min(d_actual, -d_expected)


def _clamp(value: float, bounds) -> float:
    lo, hi = bounds
    return max(lo, min(hi, value))


def _random_params(rng: random.Random) -> Dict[str, float]:
    return {
        "ego_speed_kmh": rng.uniform(*EGO_SPEED_RANGE),
        "gap_distance_m": rng.uniform(*GAP_RANGE),
    }


def _perturb(params: Dict[str, float], rng: random.Random) -> Dict[str, float]:
    ranges = {"ego_speed_kmh": EGO_SPEED_RANGE, "gap_distance_m": GAP_RANGE}
    key = rng.choice(list(ranges))
    lo, hi = ranges[key]
    step = rng.gauss(0, (hi - lo) * STEP_FRACTION)
    new_params = dict(params)
    new_params[key] = _clamp(params[key] + step, (lo, hi))
    return new_params


def find_critical_scenarios(restarts: int = 40, iterations: int = 150, seed: int = 123) -> List[CriticalResult]:
    rng = random.Random(seed)
    ecu = ACCVirtualECU()
    results: List[CriticalResult] = []
    scenario_id = 1

    for _ in range(restarts):
        params = _random_params(rng)
        lead_speed = rng.uniform(*LEAD_SPEED_RANGE)  # cosmetic only - doesn't affect the decision
        actual = ecu.process(lead_speed_kmh=lead_speed, driver_override_active=False, **params)
        expected = compute_acc_expected(lead_speed_kmh=lead_speed, driver_override_active=False, **params)
        best_risk = _risk(actual, expected, params["gap_distance_m"])

        for _step in range(iterations):
            candidate = _perturb(params, rng)
            c_actual = ecu.process(lead_speed_kmh=lead_speed, driver_override_active=False, **candidate)
            c_expected = compute_acc_expected(lead_speed_kmh=lead_speed, driver_override_active=False, **candidate)
            c_risk = _risk(c_actual, c_expected, candidate["gap_distance_m"])
            if c_risk > best_risk or rng.random() < ACCEPT_WORSE_PROB:
                params, actual, expected, best_risk = candidate, c_actual, c_expected, c_risk

        if best_risk <= 0:
            continue

        rounded = {
            "ego_speed_kmh": round(params["ego_speed_kmh"], 1),
            "gap_distance_m": round(params["gap_distance_m"], 1),
        }
        display_lead_speed = round(lead_speed, 1)
        final_actual = ecu.process(lead_speed_kmh=display_lead_speed, driver_override_active=False, **rounded)
        final_expected = compute_acc_expected(
            lead_speed_kmh=display_lead_speed, driver_override_active=False, **rounded
        )
        final_risk = _risk(final_actual, final_expected, rounded["gap_distance_m"])
        if final_risk <= 0:
            continue

        scenario = ACCScenario(
            id=scenario_id, lead_speed_kmh=display_lead_speed, driver_override_active=False, **rounded
        )
        result = ACCTestResult(
            scenario=scenario,
            actual=final_actual,
            expected=final_expected,
            passed=final_actual.decelerate == final_expected.decelerate,
        )
        results.append(CriticalResult(result=result, risk_score=round(final_risk, 3)))
        scenario_id += 1

    results.sort(key=lambda r: r.risk_score, reverse=True)
    return results
