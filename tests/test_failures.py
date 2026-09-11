from analytics.failures import failure_pattern_summary, group_failures
from scenarios.generator import generate_random_scenarios
from test_engine.runner import TestEngine


def test_failure_grouping_only_contains_failed_results():
    scenarios = generate_random_scenarios(500, seed=99)
    engine = TestEngine()
    results = engine.run_batch(scenarios)
    groups = group_failures(results)
    for items in groups.values():
        for r in items:
            assert r.passed is False


def test_failure_pattern_summary_counts_match_groups():
    scenarios = generate_random_scenarios(500, seed=99)
    engine = TestEngine()
    results = engine.run_batch(scenarios)
    groups = group_failures(results)
    summary = failure_pattern_summary(results)
    assert summary == {k: len(v) for k, v in groups.items()}
