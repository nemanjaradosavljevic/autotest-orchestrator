"""
Unit tests for the LKA Virtual ECU, with manually calculated expected
values - the same approach as tests/test_aeb.py.
"""

import pytest

from virtual_ecu.lka import LKAVirtualECU


def test_intervene_on_near_edge_approaching():
    """Near the edge (0.75m remaining) and approaching at 1 m/s -> TTLC 0.75s -> ON."""
    ecu = LKAVirtualECU()
    r = ecu.process(
        vehicle_speed_kmh=100,
        lateral_offset_m=1.0,
        lane_half_width_m=1.75,
        lateral_velocity_m_s=1.0,
        driver_steering_active=False,
    )
    assert r.intervene is True
    assert r.time_to_crossing_s == 0.75


def test_intervene_off_when_centered_and_still():
    ecu = LKAVirtualECU()
    r = ecu.process(
        vehicle_speed_kmh=100,
        lateral_offset_m=0.0,
        lane_half_width_m=1.75,
        lateral_velocity_m_s=0.0,
        driver_steering_active=False,
    )
    assert r.intervene is False
    assert r.time_to_crossing_s is None


def test_driver_override_suppresses_intervention():
    """Even when the system would otherwise intervene, the driver actively steering prevents it."""
    ecu = LKAVirtualECU()
    r = ecu.process(
        vehicle_speed_kmh=100,
        lateral_offset_m=1.0,
        lane_half_width_m=1.75,
        lateral_velocity_m_s=2.0,
        driver_steering_active=True,
    )
    assert r.intervene is False


def test_intervene_on_immediately_when_already_past_edge():
    ecu = LKAVirtualECU()
    r = ecu.process(
        vehicle_speed_kmh=100,
        lateral_offset_m=1.8,
        lane_half_width_m=1.75,
        lateral_velocity_m_s=1.0,
        driver_steering_active=False,
    )
    assert r.intervene is True
    assert r.time_to_crossing_s == 0.0


def test_moving_back_toward_center_never_intervenes():
    """Negative lateral velocity = moving back toward center - no need for intervention."""
    ecu = LKAVirtualECU()
    r = ecu.process(
        vehicle_speed_kmh=100,
        lateral_offset_m=1.5,
        lane_half_width_m=1.75,
        lateral_velocity_m_s=-1.0,
        driver_steering_active=False,
    )
    assert r.intervene is False
    assert r.time_to_crossing_s is None


def test_invalid_negative_speed_raises():
    ecu = LKAVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(
            vehicle_speed_kmh=-10,
            lateral_offset_m=0.0,
            lane_half_width_m=1.75,
            lateral_velocity_m_s=0.0,
            driver_steering_active=False,
        )


def test_invalid_zero_lane_width_raises():
    ecu = LKAVirtualECU()
    with pytest.raises(ValueError):
        ecu.process(
            vehicle_speed_kmh=100,
            lateral_offset_m=0.0,
            lane_half_width_m=0,
            lateral_velocity_m_s=0.0,
            driver_steering_active=False,
        )
