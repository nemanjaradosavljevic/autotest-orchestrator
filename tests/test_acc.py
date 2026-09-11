"""
Unit testovi za ACC Virtual ECU, sa rucno izracunatim ocekivanim
vrednostima - isti princip kao tests/test_aeb.py i tests/test_lka.py.
"""

import pytest

from virtual_ecu.acc import ACCVirtualECU


def test_decelerate_on_when_gap_below_desired():
    """100 km/h = 27.78 m/s -> desired_gap = 5 + 27.78*1.5 = 46.67m.
    Razmak 40m < 46.67m -> DECELERATE ON."""
    ecu = ACCVirtualECU()
    r = ecu.process(
        ego_speed_kmh=100,
        lead_speed_kmh=80,
        gap_distance_m=40,
        driver_override_active=False,
    )
    assert r.decelerate is True
    assert r.desired_gap_m == 46.67


def test_decelerate_off_when_gap_above_desired():
    """Isti desired_gap (46.67m), ali razmak 60m > 46.67m -> DECELERATE OFF."""
    ecu = ACCVirtualECU()
    r = ecu.process(
        ego_speed_kmh=100,
        lead_speed_kmh=80,
        gap_distance_m=60,
        driver_override_active=False,
    )
    assert r.decelerate is False


def test_driver_override_suppresses_deceleration():
    """Cak i kad bi ACC inace usporio (mali razmak), vozac na gasu to sprecava."""
    ecu = ACCVirtualECU()
    r = ecu.process(
        ego_speed_kmh=100,
        lead_speed_kmh=80,
        gap_distance_m=20,
        driver_override_active=True,
    )
    assert r.decelerate is False


def test_minimum_gap_applies_even_at_standstill():
    """Pri brzini 0, desired_gap = samo ACC_MIN_GAP_M (5m) - fiksni minimum
    se postuje i pri stajanju, ne samo vremenski razmak."""
    ecu = ACCVirtualECU()
    r = ecu.process(
        ego_speed_kmh=0,
        lead_speed_kmh=0,
        gap_distance_m=3,
        driver_override_active=False,
    )
    assert r.decelerate is True
    assert r.desired_gap_m == 5.0


def test_relative_speed_positive_when_closing_in():
    """Moja brzina (108 km/h = 30 m/s) veca od brzine vozila ispred
    (72 km/h = 20 m/s) -> priblizavamo se, relativna brzina = +10 m/s."""
    ecu = ACCVirtualECU()
    r = ecu.process(
        ego_speed_kmh=108,
        lead_speed_kmh=72,
        gap_distance_m=100,
        driver_override_active=False,
    )
    assert r.relative_speed_m_s == 10.0


def test_invalid_negative_ego_speed_raises():
    ecu = ACCVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(
            ego_speed_kmh=-10,
            lead_speed_kmh=50,
            gap_distance_m=50,
            driver_override_active=False,
        )


def test_invalid_negative_lead_speed_raises():
    ecu = ACCVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(
            ego_speed_kmh=100,
            lead_speed_kmh=-5,
            gap_distance_m=50,
            driver_override_active=False,
        )


def test_invalid_negative_gap_raises():
    ecu = ACCVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(
            ego_speed_kmh=100,
            lead_speed_kmh=80,
            gap_distance_m=-5,
            driver_override_active=False,
        )
