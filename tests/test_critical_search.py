"""
Tests for critical_search/{aeb,lka,acc}.py - the hill-climbing search that
deliberately hunts for scenarios inside the safety-margin "gray zone",
instead of relying on scenarios/generator.py's random sampling to stumble
into it (see the module docstrings in critical_search/ for the full
rationale).

These are ordinary example-based tests (not property-based like
tests/test_properties.py) because the thing being tested here is the
search algorithm's own behavior with a fixed seed, not an invariant over
arbitrary inputs - a fixed, reasonable search budget should reliably find
several genuine counterexamples, and every one it reports must be
self-consistent (a real FAIL, with a positive risk score) and the list
must come back sorted worst-first.
"""

from critical_search.acc import find_critical_scenarios as find_acc_critical
from critical_search.aeb import find_critical_scenarios as find_aeb_critical
from critical_search.lka import find_critical_scenarios as find_lka_critical


def _assert_well_formed(results):
    assert len(results) > 0
    for r in results:
        assert r.result.passed is False
        assert r.risk_score > 0
    risk_scores = [r.risk_score for r in results]
    assert risk_scores == sorted(risk_scores, reverse=True)
    # Every scenario id must be unique within one search's results.
    ids = [r.result.scenario.id for r in results]
    assert len(ids) == len(set(ids))


def test_aeb_critical_search_finds_genuine_fails():
    results = find_aeb_critical(restarts=20, iterations=100, seed=1)
    _assert_well_formed(results)


def test_lka_critical_search_finds_genuine_fails():
    results = find_lka_critical(restarts=20, iterations=100, seed=1)
    _assert_well_formed(results)


def test_acc_critical_search_finds_genuine_fails():
    results = find_acc_critical(restarts=20, iterations=100, seed=1)
    _assert_well_formed(results)


def test_aeb_critical_search_is_deterministic():
    a = find_aeb_critical(restarts=15, iterations=80, seed=7)
    b = find_aeb_critical(restarts=15, iterations=80, seed=7)
    assert [r.risk_score for r in a] == [r.risk_score for r in b]
    assert [r.result.scenario.to_dict() for r in a] == [r.result.scenario.to_dict() for r in b]


def test_lka_critical_search_is_deterministic():
    a = find_lka_critical(restarts=15, iterations=80, seed=7)
    b = find_lka_critical(restarts=15, iterations=80, seed=7)
    assert [r.risk_score for r in a] == [r.risk_score for r in b]


def test_acc_critical_search_is_deterministic():
    a = find_acc_critical(restarts=15, iterations=80, seed=7)
    b = find_acc_critical(restarts=15, iterations=80, seed=7)
    assert [r.risk_score for r in a] == [r.risk_score for r in b]


def test_aeb_critical_search_different_seeds_explore_differently():
    a = find_aeb_critical(restarts=15, iterations=80, seed=1)
    b = find_aeb_critical(restarts=15, iterations=80, seed=2)
    # Not a strict guarantee for every possible pair of seeds, but with two
    # different seeds over 15 restarts each, getting the exact same set of
    # (rounded) scenarios back would mean the search isn't actually using
    # its randomness at all.
    a_scenarios = [r.result.scenario.to_dict() for r in a]
    b_scenarios = [r.result.scenario.to_dict() for r in b]
    assert a_scenarios != b_scenarios


def test_aeb_critical_search_respects_scenario_ranges():
    from config import AEB_SCENARIO_RANGES

    results = find_aeb_critical(restarts=20, iterations=100, seed=3)
    speed_lo, speed_hi = AEB_SCENARIO_RANGES["speed_kmh"]
    dist_lo, dist_hi = AEB_SCENARIO_RANGES["obstacle_distance_m"]
    friction_lo, friction_hi = AEB_SCENARIO_RANGES["road_friction"]
    delay_lo, delay_hi = AEB_SCENARIO_RANGES["sensor_delay_ms"]
    for r in results:
        s = r.result.scenario
        assert speed_lo <= s.vehicle_speed_kmh <= speed_hi
        assert dist_lo <= s.obstacle_distance_m <= dist_hi
        assert friction_lo <= s.road_friction <= friction_hi
        assert delay_lo <= s.sensor_delay_ms <= delay_hi


def test_lka_critical_search_never_returns_steering_active():
    results = find_lka_critical(restarts=20, iterations=100, seed=3)
    assert all(r.result.scenario.driver_steering_active is False for r in results)


def test_acc_critical_search_never_returns_driver_override():
    results = find_acc_critical(restarts=20, iterations=100, seed=3)
    assert all(r.result.scenario.driver_override_active is False for r in results)
