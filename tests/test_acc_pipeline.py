"""
Integracioni testovi za ACC scenario generator, test engine i failure
analizu - isti princip kao test_generator.py / test_engine.py /
test_failures.py (AEB) i test_lka_pipeline.py (LKA).
"""

from analytics.acc_failures import failure_pattern_summary, group_failures
from scenarios.generator import (
    ACC_RANGES,
    generate_edge_case_acc_scenarios,
    generate_random_acc_scenarios,
)
from test_engine.acc_runner import ACCTestEngine
from test_engine.results import summarize


def test_generate_random_acc_scenarios_count():
    scenarios = generate_random_acc_scenarios(50, seed=1)
    assert len(scenarios) == 50


def test_generate_random_acc_scenarios_within_ranges():
    scenarios = generate_random_acc_scenarios(200, seed=7)
    ego_lo, ego_hi = ACC_RANGES["ego_speed_kmh"]
    for s in scenarios:
        assert ego_lo <= s.ego_speed_kmh <= ego_hi
        assert s.lead_speed_kmh >= 0
        assert s.gap_distance_m >= 0
        assert isinstance(s.driver_override_active, bool)


def test_generate_random_acc_scenarios_reproducible_with_seed():
    a = generate_random_acc_scenarios(20, seed=123)
    b = generate_random_acc_scenarios(20, seed=123)
    assert [x.to_dict() for x in a] == [x.to_dict() for x in b]


def test_generate_edge_case_acc_scenarios_not_empty():
    assert len(generate_edge_case_acc_scenarios()) > 0


def test_acc_engine_runs_batch_and_all_scenarios_get_a_result():
    scenarios = generate_random_acc_scenarios(100, seed=42)
    engine = ACCTestEngine()
    results = engine.run_batch(scenarios)
    assert len(results) == 100
    for r in results:
        assert isinstance(r.passed, bool)


def test_acc_summary_counts_add_up():
    scenarios = generate_random_acc_scenarios(300, seed=5)
    engine = ACCTestEngine()
    results = engine.run_batch(scenarios)
    summary = summarize(results)
    assert summary["total"] == 300
    assert summary["passed"] + summary["failed"] == 300


def test_acc_failure_grouping_only_contains_failed_results():
    scenarios = generate_random_acc_scenarios(500, seed=99)
    engine = ACCTestEngine()
    results = engine.run_batch(scenarios)
    groups = group_failures(results)
    for items in groups.values():
        for r in items:
            assert r.passed is False


def test_acc_failure_pattern_summary_counts_match_groups():
    scenarios = generate_random_acc_scenarios(500, seed=99)
    engine = ACCTestEngine()
    results = engine.run_batch(scenarios)
    groups = group_failures(results)
    summary = failure_pattern_summary(results)
    assert summary == {k: len(v) for k, v in groups.items()}
