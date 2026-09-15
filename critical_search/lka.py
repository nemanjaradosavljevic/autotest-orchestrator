"""
Critical scenario search - LKA.

Same idea as critical_search/aeb.py - see that module's docstring for the
full rationale. The "gray zone" here is on the projected time-to-lane-
crossing (TTLC): a FAIL happens when TTLC lands strictly between
LKA_TTLC_THRESHOLD_S (the actual system's threshold) and
LKA_TTLC_THRESHOLD_S * LKA_SAFETY_MARGIN (the oracle's more cautious,
larger threshold - see test_engine/lka_assertions.py), because the actual
system only reacts to a TTLC at or below its stricter threshold while the
spec wants it to react earlier, with more time to spare.

driver_steering_active is left OFF for every scenario this search
generates: virtual_ecu/lka.py and test_engine/lka_assertions.py both force
intervene=False whenever it's True, on both the actual and expected side,
so it can never produce a FAIL - there's nothing for the search to find
there. vehicle_speed_kmh isn't used anywhere in the TTLC/intervene
formula either (virtual_ecu/lka.py only validates it isn't negative), so
it isn't searched - it's filled in with a realistic-looking value only for
display once a result is found.
"""

import random
from dataclasses import dataclass
from typing import Dict, List

from config import LKA_SAFETY_MARGIN, LKA_SCENARIO_RANGES, LKA_TTLC_THRESHOLD_S
from scenarios.schemas import LKAScenario
from test_engine.lka_assertions import compute_lka_expected
from test_engine.lka_runner import LKATestResult
from virtual_ecu.lka import LKAOutput, LKAVirtualECU

SPEED_RANGE = LKA_SCENARIO_RANGES["speed_kmh"]
HALF_WIDTH_RANGE = LKA_SCENARIO_RANGES["lane_half_width_m"]
LATERAL_VELOCITY_RANGE = LKA_SCENARIO_RANGES["lateral_velocity_m_s"]
MARGIN_THRESHOLD_S = LKA_TTLC_THRESHOLD_S * LKA_SAFETY_MARGIN

STEP_FRACTION = 0.12
ACCEPT_WORSE_PROB = 0.03


@dataclass(frozen=True)
class CriticalResult:
    result: LKATestResult
    risk_score: float


def _risk(actual: LKAOutput) -> float:
    """Positive means a genuine FAIL; see the module docstring. A TTLC of
    None (not drifting toward the edge - lateral velocity <= 0, or already
    centered) can never be a FAIL, so it's scored as strongly negative to
    steer the search away from that region."""
    if actual.time_to_crossing_s is None:
        return -1000.0
    d_actual = actual.time_to_crossing_s - LKA_TTLC_THRESHOLD_S
    d_expected = actual.time_to_crossing_s - MARGIN_THRESHOLD_S
    return min(d_actual, -d_expected)


def _clamp(value: float, bounds) -> float:
    lo, hi = bounds
    return max(lo, min(hi, value))


def _random_params(rng: random.Random) -> Dict[str, float]:
    lane_half_width_m = rng.uniform(*HALF_WIDTH_RANGE)
    return {
        "lane_half_width_m": lane_half_width_m,
        # Same "up to 5% past the edge" allowance scenarios/generator.py
        # uses - a vehicle rarely teleports abruptly out of the lane.
        "lateral_offset_m": rng.uniform(0, lane_half_width_m * 1.05),
        "lateral_velocity_m_s": rng.uniform(*LATERAL_VELOCITY_RANGE),
    }


def _perturb(params: Dict[str, float], rng: random.Random) -> Dict[str, float]:
    new_params = dict(params)
    key = rng.choice(["lane_half_width_m", "lateral_offset_m", "lateral_velocity_m_s"])

    if key == "lane_half_width_m":
        lo, hi = HALF_WIDTH_RANGE
        step = rng.gauss(0, (hi - lo) * STEP_FRACTION)
        new_params[key] = _clamp(params[key] + step, HALF_WIDTH_RANGE)
        # Keep the offset a valid position within the (possibly now
        # narrower) lane.
        max_offset = new_params["lane_half_width_m"] * 1.05
        new_params["lateral_offset_m"] = min(new_params["lateral_offset_m"], max_offset)
    elif key == "lateral_offset_m":
        max_offset = new_params["lane_half_width_m"] * 1.05
        step = rng.gauss(0, max_offset * STEP_FRACTION)
        new_params[key] = _clamp(params[key] + step, (0, max_offset))
    else:
        lo, hi = LATERAL_VELOCITY_RANGE
        step = rng.gauss(0, (hi - lo) * STEP_FRACTION)
        new_params[key] = _clamp(params[key] + step, LATERAL_VELOCITY_RANGE)

    return new_params


def find_critical_scenarios(restarts: int = 40, iterations: int = 150, seed: int = 123) -> List[CriticalResult]:
    rng = random.Random(seed)
    ecu = LKAVirtualECU()
    results: List[CriticalResult] = []
    scenario_id = 1

    for _ in range(restarts):
        params = _random_params(rng)
        actual = ecu.process(vehicle_speed_kmh=0, driver_steering_active=False, **params)
        best_risk = _risk(actual)

        for _step in range(iterations):
            candidate = _perturb(params, rng)
            c_actual = ecu.process(vehicle_speed_kmh=0, driver_steering_active=False, **candidate)
            c_risk = _risk(c_actual)
            if c_risk > best_risk or rng.random() < ACCEPT_WORSE_PROB:
                params, actual, best_risk = candidate, c_actual, c_risk

        if best_risk <= 0:
            continue

        rounded = {
            "lane_half_width_m": round(params["lane_half_width_m"], 2),
            "lateral_offset_m": round(params["lateral_offset_m"], 3),
            "lateral_velocity_m_s": round(params["lateral_velocity_m_s"], 3),
        }
        # Cosmetic only - doesn't affect the TTLC/intervene decision at all.
        display_speed = round(rng.uniform(*SPEED_RANGE), 1)

        final_actual = ecu.process(vehicle_speed_kmh=display_speed, driver_steering_active=False, **rounded)
        final_expected = compute_lka_expected(
            vehicle_speed_kmh=display_speed, driver_steering_active=False, **rounded
        )
        final_risk = _risk(final_actual)
        if final_risk <= 0:
            continue

        scenario = LKAScenario(
            id=scenario_id, vehicle_speed_kmh=display_speed, driver_steering_active=False, **rounded
        )
        result = LKATestResult(
            scenario=scenario,
            actual=final_actual,
            expected=final_expected,
            passed=final_actual.intervene == final_expected.intervene,
        )
        results.append(CriticalResult(result=result, risk_score=round(final_risk, 3)))
        scenario_id += 1

    results.sort(key=lambda r: r.risk_score, reverse=True)
    return results
