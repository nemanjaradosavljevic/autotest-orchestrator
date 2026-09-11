"""
ACC Failure Analysis - grupise neuspesne ACC scenarije po prepoznatljivim
obrascima. Isti obrazac kao analytics/failures.py (AEB) i
analytics/lka_failures.py (LKA), primenjen na ACC polja.
"""

from collections import defaultdict
from typing import Dict, List

from config import ACC_FAST_CLOSING_THRESHOLD_M_S, ACC_HIGH_SPEED_THRESHOLD_KMH
from test_engine.acc_runner import ACCTestResult


def classify(result: ACCTestResult) -> str:
    s = result.scenario
    relative_speed = result.actual.relative_speed_m_s
    if s.ego_speed_kmh >= ACC_HIGH_SPEED_THRESHOLD_KMH and relative_speed >= ACC_FAST_CLOSING_THRESHOLD_M_S:
        return "high_speed_fast_closing"
    if relative_speed >= ACC_FAST_CLOSING_THRESHOLD_M_S:
        return "fast_closing"
    return "safety_margin_edge_case"


def group_failures(results: List[ACCTestResult]) -> Dict[str, List[ACCTestResult]]:
    failures = [r for r in results if not r.passed]
    groups: Dict[str, List[ACCTestResult]] = defaultdict(list)
    for r in failures:
        groups[classify(r)].append(r)
    return dict(groups)


def failure_pattern_summary(results: List[ACCTestResult]) -> Dict[str, int]:
    groups = group_failures(results)
    return {pattern: len(items) for pattern, items in groups.items()}
