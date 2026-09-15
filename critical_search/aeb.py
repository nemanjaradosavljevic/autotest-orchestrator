"""
Critical scenario search - AEB.

scenarios/generator.py samples each parameter independently and
uniformly, so it only lands inside the safety-margin "gray zone" - where
the actual ECU (virtual_ecu/aeb.py) says OFF but the oracle
(test_engine/assertions.py) says it should have said ON - by chance, and
that zone can be a thin sliver of the full 4-dimensional parameter space
(speed, obstacle distance, friction, sensor delay). This module instead
deliberately searches for it.

It treats the ECU and the oracle as a black box - calling
AEBVirtualECU.process() and compute_expected() and reading their outputs,
never their source code - the same way a hardware-in-the-loop tool would
have to once V2 replaces the virtual ECU with a real STM32/CAN device and
there's no formula left to read. A hill-climbing search with random
restarts nudges scenario parameters toward the gray zone step by step,
occasionally accepting a slightly worse step too (a simplified
simulated-annealing touch) so it doesn't get stuck the moment it finds a
merely-OK spot. This is the same idea the automotive testing world calls
"critical scenario search" / "falsification" in the context of ISO 21448
(SOTIF).

See test_engine/assertions.py for what the "gray zone" actually means and
why it exists at all.
"""

import random
from dataclasses import dataclass
from typing import Dict, List

from config import AEB_SCENARIO_RANGES
from scenarios.schemas import Scenario
from test_engine.assertions import ExpectedResult, compute_expected
from test_engine.runner import TestResult
from virtual_ecu.aeb import AEBVirtualECU, ECUOutput

SPEED_RANGE = AEB_SCENARIO_RANGES["speed_kmh"]
DISTANCE_RANGE = AEB_SCENARIO_RANGES["obstacle_distance_m"]
FRICTION_RANGE = AEB_SCENARIO_RANGES["road_friction"]
DELAY_RANGE = AEB_SCENARIO_RANGES["sensor_delay_ms"]

# One random-walk step changes a parameter by at most roughly this
# fraction of its full range - kept small so the search can settle
# precisely onto the (usually narrow) gray zone instead of stepping
# straight over it.
STEP_FRACTION = 0.12
# Flat probability of accepting a worse candidate anyway - a simplified
# simulated-annealing touch that helps the search escape a merely-OK spot
# instead of settling for it.
ACCEPT_WORSE_PROB = 0.03


@dataclass(frozen=True)
class CriticalResult:
    result: TestResult
    risk_score: float


def _risk(actual: ECUOutput, expected: ExpectedResult, obstacle_distance_m: float) -> float:
    """How deep inside the gray zone this scenario sits: positive means a
    genuine FAIL (actual=OFF, expected=ON), and the further above zero the
    more robust a counterexample it is (the obstacle distance sits well
    clear of BOTH edges of the zone, not right on the boundary by luck).
    Zero or below means it currently agrees - still a useful gradient,
    since "less negative" means "closer to the zone" and guides the
    search even from a passing scenario."""
    d_actual = obstacle_distance_m - actual.stopping_distance_m
    d_expected = obstacle_distance_m - expected.required_distance_with_margin_m
    return min(d_actual, -d_expected)


def _clamp(value: float, bounds) -> float:
    lo, hi = bounds
    return max(lo, min(hi, value))


def _random_params(rng: random.Random) -> Dict[str, float]:
    return {
        "vehicle_speed_kmh": rng.uniform(*SPEED_RANGE),
        "obstacle_distance_m": rng.uniform(*DISTANCE_RANGE),
        "road_friction": rng.uniform(*FRICTION_RANGE),
        "sensor_delay_ms": rng.uniform(*DELAY_RANGE),
    }


def _perturb(params: Dict[str, float], rng: random.Random) -> Dict[str, float]:
    """Nudges exactly one parameter by a small random step - changing one
    dimension at a time (rather than all four at once) makes each step's
    effect on the risk score easy to attribute, which is what lets
    hill-climbing reliably improve step over step instead of wandering."""
    ranges = {
        "vehicle_speed_kmh": SPEED_RANGE,
        "obstacle_distance_m": DISTANCE_RANGE,
        "road_friction": FRICTION_RANGE,
        "sensor_delay_ms": DELAY_RANGE,
    }
    key = rng.choice(list(ranges))
    lo, hi = ranges[key]
    step = rng.gauss(0, (hi - lo) * STEP_FRACTION)
    new_params = dict(params)
    new_params[key] = _clamp(params[key] + step, ranges[key])
    return new_params


def find_critical_scenarios(restarts: int = 40, iterations: int = 150, seed: int = 123) -> List[CriticalResult]:
    """Runs `restarts` independent hill-climbing searches (each
    `iterations` steps long) and returns every restart that ended inside
    the gray zone, ranked by risk_score (most robust counterexample
    first). A restart that never finds the zone contributes nothing - not
    every one has to succeed, since exploring from many different
    starting points is what covers the space."""
    rng = random.Random(seed)
    ecu = AEBVirtualECU()
    results: List[CriticalResult] = []
    scenario_id = 1

    for _ in range(restarts):
        params = _random_params(rng)
        actual = ecu.process(**params)
        expected = compute_expected(**params)
        best_risk = _risk(actual, expected, params["obstacle_distance_m"])

        for _step in range(iterations):
            candidate = _perturb(params, rng)
            c_actual = ecu.process(**candidate)
            c_expected = compute_expected(**candidate)
            c_risk = _risk(c_actual, c_expected, candidate["obstacle_distance_m"])
            if c_risk > best_risk or rng.random() < ACCEPT_WORSE_PROB:
                params, actual, expected, best_risk = candidate, c_actual, c_expected, c_risk

        if best_risk <= 0:
            continue

        # The search itself works in full precision so it can settle
        # exactly onto the (often narrow) gray zone; only now do we round
        # to "scenario file" precision, and recompute from the ROUNDED
        # values - so the numbers this function reports are always
        # perfectly self-consistent with the actual/expected/passed they
        # come with, never just close.
        rounded = {
            "vehicle_speed_kmh": round(params["vehicle_speed_kmh"], 1),
            "obstacle_distance_m": round(params["obstacle_distance_m"], 1),
            "road_friction": round(params["road_friction"], 3),
            "sensor_delay_ms": round(params["sensor_delay_ms"], 0),
        }
        final_actual = ecu.process(**rounded)
        final_expected = compute_expected(**rounded)
        final_risk = _risk(final_actual, final_expected, rounded["obstacle_distance_m"])
        if final_risk <= 0:
            continue

        weather = "rain" if rounded["road_friction"] < 0.7 else "dry"
        scenario = Scenario(id=scenario_id, weather=weather, **rounded)
        result = TestResult(
            scenario=scenario,
            actual=final_actual,
            expected=final_expected,
            passed=final_actual.brake == final_expected.brake,
        )
        results.append(CriticalResult(result=result, risk_score=round(final_risk, 3)))
        scenario_id += 1

    results.sort(key=lambda r: r.risk_score, reverse=True)
    return results
