from scenarios.generator import (
    DEFAULT_RANGES,
    generate_edge_case_scenarios,
    generate_random_scenarios,
)


def test_generate_random_scenarios_count():
    scenarios = generate_random_scenarios(50, seed=1)
    assert len(scenarios) == 50


def test_generate_random_scenarios_within_ranges():
    scenarios = generate_random_scenarios(200, seed=7)
    speed_lo, speed_hi = DEFAULT_RANGES["speed_kmh"]
    dist_lo, dist_hi = DEFAULT_RANGES["obstacle_distance_m"]
    for s in scenarios:
        assert speed_lo <= s.vehicle_speed_kmh <= speed_hi
        assert dist_lo <= s.obstacle_distance_m <= dist_hi
        assert s.weather in ("dry", "rain")
        assert s.road_friction > 0


def test_generate_random_scenarios_reproducible_with_seed():
    a = generate_random_scenarios(20, seed=123)
    b = generate_random_scenarios(20, seed=123)
    assert [x.to_dict() for x in a] == [x.to_dict() for x in b]


def test_generate_edge_case_scenarios_not_empty():
    presets = generate_edge_case_scenarios()
    assert len(presets) > 0
