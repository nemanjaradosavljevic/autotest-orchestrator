from scenarios.generator import generate_random_scenarios
from test_engine.results import summarize
from test_engine.runner import TestEngine


def test_engine_runs_batch_and_all_scenarios_get_a_result():
    scenarios = generate_random_scenarios(100, seed=42)
    engine = TestEngine()
    results = engine.run_batch(scenarios)
    assert len(results) == 100
    for r in results:
        assert isinstance(r.passed, bool)


def test_summary_counts_add_up():
    scenarios = generate_random_scenarios(300, seed=5)
    engine = TestEngine()
    results = engine.run_batch(scenarios)
    summary = summarize(results)
    assert summary["total"] == 300
    assert summary["passed"] + summary["failed"] == 300
