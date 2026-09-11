"""
LKA Failure Analysis - grupise neuspesne LKA scenarije po prepoznatljivim
obrascima. Isti obrazac kao analytics/failures.py (AEB), primenjen na LKA
polja.
"""

from collections import defaultdict
from typing import Dict, List

from config import LKA_FAST_DRIFT_THRESHOLD_M_S as FAST_DRIFT_THRESHOLD_M_S
from config import LKA_HIGH_SPEED_THRESHOLD_KMH as HIGH_SPEED_THRESHOLD_KMH
from test_engine.lka_runner import LKATestResult


def classify(result: LKATestResult) -> str:
    s = result.scenario
    if s.vehicle_speed_kmh >= HIGH_SPEED_THRESHOLD_KMH and s.lateral_velocity_m_s >= FAST_DRIFT_THRESHOLD_M_S:
        return "high_speed_fast_drift"
    if s.lateral_velocity_m_s >= FAST_DRIFT_THRESHOLD_M_S:
        return "fast_drift"
    return "safety_margin_edge_case"


def group_failures(results: List[LKATestResult]) -> Dict[str, List[LKATestResult]]:
    failures = [r for r in results if not r.passed]
    groups: Dict[str, List[LKATestResult]] = defaultdict(list)
    for r in failures:
        groups[classify(r)].append(r)
    return dict(groups)


def failure_pattern_summary(results: List[LKATestResult]) -> Dict[str, int]:
    groups = group_failures(results)
    return {pattern: len(items) for pattern, items in groups.items()}
