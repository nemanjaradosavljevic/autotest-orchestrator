"""
Failure Analysis - grupise neuspesne scenarije po prepoznatljivim
obrascima, da bi inzenjer brze razumeo GDE i ZASTO sistem najcesce pada,
umesto da samo vidi "N testova je palo" (poglavlje "Failure Analysis" u
projektnom planu).

Ovo su rucno definisana ("rule-based") pravila - dovoljno za prvi MVP.
Kasnije se ovde moze dodati clustering/ML kada za tim postoji stvarna
potreba.

Napomena o "safety_margin_edge_case": otkad test_engine/assertions.py
zahteva SAFETY_MARGIN (15% vise prostora nego sto aeb.py stvarno koristi),
svaki FAIL po definiciji znaci "ECU nije zakocio na vreme sa rezervom" -
i to se moze desiti pri BILO KOJOJ brzini/vremenu, ne samo u ekstremnim
uslovima. Zato ce najveci deo failure-a padati u ovu kategoriju osim ako
se ne poklope i sa nekim drugim otezavajucim faktorom (brzina, kisa,
kasnjenje senzora) - to je ocekivano i realno ponasanje, ne greska u
klasifikatoru.
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
