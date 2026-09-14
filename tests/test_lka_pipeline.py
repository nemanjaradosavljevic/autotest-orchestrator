"""
Integration tests for the LKA scenario generator, test engine, and failure
analysis - the same approach as test_generator.py / test_engine.py / test_failures.py
for AEB.
"""

from analytics.lka_failures import failure_pattern_summary, group_failures
from scenarios.generator import (
    LKA_RANGES,
    generate_edge_case_lka_scenarios,
    generate_random_lka_scenarios,
)
from test_engine.lka_runner import LKATestEngine
from test_engine.results import summarize


def test_generate_random_lka_scenarios_count():
    scenarios = generate_random_lka_scenarios(50, seed=1)
    assert len(scenarios) == 50


def test_generate_random_lka_scenarios_within_ranges():
    scenarios = generate_random_lka_scenarios(200, seed=7)
    speed_lo, speed_hi = LKA_RANGES["speed_kmh"]
    for s in scenarios:
        assert speed_lo <= s.vehicle_speed_kmh <= speed_hi
        assert s.lane_half_width_m > 0
        assert s.lateral_offset_m >= 0
        assert s.lateral_velocity_m_s >= 0
        assert isinstance(s.driver_steering_active, bool)


def test_generate_random_lka_scenarios_reproducible_with_seed():
    a = generate_random_lka_scenarios(20, seed=123)
    b = generate_random_lka_scenarios(20, seed=123)
    assert [x.to_dict() for x in a] == [x.to_dict() for x in b]


def test_generate_edge_case_lka_scenarios_not_empty():
    assert len(generate_edge_case_lka_scenarios()) > 0


def test_lka_engine_runs_batch_and_all_scenarios_get_a_result():
    scenarios = generate_random_lka_scenarios(100, seed=42)
    engine = LKATestEngine()
    results = engine.run_batch(scenarios)
    assert len(results) == 100
    for r in results:
        assert isinstance(r.passed, bool)


def test_lka_summary_counts_add_up():
    scenarios = generate_random_lka_scenarios(300, seed=5)
    engine = LKATestEngine()
    results = engine.run_batch(scenarios)
    summary = summarize(results)
    assert summary["total"] == 300
    assert summary["passed"] + summary["failed"] == 300


def test_lka_failure_grouping_only_contains_failed_results():
    scenarios = generate_random_lka_scenarios(500, seed=99)
    engine = LKATestEngine()
    results = engine.run_batch(scenarios)
    groups = group_failures(results)
    for items in groups.values():
        for r in items:
            assert r.passed is False


def test_lka_failure_pattern_summary_counts_match_groups():
    scenarios = generate_random_lka_scenarios(500, seed=99)
    engine = LKATestEngine()
    results = engine.run_batch(scenarios)
    groups = group_failures(results)
    summary = failure_pattern_summary(results)
    assert summary == {k: len(v) for k, v in groups.items()}
