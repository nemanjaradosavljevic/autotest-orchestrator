"""
Failure Analysis - groups failed scenarios into recognizable patterns, so an
engineer can quickly understand WHERE and WHY the system fails most often,
instead of just seeing "N tests failed" (see the "Failure Analysis" section
in the project plan).

These are manually defined ("rule-based") rules - good enough for the first
MVP. Clustering/ML can be added here later, if and when there is a real
need for it.

Note on "safety_margin_edge_case": since test_engine/assertions.py requires
SAFETY_MARGIN (15% more room than aeb.py actually uses), every FAIL by
definition means "the ECU did not brake in time with a margin to spare" -
and this can happen at ANY speed/time, not only in extreme conditions. So
most failures will fall into this category unless they also coincide with
some other aggravating factor (speed, rain, sensor delay) - that is
expected, realistic behavior, not a bug in the classifier.
"""

from collections import defaultdict
from typing import Dict, List

from config import AEB_HIGH_SENSOR_DELAY_THRESHOLD_MS as HIGH_SENSOR_DELAY_THRESHOLD_MS
from config import AEB_HIGH_SPEED_THRESHOLD_KMH as HIGH_SPEED_THRESHOLD_KMH
from config import AEB_LOW_DISTANCE_THRESHOLD_M as LOW_DISTANCE_THRESHOLD_M
from test_engine.runner import TestResult


def classify(result: TestResult) -> str:
    s = result.scenario
    if s.vehicle_speed_kmh >= HIGH_SPEED_THRESHOLD_KMH and s.weather == "rain":
        return "high_speed_wet_road"
    if s.obstacle_distance_m <= LOW_DISTANCE_THRESHOLD_M and s.vehicle_speed_kmh >= HIGH_SPEED_THRESHOLD_KMH:
        return "low_distance_high_speed"
    if s.sensor_delay_ms >= HIGH_SENSOR_DELAY_THRESHOLD_MS:
        return "high_sensor_delay"
    return "safety_margin_edge_case"


def group_failures(results: List[TestResult]) -> Dict[str, List[TestResult]]:
    failures = [r for r in results if not r.passed]
    groups: Dict[str, List[TestResult]] = defaultdict(list)
    for r in failures:
        groups[classify(r)].append(r)
    return dict(groups)


def failure_pattern_summary(results: List[TestResult]) -> Dict[str, int]:
    groups = group_failures(results)
    return {pattern: len(items) for pattern, items in groups.items()}
